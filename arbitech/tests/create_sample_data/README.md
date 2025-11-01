# Sample Data Directory for VLM Testing

This directory contains mock betting interface screenshots and ground truth odds data for testing VLM accuracy.

## Directory Structure

```
create_sample_data/
├── betting_interfaces/          # Mock interface images
├── ground_truth_data/           # Ground truth odds data in JSON format
├── test_scenarios/             # Specific test scenario configurations
└── metadata/                   # Metadata about test data
```

## Mock Images

The `betting_interfaces/` directory contains placeholder images that simulate real betting interfaces:

### Supported Bookmakers
- **Bet365**: Complex layouts with overlays and dynamic elements
- **William Hill**: Clean interfaces with navigation menus
- **Ladbrokes**: Bet builder interfaces and in-play sections
- **Betfair Exchange**: Back/lay odds displays and market data
- **Pinnacle**: Asian handicap and live betting interfaces
- **1xBet**: Multi-language and casino-integrated interfaces

### Image Categories

1. **Perfect Interfaces** (`perfect_*.png`)
   - Clear, unobstructed views of betting interfaces
   - High resolution with readable text
   - Standard layouts without overlays

2. **Complex Interfaces** (`complex_*.png`)
   - Multi-market displays
   - Live betting interfaces with dynamic updates
   - Bet builder and accumulator interfaces

3. **Edge Cases** (`edge_case_*.png`)
   - Partial interfaces (cropped views)
   - Loading states with spinners
   - Error pages and maintenance messages
   - Low resolution or blurry images
   - Multi-language interfaces

4. **Mobile Views** (`mobile_*.png`)
   - Mobile-optimized interfaces
   - Touch-friendly layouts
   - Responsive design variations

## Ground Truth Data

The `ground_truth_data/` directory contains JSON files with accurate odds data corresponding to the mock images.

### File Naming Convention
- `<bookmaker>_<sport>_<market_type>_<image_name>.json`
- Example: `bet365_football_match_winner_perfect_football_interface.json`

### Ground Truth Data Format

```json
{
  "image_filename": "perfect_football_interface.png",
  "bookmaker": "Bet365",
  "sport": "Football",
  "event_name": "Manchester United vs Liverpool",
  "event_date": "2024-03-15T15:00:00Z",
  "market_type": "match_winner",
  "odds": [
    {
      "outcome": "Home Win",
      "decimal_odds": 2.10,
      "fractional_odds": "11/10",
      "implied_probability": 0.476,
      "american_odds": +110
    },
    {
      "outcome": "Draw",
      "decimal_odds": 3.20,
      "fractional_odds": "11/5",
      "implied_probability": 0.313,
      "american_odds": +220
    },
    {
      "outcome": "Away Win",
      "decimal_odds": 3.80,
      "fractional_odds": "14/5",
      "implied_probability": 0.263,
      "american_odds": +280
    }
  ],
  "ui_elements": [
    "odds_display",
    "team_names",
    "live_indicator",
    "cash_out_button"
  ],
  "extraction_difficulty": "easy",
  "validation_notes": [
    "Clear interface with no obstructions",
    "Standard odds format",
    "All text clearly readable"
  ]
}
```

## Test Scenarios

The `test_scenarios/` directory contains configuration files for specific testing scenarios.

### Scenario Types

1. **Accuracy Tests**
   - `basic_accuracy.json`: Standard extraction tests
   - `high_accuracy.json`: Focus on precision metrics

2. **Edge Case Tests**
   - `partial_interfaces.json`: Tests with incomplete data
   - `loading_states.json`: Tests during loading periods
   - `error_handling.json`: Tests with error pages

3. **Performance Tests**
   - `speed_benchmark.json`: Processing time tests
   - `batch_processing.json`: Multiple simultaneous extractions

4. **Bookmaker-Specific Tests**
   - `<bookmaker>_specific.json`: Tests tailored to each bookmaker

### Scenario Configuration Format

```json
{
  "scenario_name": "Basic Accuracy Test",
  "description": "Test VLM accuracy on standard betting interfaces",
  "test_images": [
    {
      "image": "perfect_football_interface.png",
      "ground_truth": "bet365_football_match_winner_perfect_football_interface.json",
      "expected_success_rate": 0.90,
      "tolerance": {
        "odds_variance": 0.05,
        "confidence_threshold": 0.75
      }
    }
  ],
  "success_criteria": {
    "minimum_accuracy": 0.85,
    "maximum_false_positive_rate": 0.10,
    "minimum_confidence": 0.70
  }
}
```

## Metadata

The `metadata/` directory contains information about the test dataset.

### Dataset Statistics
- Total number of images per bookmaker
- Distribution of difficulty levels
- Coverage of different sports and market types
- Quality metrics of mock images

### Version Information
- Creation date
- Data version
- Last updated timestamp
- Contributing sources

## Usage in Tests

### Test Integration
The sample data is used by the VLM testing framework:

```python
from arbitech.tests.create_sample_data import SampleDataProvider

# Load sample data for testing
provider = SampleDataProvider()
test_images = provider.get_test_images(bookmaker="bet365", difficulty="easy")
ground_truth = provider.get_ground_truth_data(test_images[0])
```

### Validation
Ground truth data is used to validate VLM extraction accuracy:

```python
from arbitech.tests.test_vlm_accuracy import VLMAccuracyTestSuite

# Run tests with sample data
test_suite = VLMAccuracyTestSuite()
test_suite.sample_data_path = "arbitech/tests/create_sample_data"
results = test_suite.run_basic_accuracy_tests()
```

## Notes

- All mock images are synthetic representations and do not contain actual bookmaker logos or proprietary designs
- Ground truth data is realistic but artificially generated for testing purposes
- Test scenarios cover a wide range of difficulty levels and edge cases
- Data is regularly updated to reflect new bookmaker interface variations

## Contributing

When adding new test data:

1. Place mock images in the appropriate category folder
2. Create corresponding ground truth JSON files
3. Update metadata files with new statistics
4. Follow the established naming conventions
5. Ensure all sensitive or proprietary information is removed or genericized