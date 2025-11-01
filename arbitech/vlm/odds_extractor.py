"""
VLM-powered Odds Extraction Engine

This module provides the core functionality for extracting betting odds from images
of bookmaker interfaces using Vision Language Models (VLM) like Qwen-VL.

Features:
- Sophisticated prompt engineering for different bookmaker interfaces
- Confidence scoring for extracted odds
- Batch processing of multiple markets
- Integration with configuration system
- Support for multiple image formats
"""

import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Union, Tuple, Any
from uuid import uuid4, UUID

import aiohttp
from pydantic import BaseModel, Field, validator

from .bookmaker_templates import TemplateManager, BookmakerTemplate
from ..core.config_manager import get_config
from ..storage.models import ArbitrageOpportunity, ArbitrageLeg, Sport, RiskTier


# ============================================================================
# CORE DATA MODELS
# ============================================================================

class ExtractionRequest(BaseModel):
    """Request model for odds extraction from bookmaker images."""
    
    id: UUID = Field(default_factory=uuid4, description="Unique extraction request ID")
    
    # Image data
    image_data: Union[str, bytes] = Field(..., description="Image data (URL or bytes)")
    image_format: str = Field(default="png", description="Image format (png, jpg, etc.)")
    
    # Bookmaker context
    bookmaker: str = Field(..., description="Bookmaker name for template selection")
    sport: Sport = Field(..., description="Sport type")
    
    # Market context
    market_type: str = Field(..., description="Market type (match_winner, over_under, etc.)")
    event_name: str = Field(..., description="Event name")
    
    # Extraction parameters
    template_version: Optional[str] = Field(None, description="Specific template version to use")
    custom_prompt: Optional[str] = Field(None, description="Custom extraction prompt")
    
    # Confidence thresholds
    min_confidence: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum confidence threshold")
    max_extraction_time: int = Field(default=30, gt=0, description="Maximum extraction time in seconds")
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ConfidenceScore(BaseModel):
    """Confidence scoring for extracted odds."""
    
    overall: float = Field(..., ge=0.0, le=1.0, description="Overall extraction confidence")
    
    # Individual confidence metrics
    text_recognition: float = Field(..., ge=0.0, le=1.0, description="Text recognition confidence")
    odds_format: float = Field(..., ge=0.0, le=1.0, description="Odds format detection confidence")
    market_recognition: float = Field(..., ge=0.0, le=1.0, description="Market recognition confidence")
    
    # Per-odd confidence scores
    odds_confidence: Dict[str, float] = Field(default_factory=dict, 
                                              description="Confidence per extracted odd")
    
    # Quality indicators
    completeness_score: float = Field(..., ge=0.0, le=1.0, description="How complete the extraction is")
    consistency_score: float = Field(..., ge=0.0, le=1.0, description="Internal consistency score")


class ExtractionMetadata(BaseModel):
    """Metadata for extraction process."""
    
    extraction_time_ms: int = Field(..., ge=0, description="Total extraction time in milliseconds")
    vlm_model_used: str = Field(..., description="VLM model used for extraction")
    template_used: str = Field(..., description="Template used for extraction")
    
    # Processing details
    image_size: Tuple[int, int] = Field(..., description="Image dimensions (width, height)")
    image_format: str = Field(..., description="Image format")
    
    # Parsing details
    raw_response: str = Field(..., description="Raw VLM response")
    parsed_elements: int = Field(default=0, ge=0, description="Number of parsed elements")
    
    # Quality metrics
    quality_flags: List[str] = Field(default_factory=list, description="Quality issue flags")
    warnings: List[str] = Field(default_factory=list, description="Processing warnings")


