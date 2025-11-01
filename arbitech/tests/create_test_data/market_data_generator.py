"""
Realistic Arbitrage Test Data Generator

Generates comprehensive test data for arbitrage detection including:
- Market scenarios with known arbitrage opportunities
- Realistic bookmaker odds with natural variations
- Stress test data with high-frequency changes
- Edge cases and boundary conditions
"""

import json
import random
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Tuple
import math


class ArbitrageTestDataGenerator:
    """Generator for realistic arbitrage testing data."""
    
    def __init__(self, seed: int = 42):
        random.seed(seed)
        
    def generate_market_scenario(self, scenario_type: str) -> Dict[str, Any]:
        """Generate a complete market scenario with multiple bookmakers."""
        
        if scenario_type == "clear_arbitrage":
            return self._generate_clear_arbitrage_scenario()
        elif scenario_type == "marginal_arbitrage":
            return self._generate_marginal_arbitrage_scenario()
        elif scenario_type == "no_arbitrage":
            return self._generate_no_arbitrage_scenario()
        elif scenario_type == "edge_cases":
            return self._generate_edge_case_scenario()
        elif scenario_type == "high_frequency":
            return self._generate_high_frequency_scenario()
        else:
            raise ValueError(f"Unknown scenario type: {scenario_type}")
    
    def _generate_clear_arbitrage_scenario(self) -> Dict[str, Any]:
        """Generate scenario with clear arbitrage opportunity."""
        bookmakers = ["Bet365", "William Hill", "Ladbrokes", "Betfair", "Pinnacle"]
        outcomes = ["Home Win", "Draw", "Away Win"]
        
        odds_by_bookmaker = {}
        
        # Create intentional arbitrage by having different best odds for each outcome
        odds_configs = [
            [Decimal("2.10"), Decimal("1.90"), Decimal("3.20")],  # Bookmaker 1 has best Home and Draw
            [Decimal("1.95"), Decimal("2.20"), Decimal("2.80")],  # Bookmaker 2 has best Away
            [Decimal("2.05"), Decimal("1.95"), Decimal("3.00")],  # Bookmaker 3 has competitive odds
            [Decimal("2.00"), Decimal("2.10"), Decimal("2.90")],  # Bookmaker 4
            [Decimal("2.08"), Decimal("2.05"), Decimal("3.15")]   # Bookmaker 5
        ]
        
        for i, bookmaker in enumerate(bookmakers):
            odds_by_bookmaker[bookmaker] = odds_configs[i]
        
        return {
            "scenario_id": "clear_arbitrage_001",
            "sport": "Football",
            "event_name": "Manchester United vs Liverpool",
            "event_date": datetime.now() + timedelta(days=1),
            "market_type": "match_winner",
            "odds_by_bookmaker": {k: [float(x) for x in v] for k, v in odds_by_bookmaker.items()},
            "expected_arbitrage": True,
            "expected_profit_margin": 0.032,  # ~3.2%
            "difficulty": "easy",
            "notes": "Clear arbitrage opportunity with well-defined best odds for each outcome"
        }
    
    def _generate_marginal_arbitrage_scenario(self) -> Dict[str, Any]:
        """Generate scenario with marginal arbitrage opportunity."""
        bookmakers = ["Bet365", "Pinnacle", "1xBet"]
        outcomes = ["Home Win", "Away Win"]
        
        # Very close to break-even odds
        odds_by_bookmaker = {
            "Bet365": [Decimal("1.98"), Decimal("1.99")],
            "Pinnacle": [Decimal("1.97"), Decimal("2.01")],
            "1xBet": [Decimal("2.00"), Decimal("1.97")]
        }
        
        return {
            "scenario_id": "marginal_arbitrage_001",
            "sport": "Tennis",
            "event_name": "Djokovic vs Nadal",
            "event_date": datetime.now() + timedelta(days=2),
            "market_type": "match_winner",
            "odds_by_bookmaker": {k: [float(x) for x in v] for k, v in odds_by_bookmaker.items()},
            "expected_arbitrage": False,  # Very marginal - treat as no arbitrage
            "expected_profit_margin": 0.001,  # ~0.1%
            "difficulty": "hard",
            "notes": "Marginal arbitrage opportunity requiring precise calculation"
        }
    
    def _generate_no_arbitrage_scenario(self) -> Dict[str, Any]:
        """Generate scenario with no arbitrage opportunity."""
        bookmakers = ["Bet365", "William Hill", "Ladbrokes"]
        outcomes = ["Over 2.5", "Under 2.5"]
        
        # Standard bookmaker margins
        odds_by_bookmaker = {
            "Bet365": [Decimal("1.85"), Decimal("1.95")],
            "William Hill": [Decimal("1.87"), Decimal("1.93")],
            "Ladbrokes": [Decimal("1.83"), Decimal("1.97")]
        }
        
        return {
            "scenario_id": "no_arbitrage_001",
            "sport": "Football",
            "event_name": "Arsenal vs Chelsea",
            "event_date": datetime.now() + timedelta(hours=6),
            "market_type": "total_goals",
            "odds_by_bookmaker": {k: [float(x) for x in v] for k, v in odds_by_bookmaker.items()},
            "expected_arbitrage": False,
            "expected_profit_margin": -0.055,  # ~5.5% house edge
            "difficulty": "easy",
            "notes": "Standard market with typical bookmaker margins"
        }
    
    def _generate_edge_case_scenario(self) -> Dict[str, Any]:
        """Generate edge case scenarios."""
        scenarios = []
        
        # Edge case 1: Very high odds
        high_odds_scenario = {
            "scenario_id": "edge_case_high_odds",
            "sport": "Football",
            "event_name": "Real Madrid vs Barcelona",
            "event_date": datetime.now() + timedelta(days=7),
            "market_type": "exact_score",
            "odds_by_bookmaker": {
                "Bet365": [Decimal("15.0"), Decimal("25.0"), Decimal("50.0")],
                "William Hill": [Decimal("14.0"), Decimal("30.0"), Decimal("45.0")]
            },
            "expected_arbitrage": True,
            "difficulty": "medium",
            "notes": "High odds scenario testing precision with large numbers"
        }
        scenarios.append(high_odds_scenario)
        
        # Edge case 2: Very low odds
        low_odds_scenario = {
            "scenario_id": "edge_case_low_odds",
            "sport": "Football",
            "event_name": "Manchester City vs Burnley",
            "event_date": datetime.now() + timedelta(hours=3),
            "market_type": "match_winner",
            "odds_by_bookmaker": {
                "Pinnacle": [Decimal("1.05"), Decimal("15.0"), Decimal("50.0")],
                "Bet365": [Decimal("1.03"), Decimal("18.0"), Decimal("60.0")]
            },
            "expected_arbitrage": True,
            "difficulty": "hard",
            "notes": "Very low odds scenario testing boundary conditions"
        }
        scenarios.append(low_odds_scenario)
        
        # Edge case 3: Many outcomes
        many_outcomes_scenario = {
            "scenario_id": "edge_case_many_outcomes",
            "sport": "Horse Racing",
            "event_name": "Grand National",
            "event_date": datetime.now() + timedelta(days=14),
            "market_type": "winner",
            "odds_by_bookmaker": {
                "Bet365": [Decimal(x) for x in [3.5, 4.0, 6.0, 8.0, 12.0, 15.0]],
                "William Hill": [Decimal(x) for x in [3.2, 4.2, 5.8, 7.5, 13.0, 16.0]]
            },
            "expected_arbitrage": False,
            "difficulty": "hard",
            "notes": "Many outcomes scenario testing scalability"
        }
        scenarios.append(many_outcomes_scenario)
        
        return scenarios
    
    def _generate_high_frequency_scenario(self) -> Dict[str, Any]:
        """Generate high-frequency market data for stress testing."""
        base_scenario = self._generate_clear_arbitrage_scenario()
        base_scenario["scenario_id"] = "high_freq_001"
        
        # Generate 100 data points with changing odds
        market_updates = []
        base_odds = base_scenario["odds_by_bookmaker"]
        
        for i in range(100):
            timestamp = datetime.now() + timedelta(seconds=i)
            
            # Simulate natural odds movement
            update = {
                "timestamp": timestamp.isoformat(),
                "odds_by_bookmaker": {}
            }
            
            for bookmaker, odds in base_odds.items():
                # Add small random variations (±2%)
                decimal_odds = [Decimal(str(odd)) for odd in odds]
                varied_odds = [odd * Decimal(str(random.uniform(0.98, 1.02))) for odd in decimal_odds]
                update["odds_by_bookmaker"][bookmaker] = [float(x) for x in varied_odds]
                
            market_updates.append(update)
        
        base_scenario["market_updates"] = market_updates
        base_scenario["update_frequency"] = "1_second"
        base_scenario["total_updates"] = 100
        
        return base_scenario
    
    def generate_bookmaker_dataset(self, num_bookmakers: int = 10, num_events: int = 50) -> Dict[str, Any]:
        """Generate comprehensive bookmaker odds dataset."""
        
        bookmakers = [
            "Bet365", "William Hill", "Ladbrokes", "Betfair", "Pinnacle", 
            "1xBet", "Unibet", "Betway", "LeoVegas", "Mr Green"
        ]
        
        sports = ["Football", "Tennis", "Basketball", "Baseball"]
        events = [
            "Team A vs Team B", "Player X vs Player Y", "Home vs Away",
            "Over/Under Scenario", "Handicap Match", "Exact Score Bet"
        ]
        
        dataset = {
            "dataset_id": f"bookmaker_dataset_{num_bookmakers}_{num_events}",
            "generated_at": datetime.now().isoformat(),
            "num_bookmakers": num_bookmakers,
            "num_events": num_events,
            "bookmakers": bookmakers[:num_bookmakers],
            "events": []
        }
        
        selected_bookmakers = bookmakers[:num_bookmakers]
        
        for i in range(num_events):
            event = {
                "event_id": f"event_{i:03d}",
                "sport": random.choice(sports),
                "event_name": random.choice(events),
                "event_date": datetime.now() + timedelta(hours=random.randint(1, 168)),
                "market_type": random.choice(["match_winner", "total_goals", "handicap"]),
                "odds_by_bookmaker": {}
            }
            
            # Generate realistic odds with some intentional arbitrage
            num_outcomes = random.choice([2, 3])
            base_odds = [Decimal(str(random.uniform(1.5, 4.0))) for _ in range(num_outcomes)]
            
            for bookmaker in selected_bookmakers:
                # Add bookmaker-specific variations
                bookmaker_variation = random.uniform(0.95, 1.05)
                odds = [odd * Decimal(str(bookmaker_variation)) for odd in base_odds]
                
                # Some bookmakers might have better odds for specific outcomes
                if random.random() < 0.3:  # 30% chance of better odds
                    best_outcome = random.randint(0, num_outcomes - 1)
                    odds[best_outcome] *= Decimal(str(random.uniform(1.05, 1.15)))
                
                event["odds_by_bookmaker"][bookmaker] = [float(x) for x in odds]
            
            dataset["events"].append(event)
        
        return dataset
    
    def generate_performance_test_data(self) -> Dict[str, Any]:
        """Generate data for performance and scalability testing."""
        
        # Large dataset for stress testing
        large_dataset = {
            "test_id": "performance_stress_001",
            "test_type": "scalability",
            "num_events": 1000,
            "num_bookmakers": 20,
            "complexity": "high",
            "description": "Large-scale arbitrage detection stress test"
        }
        
        # High-frequency data
        high_freq_data = {
            "test_id": "performance_highfreq_001", 
            "test_type": "high_frequency",
            "update_frequency": "100ms",
            "duration_minutes": 5,
            "total_updates": 3000,
            "description": "High-frequency market data processing test"
        }
        
        # Memory usage test
        memory_test = {
            "test_id": "performance_memory_001",
            "test_type": "memory_usage",
            "data_size_gb": 1.0,
            "complexity": "extreme",
            "description": "Memory usage and garbage collection test"
        }
        
        return {
            "performance_tests": {
                "stress_test": large_dataset,
                "high_frequency_test": high_freq_data,
                "memory_test": memory_test
            }
        }
    
    def save_test_data(self, data: Dict[str, Any], filepath: str):
        """Save generated test data to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def generate_all_test_data(self, output_dir: str = "test_data"):
        """Generate all test data and save to files."""
        import os
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate individual scenarios
        scenarios = [
            "clear_arbitrage", "marginal_arbitrage", "no_arbitrage", 
            "edge_cases", "high_frequency"
        ]
        
        for scenario in scenarios:
            data = self.generate_market_scenario(scenario)
            if isinstance(data, list):
                for i, scenario_data in enumerate(data):
                    filename = f"{scenario}_{i+1:02d}.json"
                    filepath = os.path.join(output_dir, filename)
                    self.save_test_data(scenario_data, filepath)
            else:
                filename = f"{scenario}.json"
                filepath = os.path.join(output_dir, filename)
                self.save_test_data(data, filepath)
        
        # Generate comprehensive datasets
        bookmaker_dataset = self.generate_bookmaker_dataset(10, 50)
        self.save_test_data(bookmaker_dataset, os.path.join(output_dir, "bookmaker_dataset.json"))
        
        performance_data = self.generate_performance_test_data()
        self.save_test_data(performance_data, os.path.join(output_dir, "performance_tests.json"))
        
        # Generate test data index
        index = {
            "test_data_index": {
                "generated_at": datetime.now().isoformat(),
                "total_files": len(os.listdir(output_dir)),
                "files": os.listdir(output_dir),
                "categories": {
                    "market_scenarios": [f for f in os.listdir(output_dir) if not f.startswith("bookmaker") and not f.startswith("performance")],
                    "bookmaker_datasets": [f for f in os.listdir(output_dir) if "bookmaker" in f],
                    "performance_tests": [f for f in os.listdir(output_dir) if "performance" in f]
                }
            }
        }
        
        self.save_test_data(index, os.path.join(output_dir, "index.json"))
        
        return output_dir


if __name__ == "__main__":
    generator = ArbitrageTestDataGenerator()
    output_directory = generator.generate_all_test_data("test_data")
    print(f"Test data generated in: {output_directory}")
    print("Files created:")
    import os
    for file in os.listdir(output_directory):
        print(f"  - {file}")