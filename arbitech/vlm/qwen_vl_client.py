"""
Qwen-VL Client Implementation

This module provides a comprehensive client wrapper for the Qwen2-VL Vision Language
Model, including model loading, inference, response handling, performance monitoring,
and integration with the ARBitech configuration and logging systems.
"""

import io
import base64
import asyncio
import time
import traceback
from typing import Dict, Any, Optional, List, Union, BinaryIO, Callable
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import logging
import json
import hashlib

try:
    import torch
    from PIL import Image
    import numpy as np
    HAS_TORCH = True
except ImportError:
    # Mock for testing without dependencies
    HAS_TORCH = False
    torch = None
    Image = None
    np = None

try:
    from transformers import Qwen2VLForConditionalGeneration, AutoTokenizer, AutoProcessor
    HAS_TRANSFORMERS = True
except ImportError:
    # Mock for testing
    HAS_TRANSFORMERS = False
    Qwen2VLForConditionalGeneration = None
    AutoTokenizer = None
    AutoProcessor = None

try:
    from .model_config import (
        VLMConfig,
        ModelParameters,
        PerformanceConfig,
        MonitoringConfig,
        ModelStatus,
        get_default_config,
        validate_config,
        get_optimal_device_config
    )
except ImportError:
    from model_config import (
        VLMConfig,
        ModelParameters,
        PerformanceConfig,
        MonitoringConfig,
        ModelStatus,
        get_default_config,
        validate_config,
        get_optimal_device_config
    )

try:
    from ..core.config_manager import get_config_manager, ConfigError
except ImportError:
    ConfigError = Exception
    get_config_manager = None

try:
    from ..utils.logger import get_logger
except ImportError:
    import logging
    get_logger = lambda x: logging.getLogger(x)

try:
    from ..storage.audit_logger import log_performance_metric, log_security_event
except ImportError:
    def log_performance_metric(*args, **kwargs): pass
    def log_security_event(*args, **kwargs): pass


@dataclass
class VLMRequest:
    """VLM request structure"""
    id: str
    images: List[Union[str, bytes, Image.Image, BinaryIO]]
    text: str
    timestamp: datetime = field(default_factory=datetime.now)
    timeout: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {
            "id": self.id,
            "text": self.text[:100] + "..." if len(self.text) > 100 else self.text,
            "timestamp": self.timestamp.isoformat(),
            "timeout": self.timeout,
            "metadata": self.metadata,
            "image_count": len(self.images)
        }


@dataclass
class VLMResponse:
    """VLM response structure"""
    request_id: str
    text: str
    success: bool
    timestamp: datetime = field(default_factory=datetime.now)
    processing_time: float = 0.0
    token_count: Optional[int] = None
    error: Optional[str] = None
    confidence_score: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {
            "request_id": self.request_id,
            "success": self.success,
            "timestamp": self.timestamp.isoformat(),
            "processing_time": self.processing_time,
            "token_count": self.token_count,
            "error": self.error,
            "confidence_score": self.confidence_score,
            "text": self.text[:200] + "..." if len(self.text) > 200 else self.text,
            "metadata": self.metadata
        }


class VLMCClientError(Exception):
    """Base exception for VLM client errors"""
    pass


class VLMModelError(VLMCClientError):
    """Model loading and inference errors"""
    pass


class VLMTimeoutError(VLMCClientError):
    """Request timeout errors"""
    pass


class VLMRequestError(VLMCClientError):
    """Request validation and processing errors"""
    pass