class ExtractionResult(BaseModel):
    """Result model for odds extraction."""
    
    id: UUID = Field(default_factory=uuid4, description="Unique extraction result ID")
    request_id: UUID = Field(..., description="Associated extraction request ID")
    
    # Extraction status
    success: bool = Field(..., description="Whether extraction was successful")
    error_message: Optional[str] = Field(None, description="Error message if extraction failed")
    
    # Extracted data
    extracted_odds: Dict[str, Decimal] = Field(default_factory=dict, 
                                              description="Extracted odds by outcome")
    event_outcomes: List[str] = Field(default_factory=list, description="Available outcomes")
    
    # Confidence and quality
    confidence: ConfidenceScore = Field(..., description="Confidence scoring")
    metadata: ExtractionMetadata = Field(..., description="Extraction metadata")
    
    # Post-extraction processing
    arbitrage_calculations: Optional[Dict[str, Any]] = Field(
        None, description="Arbitrage calculation results if applicable"
    )
    
    # Timestamps
    extracted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @validator('confidence')
    def validate_confidence(cls, v):
        """Ensure confidence scores are realistic."""
        if v.overall < 0.5:
            raise ValueError("Overall confidence too low for reliable extraction")
        return v
    
    @validator('extracted_odds')
    def validate_odds(cls, v):
        """Validate extracted odds."""
        for outcome, odds in v.items():
            if odds <= Decimal('1.0'):
                raise ValueError(f"Invalid odds value for {outcome}: {odds}")
        return v


# ============================================================================
# MAIN ODDS EXTRACTOR ENGINE
# ============================================================================

