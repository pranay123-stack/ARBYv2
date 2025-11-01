# VLM Odds Extraction Parser System

A sophisticated odds extraction and parsing system using Vision Language Models (VLM) like Qwen-VL that integrates seamlessly with the ARBitech arbitrage trading platform.

## Overview

This system provides:

- **VLM-powered odds extraction** from bookmaker interface images
- **Sophisticated response parsing** with confidence scoring
- **Template system** for different betting sites (Betfair, Pinnacle, BetDex, Aver)
- **Comprehensive validation** against mathematical constraints
- **Arbitrage opportunity detection** and validation
- **Cross-bookmaker consistency checks**

## Key Components

### 1. OddsExtractor (`odds_extractor.py`)
Main VLM-powered odds extraction engine with:
- Sophisticated prompt engineering for different bookmaker interfaces
- Confidence scoring for extracted odds
- Batch processing of multiple markets
- Integration with configuration system
- Rate limiting and error handling

### 2. OddsParser (`odds_parser.py`)
Response parsing and validation system with:
- Support for multiple odds formats (decimal, fractional, American, etc.)
- Mathematical validation of odds
- Integration with ArbitrageOpportunity model
- Detailed parsing metadata for debugging

### 3. BookmakerTemplates (`bookmaker_templates.py`)
Template system for different betting sites:
- **Betfair**: Exchange-style interface with back/lay odds
- **Pinnacle**: Clean, professional layout
- **BetDex**: Modern betting interface
- **Aver**: Regional bookmaker layout
- Dynamic prompt generation and versioning

### 4. Validation (`validation.py`)
Cross-validation of extracted odds:
- Mathematical constraint validation
- Consistency checks across bookmakers
- Arbitrage opportunity validation
- Quality scoring and confidence adjustment

## Installation

The system integrates with the existing ARBitech configuration and models:

```python
from vlm import OddsExtractor, OddsParser, TemplateManager, OddsValidator
from storage.models import Sport

# Initialize components
extractor = OddsExtractor()
parser = OddsParser()
template_manager = TemplateManager()
validator = OddsValidator()
```

## Usage Examples

### Basic Odds Extraction

```python
import asyncio
from vlm import ExtractionRequest, Sport

async def extract_odds():
    # Create extraction request
    request = ExtractionRequest(
        image_data="path/to/bookmaker_screenshot.png",
        bookmaker="Betfair",
        sport=Sport.FOOTBALL,
        market_type="match_winner",
        event_name="Manchester United vs Liverpool"
    )
    
    # Extract odds
    extractor = OddsExtractor()
    result = await extractor.extract_odds(request)
    
    if result.success:
        print(f"Extracted {len(result.extracted_odds)} odds")
        for outcome, odds in result.extracted_odds.items():
            print(f"{outcome}: {odds} (confidence: {result.confidence.odds_confidence.get(outcome, 0):.3f})")
    else:
        print(f"Extraction failed: {result.error_message}")

asyncio.run(extract_odds())
```

### Parsing VLM Responses

```python
async def parse_vlm_response():
    parser = OddsParser()
    
    raw_response = '''
    {
        "outcomes": ["Home Win", "Away Win", "Draw"],
        "odds": {
            "Home Win": "2.50",
            "Away Win": "3.20", 
            "Draw": "3.00"
        }
    }
    '''
    
    result = await parser.parse_vlm_response(
        raw_response=raw_response,
        bookmaker="Pinnacle",
        sport=Sport.FOOTBALL,
        market_type="match_winner",
        event_name="Chelsea vs Arsenal"
    )
    
    print(f"Parsed {len(result.parsed_odds)} odds")
    print(f"Overall confidence: {result.overall_confidence:.3f}")
    print(f"Quality score: {result.data_completeness:.3f}")

asyncio.run(parse_vlm_response())
```

### Template Management

```python
from vlm import TemplateManager, Sport

template_manager = TemplateManager()

# List available templates
templates = template_manager.list_templates()
for template in templates:
    print(f"{template.name} v{template.version} - {template.bookmaker}")

# Get specific template
betfair_template = template_manager.get_template("Betfair", Sport.FOOTBALL)
if betfair_template:
    prompt = betfair_template.get_extraction_prompt(Sport.FOOTBALL, "match_winner")
    print("Generated prompt for Betfair interface")

# Validate compatibility
compatibility = template_manager.validate_template_compatibility(
    "Pinnacle", Sport.FOOTBALL, "over_under"
)
print(f"Template compatibility: {compatibility}")
```

