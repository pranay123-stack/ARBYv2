#!/usr/bin/env python3
"""
Shared utilities for ARBITech examples

This module provides common data structures and utilities used across multiple examples.
"""

from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Any


class Sport(Enum):
    """Supported sports for arbitrage betting"""
    FOOTBALL = "football"
    BASKETBALL = "basketball"
    TENNIS = "tennis"
    BASEBALL = "baseball"
    HOCKEY = "hockey"


class RiskTier(Enum):
    """Risk tiers for arbitrage opportunities"""
    TIER_A = "TIER_A"  # Safest - conservative limit
    TIER_B = "TIER_B"  # Moderate - medium limit
    TIER_C = "TIER_C"  # Higher - aggressive limit


class TradeStatus(Enum):
    """Status of a trade"""
    PENDING = "pending"
    FILLED = "filled"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SETTLED = "settled"


@dataclass
class BettingLeg:
    """Represents a single betting leg in an arbitrage opportunity"""
    bookmaker: str
    outcome: str
    odds: float
    stake: float


@dataclass
class ArbitrageOpportunity:
    """Represents an arbitrage opportunity"""
    sport: str
    event: str
    profit_margin: float
    risk_tier: str
    required_stake: float
    expected_return: float
    legs: List[BettingLeg]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class Trade:
    """Represents an executed trade"""
    id: str
    opportunity: ArbitrageOpportunity
    status: TradeStatus
    total_stake: float
    expected_return: float
    actual_return: float = 0.0
    profit_loss: float = 0.0
    execution_time: datetime = None
    screenshots: List[str] = None
    
    def __post_init__(self):
        if self.execution_time is None:
            self.execution_time = datetime.now()
        if self.screenshots is None:
            self.screenshots = []


class MockOpportunityScanner:
    """Mock scanner that simulates API responses for demonstration"""
    
    def __init__(self):
        self.bookmakers = []
        self.sports = []
        self.min_profit = 0.02
    
    def set_bookmakers(self, bookmakers: List[str]):
        self.bookmakers = bookmakers
    
    def set_sports(self, sports: List[str]):
        self.sports = sports
    
    def set_min_profit(self, min_profit: float):
        self.min_profit = min_profit
    
    async def scan_markets(self) -> List[ArbitrageOpportunity]:
        """Simulate scanning for opportunities"""
        import asyncio
        
        # Simulate API delay
        await asyncio.sleep(2)
        
        # Generate mock opportunities based on configured parameters
        all_opportunities = [
            ArbitrageOpportunity(
                sport=Sport.FOOTBALL.value,
                event="Manchester United vs Liverpool",
                profit_margin=0.025,
                risk_tier=RiskTier.TIER_A.value,
                required_stake=100.00,
                expected_return=102.50,
                legs=[
                    BettingLeg("bet365", "Man United", 2.10, 48.81),
                    BettingLeg("william_hill", "Liverpool", 1.95, 51.19)
                ]
            ),
            ArbitrageOpportunity(
                sport=Sport.BASKETBALL.value,
                event="Lakers vs Warriors",
                profit_margin=0.031,
                risk_tier=RiskTier.TIER_A.value,
                required_stake=150.00,
                expected_return=154.65,
                legs=[
                    BettingLeg("bet365", "Lakers", 2.05, 73.17),
                    BettingLeg("pinnacle", "Warriors", 1.98, 76.83)
                ]
            ),
            ArbitrageOpportunity(
                sport=Sport.TENNIS.value,
                event="Djokovic vs Nadal",
                profit_margin=0.018,
                risk_tier=RiskTier.TIER_B.value,
                required_stake=200.00,
                expected_return=203.60,
                legs=[
                    BettingLeg("bet365", "Djokovic", 2.00, 101.80),
                    BettingLeg("william_hill", "Nadal", 2.02, 98.20)
                ]
            )
        ]
        
        # Filter by minimum profit
        filtered = [opp for opp in all_opportunities if opp.profit_margin >= self.min_profit]
        
        # Further filter by configured sports
        if self.sports:
            filtered = [opp for opp in filtered if opp.sport in self.sports]
        
        return filtered


def format_currency(amount: float) -> str:
    """Format amount as currency"""
    return f"${amount:.2f}"


def format_percentage(value: float) -> str:
    """Format value as percentage"""
    return f"{value:.2%}"


def calculate_profit(opportunity: ArbitrageOpportunity) -> float:
    """Calculate expected profit from opportunity"""
    return opportunity.expected_return - opportunity.required_stake


def validate_opportunity(opportunity: ArbitrageOpportunity) -> Dict[str, Any]:
    """Validate an arbitrage opportunity"""
    errors = []
    warnings = []
    
    # Check profit margin
    if opportunity.profit_margin < 0.005:  # 0.5%
        warnings.append("Very low profit margin")
    elif opportunity.profit_margin > 0.1:  # 10%
        warnings.append("Unusually high profit margin - check for errors")
    
    # Check odds validity
    for leg in opportunity.legs:
        if leg.odds < 1.01:
            errors.append(f"Invalid odds at {leg.bookmaker}: {leg.odds}")
    
    # Check stake distribution
    total_stake = sum(leg.stake for leg in opportunity.legs)
    if abs(total_stake - opportunity.required_stake) > 0.01:
        errors.append("Stake distribution doesn't match required stake")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


def simulate_api_delay(min_seconds: float = 1.0, max_seconds: float = 3.0):
    """Simulate API delay for demonstrations"""
    import asyncio
    import random
    
    delay = random.uniform(min_seconds, max_seconds)
    return asyncio.sleep(delay)