class OddsExtractor:
    """
    Core VLM-powered odds extraction engine.
    
    This class handles the extraction of betting odds from bookmaker interface images
    using sophisticated prompt engineering and Vision Language Models.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the odds extractor.
        
        Args:
            config: Optional configuration override
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Get VLM configuration
        self.vlm_config = get_config('system.vlm', {})
        self.vlm_endpoint = self.vlm_config.get('endpoint')
        self.vlm_api_key = self.vlm_config.get('api_key')
        self.vlm_timeout = self.vlm_config.get('timeout', 30)
        self.max_retries = self.vlm_config.get('retry_attempts', 3)
        
        if not self.vlm_endpoint:
            raise ValueError("VLM endpoint not configured")
        
        # Initialize template manager
        self.template_manager = TemplateManager()
        
        # Rate limiting
        self.rate_limit = self.vlm_config.get('rate_limit_per_minute', 60)
        self._last_requests = []
        
        self.logger.info("OddsExtractor initialized with VLM endpoint: %s", self.vlm_endpoint)
    
    async def extract_odds(
        self, 
        request: ExtractionRequest
    ) -> ExtractionResult:
        """
        Extract odds from a bookmaker image.
        
        Args:
            request: Extraction request containing image and context
            
        Returns:
            ExtractionResult with extracted odds and confidence scores
        """
        start_time = datetime.now()
        
        try:
            # Rate limiting check
            await self._check_rate_limit()
            
            # Get bookmaker template
            template = self.template_manager.get_template(
                request.bookmaker, 
                request.sport,
                version=request.template_version
            )
            
            if not template:
                raise ValueError(f"No template found for {request.bookmaker} ({request.sport})")
            
            # Generate extraction prompt
            prompt = await self._generate_extraction_prompt(request, template)
            
            # Process image data
            image_data = await self._prepare_image_data(request.image_data)
            
            # Call VLM for extraction
            raw_response = await self._call_vlm(prompt, image_data, request.max_extraction_time)
            
            # Calculate extraction time
            extraction_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Parse and validate response
            extraction_result = await self._process_vlm_response(
                raw_response, request, template, extraction_time
            )
            
            self.logger.info("Successfully extracted odds for request %s", request.id)
            return extraction_result
            
        except Exception as e:
            self.logger.error("Failed to extract odds for request %s: %s", request.id, str(e))
            
            # Return error result
            return ExtractionResult(
                id=uuid4(),
                request_id=request.id,
                success=False,
                error_message=str(e),
                confidence=ConfidenceScore(
                    overall=0.0,
                    text_recognition=0.0,
                    odds_format=0.0,
                    market_recognition=0.0,
                    odds_confidence={},
                    completeness_score=0.0,
                    consistency_score=0.0
                ),
                metadata=ExtractionMetadata(
                    extraction_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                    vlm_model_used="unknown",
                    template_used="none",
                    image_size=(0, 0),
                    image_format=request.image_format,
                    raw_response=str(e),
                    parsed_elements=0
                )
            )
    
    async def extract_odds_batch(
        self, 
        requests: List[ExtractionRequest]
    ) -> List[ExtractionResult]:
        """
        Extract odds from multiple images in batch.
        
        Args:
            requests: List of extraction requests
            
        Returns:
            List of extraction results
        """
        self.logger.info("Starting batch extraction of %d images", len(requests))
        
        # Process in batches to avoid overwhelming the VLM
        batch_size = self.config.get('batch_size', 5)
        results = []
        
        for i in range(0, len(requests), batch_size):
            batch = requests[i:i + batch_size]
            
            # Process batch concurrently
            batch_tasks = [
                self.extract_odds(request) 
                for request in batch
            ]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Handle exceptions in batch results
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    self.logger.error("Batch processing error for request %s: %s", 
                                    batch[j].id, str(result))
                    # Convert exception to error result
                    results.append(ExtractionResult(
                        id=uuid4(),
                        request_id=batch[j].id,
                        success=False,
                        error_message=str(result),
                        confidence=ConfidenceScore(
                            overall=0.0,
                            text_recognition=0.0,
                            odds_format=0.0,
                            market_recognition=0.0,
                            odds_confidence={},
                            completeness_score=0.0,
                            consistency_score=0.0
                        ),
                        metadata=ExtractionMetadata(
                            extraction_time_ms=0,
                            vlm_model_used="unknown",
                            template_used="none",
                            image_size=(0, 0),
                            image_format=batch[j].image_format,
                            raw_response=str(result),
                            parsed_elements=0
                        )
                    ))
                else:
                    results.append(result)
            
            # Small delay between batches
            if i + batch_size < len(requests):
                await asyncio.sleep(1)
        
        self.logger.info("Completed batch extraction: %d results", len(results))
        return results
    
    async def _check_rate_limit(self) -> None:
        """Check and enforce rate limiting."""
        now = datetime.now()
        
        # Remove old requests (older than 1 minute)
        self._last_requests = [
            req_time for req_time in self._last_requests 
            if (now - req_time).total_seconds() < 60
        ]
        
        # Check if we're at the limit
        if len(self._last_requests) >= self.rate_limit:
            sleep_time = 60 - (now - self._last_requests[0]).total_seconds()
            if sleep_time > 0:
                self.logger.info("Rate limit reached, sleeping for %.1f seconds", sleep_time)
                await asyncio.sleep(sleep_time)
        
        # Record this request
        self._last_requests.append(now)
    
    async def _generate_extraction_prompt(
        self, 
        request: ExtractionRequest, 
        template: BookmakerTemplate
    ) -> str:
        """
        Generate the extraction prompt using the template.
        
        Args:
            request: Extraction request
            template: Bookmaker template to use
            
        Returns:
            Formatted prompt for VLM extraction
        """
        prompt_parts = [
            "Extract betting odds from this bookmaker interface image.",
            "",
            f"Bookmaker: {request.bookmaker}",
            f"Sport: {request.sport.value}",
            f"Market Type: {request.market_type}",
            f"Event: {request.event_name}",
            "",
            template.get_extraction_prompt(),
            "",
            "Please provide the response in the following JSON format:",
            "{",
            '  "outcomes": ["outcome1", "outcome2", ...],',
            '  "odds": {',
            '    "outcome1": decimal_odds_value,',
            '    "outcome2": decimal_odds_value',
            '  },',
            '  "confidence": {',
            '    "overall": 0.0-1.0,',
            '    "text_recognition": 0.0-1.0,',
            '    "odds_format": 0.0-1.0,',
            '    "market_recognition": 0.0-1.0',
            '  }',
            "}",
            "",
            "Important:",
            "- Return only decimal odds (e.g., 2.50, not 3/2 or +150)",
            "- Ensure odds are greater than 1.0",
            "- If any information is unclear, set confidence scores accordingly",
            "- Only extract odds for the specified market type"
        ]
        
        # Add custom prompt if provided
        if request.custom_prompt:
            prompt_parts.extend(["", "Additional Instructions:", request.custom_prompt])
        
        return "\n".join(prompt_parts)
    
    async def _prepare_image_data(self, image_data: Union[str, bytes]) -> Union[str, bytes]:
        """
        Prepare image data for VLM processing.
        
        Args:
            image_data: Raw image data (URL or bytes)
            
        Returns:
            Processed image data
        """
        if isinstance(image_data, str):
            # It's a URL, fetch the image
            async with aiohttp.ClientSession() as session:
                async with session.get(image_data) as response:
                    if response.status != 200:
                        raise ValueError(f"Failed to fetch image from URL: {response.status}")
                    return await response.read()
        
        return image_data
    
    async def _call_vlm(
        self, 
        prompt: str, 
        image_data: Union[str, bytes], 
        timeout: int
    ) -> str:
        """
        Call the VLM service for odds extraction.
        
        Args:
            prompt: Extraction prompt
            image_data: Image data
            timeout: Request timeout
            
        Returns:
            Raw VLM response
        """
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.vlm_api_key:
            headers["Authorization"] = f"Bearer {self.vlm_api_key}"
        
        payload = {
            "model": "qwen-vl-plus",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_data}" if isinstance(image_data, bytes) 
                                      else image_data
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 2000,
            "temperature": 0.1
        }
        
        async with aiohttp.ClientSession() as session:
            for attempt in range(self.max_retries):
                try:
                    async with session.post(
                        self.vlm_endpoint,
                        json=payload,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=timeout)
                    ) as response:
                        
                        if response.status == 200:
                            result = await response.json()
                            return result.get("choices", [{}])[0].get("message", {}).get("content", "")
                        
                        elif response.status == 429:  # Rate limited
                            retry_delay = 2 ** attempt
                            self.logger.warning(f"Rate limited, retrying in {retry_delay} seconds")
                            await asyncio.sleep(retry_delay)
                            continue
                        
                        else:
                            error_text = await response.text()
                            raise ValueError(f"VLM API error {response.status}: {error_text}")
                
                except asyncio.TimeoutError:
                    if attempt == self.max_retries - 1:
                        raise ValueError(f"VLM API timeout after {timeout} seconds")
                    await asyncio.sleep(2 ** attempt)
                
                except Exception as e:
                    if attempt == self.max_retries - 1:
                        raise ValueError(f"VLM API call failed: {str(e)}")
                    await asyncio.sleep(2 ** attempt)
        
        raise ValueError("VLM API call failed after all retries")
    
    async def _process_vlm_response(
        self,
        raw_response: str,
        request: ExtractionRequest,
        template: BookmakerTemplate,
        extraction_time: int
    ) -> ExtractionResult:
        """
        Process and validate the VLM response.
        
        Args:
            raw_response: Raw VLM response
            request: Original extraction request
            template: Bookmaker template used
            extraction_time: Extraction time in milliseconds
            
        Returns:
            Processed ExtractionResult
        """
        try:
            # Parse JSON response
            parsed_data = self._parse_vlm_json_response(raw_response)
            
            # Validate and normalize data
            outcomes = parsed_data.get("outcomes", [])
            odds_data = parsed_data.get("odds", {})
            confidence_data = parsed_data.get("confidence", {})
            
            # Convert odds to Decimal
            extracted_odds = {}
            for outcome, odds_value in odds_data.items():
                try:
                    extracted_odds[outcome] = Decimal(str(odds_value))
                except (ValueError, TypeError):
                    self.logger.warning("Invalid odds value for %s: %s", outcome, odds_value)
            
            # Validate odds
            valid_odds = {}
            for outcome, odds in extracted_odds.items():
                if odds > Decimal('1.0'):
                    valid_odds[outcome] = odds
                else:
                    self.logger.warning("Invalid odds (<= 1.0) for %s: %s", outcome, odds)
            
            # Calculate confidence scores
            confidence = self._calculate_confidence_scores(
                confidence_data, valid_odds, outcomes, template
            )
            
            # Create metadata
            metadata = ExtractionMetadata(
                extraction_time_ms=extraction_time,
                vlm_model_used="qwen-vl-plus",
                template_used=template.name,
                image_size=(0, 0),  # TODO: Extract from image processing
                image_format=request.image_format,
                raw_response=raw_response,
                parsed_elements=len(valid_odds)
            )
            
            # Check if extraction meets minimum confidence
            if confidence.overall < request.min_confidence:
                self.logger.warning("Extraction confidence %.3f below minimum %.3f", 
                                  confidence.overall, request.min_confidence)
            
            return ExtractionResult(
                id=uuid4(),
                request_id=request.id,
                success=True,
                extracted_odds=valid_odds,
                event_outcomes=outcomes,
                confidence=confidence,
                metadata=metadata
            )
            
        except Exception as e:
            self.logger.error("Failed to process VLM response: %s", str(e))
            raise ValueError(f"Failed to process VLM response: {str(e)}")
    
    def _parse_vlm_json_response(self, raw_response: str) -> Dict[str, Any]:
        """
        Parse JSON from VLM response.
        
        Args:
            raw_response: Raw response text
            
        Returns:
            Parsed JSON data
        """
        import json
        import re
        
        # Try to extract JSON from response
        json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
        
        if json_match:
            json_str = json_match.group(0)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        # Try parsing entire response as JSON
        try:
            return json.loads(raw_response)
        except json.JSONDecodeError:
            raise ValueError("Unable to parse JSON from VLM response")
    
    def _calculate_confidence_scores(
        self,
        confidence_data: Dict[str, Any],
        odds: Dict[str, Decimal],
        outcomes: List[str],
        template: BookmakerTemplate
    ) -> ConfidenceScore:
        """
        Calculate confidence scores for the extraction.
        
        Args:
            confidence_data: Confidence data from VLM
            odds: Extracted odds
            outcomes: List of outcomes
            template: Bookmaker template used
            
        Returns:
            Calculated ConfidenceScore
        """
        # Extract individual confidence scores
        overall = confidence_data.get("overall", 0.5)
        text_recognition = confidence_data.get("text_recognition", 0.5)
        odds_format = confidence_data.get("odds_format", 0.5)
        market_recognition = confidence_data.get("market_recognition", 0.5)
        
        # Calculate per-odd confidence
        odds_confidence = {}
        for outcome in outcomes:
            if outcome in odds:
                odds_confidence[outcome] = min(overall, 0.9)  # Slightly lower than overall
        
        # Calculate completeness and consistency scores
        completeness_score = min(len(odds) / max(len(outcomes), 1), 1.0)
        
        # Check for consistency (e.g., all odds > 1.0, reasonable range)
        consistency_score = 1.0
        if odds:
            min_odds = min(odds.values())
            max_odds = max(odds.values())
            
            # Penalize if odds seem unreasonable
            if min_odds < Decimal('1.01'):
                consistency_score *= 0.8
            if max_odds > Decimal('100.0'):
                consistency_score *= 0.9
            
            # Check if all outcomes have odds
            if len(odds) < len(outcomes):
                consistency_score *= len(odds) / len(outcomes)
        
        return ConfidenceScore(
            overall=overall,
            text_recognition=text_recognition,
            odds_format=odds_format,
            market_recognition=market_recognition,
            odds_confidence=odds_confidence,
            completeness_score=completeness_score,
            consistency_score=consistency_score
        )


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

async def extract_odds_from_url(
    image_url: str,
    bookmaker: str,
    sport: Sport,
    market_type: str,
    event_name: str,
    **kwargs
) -> ExtractionResult:
    """
    Convenience function to extract odds from an image URL.
    
    Args:
        image_url: URL of the image
        bookmaker: Bookmaker name
        sport: Sport type
        market_type: Market type
        event_name: Event name
        **kwargs: Additional parameters for ExtractionRequest
        
    Returns:
        ExtractionResult
    """
    request = ExtractionRequest(
        image_data=image_url,
        bookmaker=bookmaker,
        sport=sport,
        market_type=market_type,
        event_name=event_name,
        **kwargs
    )
    
    extractor = OddsExtractor()
    return await extractor.extract_odds(request)


async def extract_odds_from_bytes(
    image_bytes: bytes,
    bookmaker: str,
    sport: Sport,
    market_type: str,
    event_name: str,
    **kwargs
) -> ExtractionResult:
    """
    Convenience function to extract odds from image bytes.
    
    Args:
        image_bytes: Image data as bytes
        bookmaker: Bookmaker name
        sport: Sport type
        market_type: Market type
        event_name: Event name
        **kwargs: Additional parameters for ExtractionRequest
        
    Returns:
        ExtractionResult
    """
    request = ExtractionRequest(
        image_data=image_bytes,
        bookmaker=bookmaker,
        sport=sport,
        market_type=market_type,
        event_name=event_name,
        **kwargs
    )
    
    extractor = OddsExtractor()
    return await extractor.extract_odds(request)