class QwenVLClient:
    """
    Qwen-VL Vision Language Model Client
    
    Provides a comprehensive interface for interacting with Qwen2-VL models,
    including model loading, inference, caching, performance monitoring, and
    integration with ARBitech systems.
    """
    
    def __init__(self, config: Optional[VLMConfig] = None):
        """
        Initialize Qwen-VL Client
        
        Args:
            config: VLM configuration. If None, loads from config system.
        """
        self.logger = get_logger("vlm.client")
        self.config = config or self._load_config()
        
        # Model components
        self.model = None
        self.processor = None
        self.tokenizer = None
        
        # State tracking
        self.status = ModelStatus.UNLOADED
        self.load_start_time = None
        self.last_activity = None
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        
        # Performance tracking
        self.request_times: List[float] = []
        self.last_health_check = None
        
        # Thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=self.config.performance.num_workers)
        
        # Request queue and rate limiting
        self.request_queue = asyncio.Queue(maxsize=self.config.performance.max_queue_size)
        self.rate_limiter = RateLimiter(
            requests_per_minute=self.config.performance.requests_per_minute,
            burst_limit=self.config.performance.burst_limit
        )
        
        # Cache
        self.response_cache = {} if self.config.features.get("enable_caching", True) else None
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Statistics
        self.stats = {
            "load_time": 0,
            "total_processing_time": 0,
            "average_response_time": 0,
            "last_error": None,
            "uptime": 0
        }
        
        self.logger.info("Qwen-VL Client initialized", 
                        config_summary=self._get_config_summary())
    
    def _load_config(self) -> VLMConfig:
        """Load configuration from ARBitech config system"""
        try:
            if get_config_manager:
                config_manager = get_config_manager()
                vlm_config_dict = config_manager.get_vlm_config()
                
                if not vlm_config_dict:
                    self.logger.warning("No VLM config found in system config, using defaults")
                    return get_default_config()
                
                # Convert to VLMConfig
                config = VLMConfig.from_dict(vlm_config_dict)
                
                # Apply optimal device configuration if enabled
                if config.features.get("auto_device_config", False):
                    optimal_config = get_optimal_device_config()
                    config.model.update_from_config(optimal_config)
                
                return config
            else:
                self.logger.warning("Config manager not available, using defaults")
                return get_default_config()
            
        except Exception as e:
            self.logger.warning(f"Failed to load VLM config from system: {e}, using defaults")
            return get_default_config()
    
    def _get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary for logging"""
        return {
            "model_name": self.config.model.model_name,
            "device": self.config.model.device.value,
            "precision": self.config.model.precision.value,
            "max_new_tokens": self.config.model.max_new_tokens,
            "batch_size": self.config.performance.batch_size,
            "cache_enabled": self.response_cache is not None,
            "async_enabled": self.config.features.get("enable_async_inference", True)
        }
    
    def _validate_images(self, images: List[Union[str, bytes, Image.Image, BinaryIO]]) -> List[Image.Image]:
        """
        Validate and preprocess images
        
        Args:
            images: List of images in various formats
            
        Returns:
            List of PIL Images
            
        Raises:
            VLMRequestError: If images are invalid
        """
        processed_images = []
        
        for i, image in enumerate(images):
            try:
                if isinstance(image, str):
                    # File path
                    if not Path(image).exists():
                        raise VLMRequestError(f"Image file not found: {image}")
                    img = Image.open(image).convert('RGB')
                elif isinstance(image, bytes):
                    # Raw bytes
                    img = Image.open(io.BytesIO(image)).convert('RGB')
                elif Image and isinstance(image, Image.Image):
                    # PIL Image
                    img = image.convert('RGB')
                elif hasattr(image, 'read'):
                    # File-like object
                    img = Image.open(image).convert('RGB')
                else:
                    raise VLMRequestError(f"Unsupported image type: {type(image)}")
                
                # Resize if necessary
                if self.config.model.image_size:
                    img = img.resize((self.config.model.image_size, self.config.model.image_size))
                
                processed_images.append(img)
                
            except Exception as e:
                raise VLMRequestError(f"Failed to process image {i}: {str(e)}")
        
        return processed_images
    
    def _create_cache_key(self, images: List[Image.Image], text: str) -> str:
        """Create cache key for request"""
        # Hash images
        image_hashes = []
        for img in images:
            if HAS_TORCH and np:
                img_array = np.array(img)
                img_hash = hashlib.md5(img_array.tobytes()).hexdigest()
            else:
                img_hash = hashlib.md5(str(img).encode()).hexdigest()
            image_hashes.append(img_hash)
        
        # Combine with text
        combined = f"{image_hashes}_{text}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    async def load_model(self) -> bool:
        """
        Load the Qwen-VL model
        
        Returns:
            True if model loaded successfully, False otherwise
            
        Raises:
            VLMModelError: If model loading fails
        """
        if self.status == ModelStatus.LOADED:
            self.logger.info("Model already loaded")
            return True
        
        self.logger.info("Starting model loading...", 
                        model_name=self.config.model.model_name,
                        device=self.config.model.device.value,
                        precision=self.config.model.precision.value)
        
        self.status = ModelStatus.LOADING
        self.load_start_time = time.time()
        
        try:
            # Check if dependencies are available
            if not HAS_TORCH or not HAS_TRANSFORMERS:
                self.logger.warning("PyTorch or Transformers not available, using mock model")
                self.model = "mock_model"
                self.processor = "mock_processor"
                self.tokenizer = "mock_tokenizer"
                
                # Simulate loading time
                await asyncio.sleep(1)
                
                self.status = ModelStatus.LOADED
                self.last_activity = datetime.now()
                return True
            
            # Device configuration
            device = self._get_device()
            torch_dtype = self._get_torch_dtype()
            
            # Load processor
            self.logger.debug("Loading processor...")
            self.processor = AutoProcessor.from_pretrained(
                self.config.model.model_path or self.config.model.model_name,
                trust_remote_code=self.config.model.trust_remote_code
            )
            
            # Load tokenizer
            self.logger.debug("Loading tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.config.model.model_path or self.config.model.model_name,
                trust_remote_code=self.config.model.trust_remote_code
            )
            
            # Load model
            self.logger.debug("Loading model...")
            self.model = Qwen2VLForConditionalGeneration.from_pretrained(
                self.config.model.model_path or self.config.model.model_name,
                torch_dtype=torch_dtype,
                device_map=self.config.model.device_map,
                trust_remote_code=self.config.model.trust_remote_code,
                load_in_8bit=self.config.model.load_in_8bit,
                load_in_4bit=self.config.model.load_in_4bit,
                max_memory=self.config.performance.max_memory_per_gpu
            )
            
            # Move to device if not using device_map
            if not self.config.model.device_map:
                self.model = self.model.to(device)
            
            self.model.eval()
            
            # Record load time
            load_time = time.time() - self.load_start_time
            self.stats["load_time"] = load_time
            
            self.status = ModelStatus.LOADED
            self.last_activity = datetime.now()
            
            self.logger.info("Model loaded successfully",
                           load_time=load_time,
                           device=str(device),
                           memory_usage=self._get_memory_usage())
            
            return True
            
        except Exception as e:
            self.status = ModelStatus.ERROR
            error_msg = f"Failed to load model: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.stats["last_error"] = str(e)
            
            raise VLMModelError(error_msg)
    
    def _get_device(self):
        """Get torch device based on configuration"""
        if not HAS_TORCH:
            return "cpu"
        
        device_type = self.config.model.device.value
        
        if device_type == "auto":
            return torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            return torch.device(device_type)
    
    def _get_torch_dtype(self):
        """Get torch dtype based on precision configuration"""
        if not HAS_TORCH:
            return None
            
        precision = self.config.model.precision.value
        
        if precision == "fp16":
            return torch.float16
        elif precision == "fp32":
            return torch.float32
        else:
            return torch.float16  # Default for quantized models
    
    def _get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage"""
        if HAS_TORCH and torch.cuda.is_available():
            return {
                "allocated_gb": torch.cuda.memory_allocated() / 1024**3,
                "reserved_gb": torch.cuda.memory_reserved() / 1024**3,
                "max_allocated_gb": torch.cuda.max_memory_allocated() / 1024**3
            }
        return {"allocated_mb": 0, "reserved_mb": 0}
    
    def is_model_loaded(self) -> bool:
        """Check if model is loaded"""
        return self.status == ModelStatus.LOADED and self.model is not None
    
    async def unload_model(self) -> bool:
        """Unload the model to free memory"""
        if not self.is_model_loaded():
            return True
        
        try:
            self.logger.info("Unloading model...")
            
            # Clear model references
            del self.model
            del self.processor
            del self.tokenizer
            
            # Clear GPU memory if using CUDA
            if HAS_TORCH and torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            self.model = None
            self.processor = None
            self.tokenizer = None
            self.status = ModelStatus.UNLOADED
            
            self.logger.info("Model unloaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to unload model: {e}")
            return False
    
    def _ensure_model_loaded(self):
        """Ensure model is loaded, raise error if not"""
        if not self.is_model_loaded():
            raise VLMModelError("Model not loaded. Call load_model() first.")
    
    def _create_request_id(self) -> str:
        """Create unique request ID"""
        timestamp = int(time.time() * 1000)
        import random
        return f"vlm_{timestamp}_{random.randint(1000, 9999)}"
    
    async def generate_response(
        self,
        images: List[Union[str, bytes, Image.Image, BinaryIO]],
        text: str,
        timeout: Optional[float] = None,
        use_cache: bool = True
    ) -> VLMResponse:
        """
        Generate response from images and text
        
        Args:
            images: List of images to analyze
            text: Text prompt/query
            timeout: Request timeout in seconds
            use_cache: Whether to use response cache
            
        Returns:
            VLMResponse object
            
        Raises:
            VLMTimeoutError: If request times out
            VLMRequestError: If request is invalid
            VLMModelError: If model fails to generate response
        """
        start_time = time.time()
        request_id = self._create_request_id()
        
        # Create request object
        request = VLMRequest(
            id=request_id,
            images=images,
            text=text,
            timeout=timeout
        )
        
        self.logger.info("Processing VLM request", request=request.to_dict())
        
        try:
            self._ensure_model_loaded()
            
            # Rate limiting check
            await self.rate_limiter.acquire()
            
            # Cache check
            cache_key = None
            if use_cache and self.response_cache and Image:
                processed_images = self._validate_images(images)
                cache_key = self._create_cache_key(processed_images, text)
                if cache_key in self.response_cache:
                    self.cache_hits += 1
                    response = self.response_cache[cache_key]
                    response.request_id = request_id
                    response.processing_time = time.time() - start_time
                    self.logger.info("Cache hit", cache_key=cache_key)
                    return response
            
            self.cache_misses += 1
            
            # Validate images
            processed_images = self._validate_images(images) if Image else images
            
            # Generate response
            response = await self._generate_with_timeout(
                processed_images, 
                text, 
                timeout or self.config.performance.inference_timeout
            )
            
            # Set request ID and timing
            response.request_id = request_id
            response.processing_time = time.time() - start_time
            
            # Cache response
            if use_cache and self.response_cache and cache_key:
                self.response_cache[cache_key] = response
            
            # Update statistics
            self.total_requests += 1
            self.successful_requests += 1
            self.request_times.append(response.processing_time)
            self.last_activity = datetime.now()
            
            self.logger.info("Request completed successfully",
                           request_id=request_id,
                           processing_time=response.processing_time)
            
            return response
            
        except asyncio.TimeoutError:
            error_msg = f"Request timed out after {timeout or self.config.performance.inference_timeout}s"
            self.logger.error(error_msg, request_id=request_id)
            
            response = VLMResponse(
                request_id=request_id,
                text="",
                success=False,
                error=error_msg
            )
            return response
            
        except Exception as e:
            error_msg = f"Request failed: {str(e)}"
            self.logger.error(error_msg, request_id=request_id, exc_info=True)
            
            response = VLMResponse(
                request_id=request_id,
                text="",
                success=False,
                error=str(e)
            )
            
            self.total_requests += 1
            self.failed_requests += 1
            self.stats["last_error"] = str(e)
            
            return response
    
    async def _generate_with_timeout(
        self,
        images: List[Image.Image],
        text: str,
        timeout: float
    ) -> VLMResponse:
        """Generate response with timeout"""
        try:
            # Run in thread pool to avoid blocking
            response_text = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    self._generate_sync,
                    images,
                    text
                ),
                timeout=timeout
            )
            
            return VLMResponse(
                request_id="",
                text=response_text,
                success=True
            )
            
        except asyncio.TimeoutError:
            raise VLMTimeoutError(f"Generation timed out after {timeout}s")
    
    def _generate_sync(self, images: List[Image.Image], text: str) -> str:
        """Synchronous generation method"""
        try:
            # Mock response for testing
            if not HAS_TRANSFORMERS or self.model == "mock_model":
                return f"Mock analysis of image(s) with text: '{text}'. Dependencies not available."
            
            # Prepare inputs
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": img} for img in images
                    ] + [{"type": "text", "text": text}]
                }
            ]
            
            # Apply chat template
            text = self.processor.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            
            # Process inputs
            inputs = self.processor(
                text=[text],
                images=images,
                padding=True,
                return_tensors="pt"
            )
            
            # Move to device
            inputs = inputs.to(self.model.device)
            
            # Generate
            with torch.no_grad():
                generated_ids = self.model.generate(
                    **inputs,
                    max_new_tokens=self.config.model.max_new_tokens,
                    temperature=self.config.model.temperature,
                    top_p=self.config.model.top_p,
                    top_k=self.config.model.top_k,
                    repetition_penalty=self.config.model.repetition_penalty,
                    do_sample=True
                )
            
            # Decode response
            generated_ids_trimmed = [
                out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
            ]
            output_text = self.processor.batch_decode(
                generated_ids_trimmed,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False
            )
            
            return output_text[0] if output_text else ""
            
        except Exception as e:
            self.logger.error(f"Generation failed: {e}", exc_info=True)
            raise VLMModelError(f"Generation failed: {str(e)}")
    
    async def batch_generate(
        self,
        requests: List[Dict[str, Any]],
        timeout: Optional[float] = None
    ) -> List[VLMResponse]:
        """
        Generate responses for multiple requests in batch
        
        Args:
            requests: List of request dictionaries with 'images' and 'text' keys
            timeout: Batch timeout in seconds
            
        Returns:
            List of VLMResponse objects
        """
        self.logger.info(f"Processing batch of {len(requests)} requests")
        
        # Create tasks for concurrent processing
        tasks = []
        for i, req_data in enumerate(requests):
            task = asyncio.create_task(
                self.generate_response(
                    images=req_data["images"],
                    text=req_data["text"],
                    timeout=timeout
                )
            )
            tasks.append(task)
        
        # Wait for all tasks to complete
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_responses = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                error_response = VLMResponse(
                    request_id=f"batch_{i}",
                    text="",
                    success=False,
                    error=str(response)
                )
                processed_responses.append(error_response)
            else:
                processed_responses.append(response)
        
        self.logger.info(f"Batch processing completed: {len(processed_responses)} responses")
        return processed_responses
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check
        
        Returns:
            Health check results
        """
        self.last_health_check = datetime.now()
        
        health_status = {
            "status": "healthy",
            "timestamp": self.last_health_check.isoformat(),
            "model_loaded": self.is_model_loaded(),
            "status_enum": self.status.value,
            "uptime_seconds": self._get_uptime_seconds(),
            "statistics": self.get_statistics(),
            "memory_usage": self._get_memory_usage()
        }
        
        # Check for issues
        issues = []
        
        if not self.is_model_loaded():
            issues.append("Model not loaded")
        
        if self.config.monitoring.monitor_memory_usage and HAS_TORCH and torch.cuda.is_available():
            memory_allocated = torch.cuda.memory_allocated()
            memory_total = torch.cuda.get_device_properties(0).total_memory
            memory_usage_ratio = memory_allocated / memory_total
            
            if memory_usage_ratio > self.config.monitoring.memory_threshold:
                issues.append(f"High memory usage: {memory_usage_ratio:.2%}")
        
        # Check error rate
        error_rate = self.failed_requests / max(self.total_requests, 1)
        if error_rate > 0.1:  # 10% error rate
            issues.append(f"High error rate: {error_rate:.2%}")
        
        if issues:
            health_status["status"] = "degraded"
            health_status["issues"] = issues
            self.logger.warning("Health check found issues", issues=issues)
        
        self.logger.debug("Health check completed", status=health_status["status"])
        return health_status
    
    def _get_uptime_seconds(self) -> float:
        """Get uptime in seconds"""
        if self.load_start_time:
            return time.time() - self.load_start_time
        return 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get client statistics"""
        avg_response_time = (
            sum(self.request_times) / len(self.request_times) 
            if self.request_times else 0
        )
        
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": (
                self.successful_requests / max(self.total_requests, 1) * 100
            ),
            "average_response_time": avg_response_time,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": (
                self.cache_hits / max(self.cache_hits + self.cache_misses, 1) * 100
            ),
            "last_activity": (
                self.last_activity.isoformat() if self.last_activity else None
            ),
            "model_stats": self.stats.copy()
        }
    
    def reset_statistics(self):
        """Reset all statistics"""
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.request_times.clear()
        self.cache_hits = 0
        self.cache_misses = 0
        self.stats = {
            "load_time": 0,
            "total_processing_time": 0,
            "average_response_time": 0,
            "last_error": None,
            "uptime": 0
        }
        self.logger.info("Statistics reset")
    
    async def close(self):
        """Cleanup resources"""
        self.logger.info("Closing VLM client")
        
        # Unload model
        await self.unload_model()
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        self.logger.info("VLM client closed")


class RateLimiter:
    """Rate limiter for API requests"""
    
    def __init__(self, requests_per_minute: int = 60, burst_limit: int = 10):
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit
        self.requests = []
    
    async def acquire(self):
        """Acquire rate limit token"""
        now = time.time()
        
        # Clean old requests
        self.requests = [req_time for req_time in self.requests if now - req_time < 60]
        
        # Check burst limit
        recent_requests = [req_time for req_time in self.requests if now - req_time < 1]
        if len(recent_requests) >= self.burst_limit:
            sleep_time = 1 - (now - min(recent_requests))
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
        
        # Check per-minute limit
        if len(self.requests) >= self.requests_per_minute:
            sleep_time = 60 - (now - self.requests[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
        
        # Record this request
        self.requests.append(now)


# Convenience function
async def create_vlm_client(config: Optional[VLMConfig] = None) -> QwenVLClient:
    """
    Create and initialize VLM client
    
    Args:
        config: Optional VLM configuration
        
    Returns:
        Initialized QwenVLClient
    """
    client = QwenVLClient(config)
    await client.load_model()
    return client