### Odds Validation

```python
async def validate_odds():
    validator = OddsValidator()
    
    # Validate parsed odds
    validation_result = await validator.validate_market_odds(market_result)
    
    print(f"Validation: {'PASS' if validation_result.is_valid else 'FAIL'}")
    print(f"Quality score: {validation_result.quality_score:.3f}")
    
    for issue in validation_result.issues:
        print(f"[{issue.severity.value}] {issue.message}")

asyncio.run(validate_odds())
```

### Cross-Bookmaker Validation

```python
from vlm import cross_validate_odds

async def cross_validate():
    # Multiple market results from different bookmakers
    market_results = [betfair_result, pinnacle_result, betdex_result]
    
    results = await cross_validate_odds(market_results, tolerance_percentage=5.0)
    
    for bookmaker, validation_result in results.items():
        print(f"{bookmaker}: Quality {validation_result.quality_score:.3f}")
        for issue in validation_result.issues:
            print(f"  {issue.message}")

asyncio.run(cross_validate())
```

### Arbitrage Opportunity Creation

```python
from vlm import create_arbitrage_opportunity

async def find_arbitrage():
    # Market results from multiple bookmakers
    market_results = [bookmaker_a_result, bookmaker_b_result]
    
    opportunity = await create_arbitrage_opportunity(market_results, min_profit_margin=2.0)
    
    if opportunity:
        print(f"Arbitrage found!")
        print(f"Profit margin: {opportunity.profit_margin:.4f}%")
        print(f"Expected profit: ${opportunity.profit_amount}")
        
        for leg in opportunity.legs:
            print(f"  {leg.bookmaker}: {leg.event_outcome} @ {leg.odds}")
    else:
        print("No arbitrage opportunity found")

asyncio.run(find_arbitrage())
```

## Configuration

The system integrates with the existing ARBitech configuration system:

```yaml
# config/config.yaml
system:
  vlm:
    endpoint: "http://localhost:8080/vlm"
    api_key: null
    timeout: 30
    retry_attempts: 3
    rate_limit_per_minute: 60
    enabled: true
```

## Supported Bookmakers

- **Betfair**: Exchange interface with back/lay odds
- **Pinnacle**: Professional betting interface
- **BetDex**: Modern betting platform
- **Aver**: Regional bookmaker support

## Supported Odds Formats

- Decimal (e.g., 2.50, 1.85)
- Fractional (e.g., 3/2, 4/5)
- American (e.g., +150, -200)
- Hong Kong, Indonesian, Malaysian

## Quality Assurance

The system includes comprehensive validation:

- **Mathematical validation**: Odds ranges, implied probabilities
- **Format validation**: Odds format detection and normalization
- **Consistency checks**: Cross-bookmaker comparisons
- **Business logic**: Market structure validation
- **Freshness checks**: Odds age validation

## Error Handling

Robust error handling with:
- Detailed error messages and codes
- Confidence scoring for uncertain extractions
- Graceful degradation for partial failures
- Comprehensive logging for debugging

## Performance

- **Batch processing**: Handle multiple images efficiently
- **Rate limiting**: Respect VLM API limits
- **Async operations**: Non-blocking extraction and parsing
- **Caching**: Template and configuration caching
- **Parallel processing**: Concurrent validation across bookmakers

## Integration

The system integrates seamlessly with:
- **ArbitrageOpportunity model** from `storage/models.py`
- **Configuration system** from `core/config_manager.py`
- **Existing logging** and monitoring systems
- **Risk management** and validation frameworks

## Demo

Run the demo script to see all features:

```bash
python vlm/demo.py
```

This will demonstrate:
- Odds extraction setup
- Response parsing
- Template management
- Odds validation
- Cross-bookmaker validation
- Arbitrage opportunity detection

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   VLM Service   │    │  OddsExtractor   │    │ TemplateManager │
│  (Qwen-VL API)  │◄──►│   (Core Engine) │◄──►│ (Bookmaker      │
│                 │    │                  │    │  Templates)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌──────────────────┐             │
         └──────────────►│   OddsParser    │◄────────────┘
                        │  (Validation &  │
                        │   Normalization)│
                        └──────────────────┘
                                 │
                        ┌──────────────────┐
                        │ OddsValidator    │
                        │ (Cross-validation│
                        │  & Constraints)  │
                        └──────────────────┘
```

## Future Enhancements

- Support for more bookmakers
- Machine learning-based confidence scoring
- Real-time odds stream processing
- Advanced arbitrage strategies
- Integration with live trading systems