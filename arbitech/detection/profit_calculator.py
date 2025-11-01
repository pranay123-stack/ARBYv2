"""
Advanced Profit and Loss Calculator

This module provides sophisticated profit and loss calculations including commission fees,
exchange rates, time value of money, and complex financial metrics for arbitrage betting.
"""

import math
from typing import List, Dict, Optional, Tuple, Union, Any
from decimal import Decimal, getcontext, ROUND_HALF_UP
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging

# Configure decimal precision for financial calculations
getcontext().prec = 50


class ProfitType(Enum):
    """Types of profit calculations."""
    ABSOLUTE = "absolute"
    PERCENTAGE = "percentage"
    ROI = "roi"
    CAGR = "cagr"
    RISK_ADJUSTED = "risk_adjusted"


class FeeStructureType(Enum):
    """Types of fee structures."""
    PERCENTAGE = "percentage"
    FIXED = "fixed"
    HYBRID = "hybrid"
    TIERED = "tiered"


class CurrencyType(Enum):
    """Types of currency representations."""
    BASE = "base_currency"
    FOREIGN = "foreign_currency"
    CRYPTO = "crypto_currency"


@dataclass
class FeeStructureConfig:
    """Represents a fee structure for bookmaker/exchange."""
    structure_type: FeeStructureType
    percentage_rate: Optional[Decimal] = None
    fixed_amount: Optional[Decimal] = None
    tier_rates: Optional[List[Tuple[Decimal, Decimal]]] = None  # (threshold, rate) pairs
    minimum_fee: Optional[Decimal] = None
    maximum_fee: Optional[Decimal] = None


@dataclass
class ExchangeRate:
    """Represents currency exchange rates."""
    from_currency: str
    to_currency: str
    rate: Decimal
    timestamp: datetime
    source: str
    confidence_level: Decimal = Decimal('1.0')


@dataclass
class TimeValueParameters:
    """Parameters for time value of money calculations."""
    annual_rate: Decimal
    compounding_frequency: int = 365  # Daily compounding
    inflation_rate: Decimal = Decimal('0')
    risk_free_rate: Decimal = Decimal('0.02')  # 2% default
    discounting_method: str = 'continuous'  # 'simple', 'compound', 'continuous'


@dataclass
class ProfitCalculation:
    """Results of profit and loss calculations."""
    calculation_id: str
    gross_profit: Decimal
    net_profit: Decimal
    total_fees: Decimal
    roi_percentage: Decimal
    annualized_return: Optional[Decimal]
    risk_adjusted_return: Optional[Decimal]
    time_value_profit: Optional[Decimal]
    currency_adjusted_profit: Optional[Decimal]
    fee_breakdown: Dict[str, Decimal]
    calculation_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CommissionStructure:
    """Detailed commission structure for betting platforms."""
    platform_name: str
    commission_type: FeeStructureConfig
    withdrawal_fees: FeeStructureConfig
    deposit_fees: Optional[FeeStructureConfig]
    currency_conversion_fees: Optional[FeeStructureConfig]
    inactivity_fees: Optional[FeeStructureConfig]
    account_tier: str = 'standard'


class AdvancedProfitCalculator:
    """
    Advanced profit and loss calculator for arbitrage betting.
    
    This class provides sophisticated calculations including:
    - Commission and fee calculations
    - Exchange rate adjustments
    - Time value of money analysis
    - Risk-adjusted returns
    - Currency and inflation adjustments
    """
    
    def __init__(self, base_currency: str = 'USD'):
        """
        Initialize the profit calculator.
        
        Args:
            base_currency: Base currency for calculations
        """
        self.base_currency = base_currency
        self.logger = logging.getLogger(__name__)
        
        # Exchange rates cache
        self._exchange_rates: Dict[str, ExchangeRate] = {}
        
        # Default fee structures (commonly used rates)
        self.default_fee_structures = {
            'bet365': CommissionStructure(
                platform_name='bet365',
                commission_type=FeeStructureConfig(FeeStructureType.PERCENTAGE, percentage_rate=Decimal('0.05')),
                withdrawal_fees=FeeStructureConfig(FeeStructureType.FIXED, fixed_amount=Decimal('2.50')),
                deposit_fees=None,
                currency_conversion_fees=FeeStructureConfig(FeeStructureType.PERCENTAGE, percentage_rate=Decimal('0.03')),
                inactivity_fees=None
            ),
            'pinnacle': CommissionStructure(
                platform_name='pinnacle',
                commission_type=FeeStructureConfig(FeeStructureType.PERCENTAGE, percentage_rate=Decimal('0.02')),
                withdrawal_fees=FeeStructureConfig(FeeStructureType.FIXED, fixed_amount=Decimal('10.00')),
                deposit_fees=None,
                currency_conversion_fees=None,
                inactivity_fees=FeeStructureConfig(FeeStructureType.FIXED, fixed_amount=Decimal('5.00'))
            ),
            'betfair': CommissionStructure(
                platform_name='betfair',
                commission_type=FeeStructureConfig(FeeStructureType.PERCENTAGE, percentage_rate=Decimal('0.05')),
                withdrawal_fees=FeeStructureConfig(FeeStructureType.FIXED, fixed_amount=Decimal('0.75')),
                deposit_fees=None,
                currency_conversion_fees=FeeStructureConfig(FeeStructureType.PERCENTAGE, percentage_rate=Decimal('0.01')),
                inactivity_fees=None
            )
        }

    def calculate_profit_with_fees(
        self,
        stake: Decimal,
        odds: Decimal,
        commission_rate: Decimal,
        platform_fees: Optional[Dict[str, Decimal]] = None
    ) -> Dict[str, Decimal]:
        """
        Calculate profit including all fees and commissions.
        
        Args:
            stake: Amount staked
            odds: Decimal odds
            commission_rate: Commission rate (0.05 = 5%)
            platform_fees: Additional platform-specific fees
            
        Returns:
            Dictionary containing detailed profit calculations
        """
        if stake <= 0:
            raise ValueError("Stake must be positive")
        
        if odds <= 1:
            raise ValueError("Odds must be greater than 1")
        
        # Calculate gross return
        gross_return = stake * odds
        
        # Calculate commission
        commission = gross_return * commission_rate
        
        # Calculate platform fees
        platform_fee_total = Decimal('0')
        if platform_fees:
            for fee_name, fee_amount in platform_fees.items():
                platform_fee_total += fee_amount
        
        # Calculate net profit
        net_return = gross_return - commission - platform_fee_total
        net_profit = net_return - stake
        
        return {
            'stake': stake.quantize(Decimal('0.01')),
            'gross_return': gross_return.quantize(Decimal('0.01')),
            'commission': commission.quantize(Decimal('0.01')),
            'platform_fees': platform_fee_total.quantize(Decimal('0.01')),
            'net_return': net_return.quantize(Decimal('0.01')),
            'net_profit': net_profit.quantize(Decimal('0.01')),
            'roi_percentage': (net_profit / stake * Decimal('100')).quantize(Decimal('0.01')),
            'effective_odds': ((net_return / stake) if stake > 0 else Decimal('0')).quantize(Decimal('0.001'))
        }

    def calculate_arbitrage_profit_with_fees(
        self,
        legs: List[Dict[str, Any]],
        total_stake: Decimal,
        commission_rates: Dict[str, Decimal],
        platform_fees: Optional[Dict[str, Dict[str, Decimal]]] = None
    ) -> ProfitCalculation:
        """
        Calculate arbitrage profit with all fees and costs included.
        
        Args:
            legs: List of betting legs with 'bookmaker', 'stake', 'odds', 'selection'
            total_stake: Total amount staked across all legs
            commission_rates: Commission rates by bookmaker
            platform_fees: Additional fees by bookmaker
            
        Returns:
            ProfitCalculation object with detailed results
        """
        if not legs:
            raise ValueError("At least one leg required")
        
        if total_stake <= 0:
            raise ValueError("Total stake must be positive")
        
        # Calculate gross returns for each leg
        leg_returns = []
        total_commission = Decimal('0')
        total_platform_fees = Decimal('0')
        
        fee_breakdown = {}
        
        for leg in legs:
            bookmaker = leg['bookmaker']
            stake = leg['stake']
            odds = leg['odds']
            commission_rate = commission_rates.get(bookmaker, Decimal('0.05'))
            
            # Calculate gross return
            gross_return = stake * odds
            
            # Calculate commission
            commission = gross_return * commission_rate
            total_commission += commission
            
            # Calculate platform fees
            leg_platform_fees = Decimal('0')
            if platform_fees and bookmaker in platform_fees:
                for fee_name, fee_amount in platform_fees[bookmaker].items():
                    leg_platform_fees += fee_amount
            total_platform_fees += leg_platform_fees
            
            # Net return for this leg
            net_return = gross_return - commission - leg_platform_fees
            
            leg_returns.append(net_return)
            
            # Fee breakdown
            fee_breakdown[f"{bookmaker}_commission"] = fee_breakdown.get(f"{bookmaker}_commission", Decimal('0')) + commission
            fee_breakdown[f"{bookmaker}_platform_fees"] = fee_breakdown.get(f"{bookmaker}_platform_fees", Decimal('0')) + leg_platform_fees
        
        # Worst-case scenario (minimum return across all legs)
        worst_case_return = min(leg_returns)
        best_case_return = max(leg_returns)
        
        # Calculate profits
        gross_profit = worst_case_return - total_stake
        net_profit = gross_profit  # Already net of fees
        
        # Calculate ROI
        roi_percentage = (net_profit / total_stake) * Decimal('100')
        
        # Calculate fee percentages
        commission_percentage = (total_commission / worst_case_return) * Decimal('100') if worst_case_return > 0 else Decimal('0')
        platform_fee_percentage = (total_platform_fees / worst_case_return) * Decimal('100') if worst_case_return > 0 else Decimal('0')
        
        return ProfitCalculation(
            calculation_id=f"ARB_PROFIT_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            gross_profit=gross_profit.quantize(Decimal('0.01')),
            net_profit=net_profit.quantize(Decimal('0.01')),
            total_fees=(total_commission + total_platform_fees).quantize(Decimal('0.01')),
            roi_percentage=roi_percentage.quantize(Decimal('0.01')),
            annualized_return=None,  # Will be calculated with time parameters
            risk_adjusted_return=None,  # Will be calculated separately
            time_value_profit=None,  # Will be calculated with time parameters
            currency_adjusted_profit=None,  # Will be calculated with exchange rates
            fee_breakdown={
                **fee_breakdown,
                'total_commission': total_commission.quantize(Decimal('0.01')),
                'total_platform_fees': total_platform_fees.quantize(Decimal('0.01')),
                'commission_percentage': commission_percentage.quantize(Decimal('0.01')),
                'platform_fee_percentage': platform_fee_percentage.quantize(Decimal('0.01'))
            },
            calculation_metadata={
                'num_legs': len(legs),
                'total_stake': total_stake,
                'calculation_timestamp': datetime.now(),
                'worst_case_return': worst_case_return.quantize(Decimal('0.01')),
                'best_case_return': best_case_return.quantize(Decimal('0.01')),
                'currency': self.base_currency
            }
        )

    def calculate_time_value_profit(
        self,
        profit: Decimal,
        stake_period: timedelta,
        time_params: TimeValueParameters
    ) -> Decimal:
        """
        Calculate profit adjusted for time value of money.
        
        Args:
            profit: Profit amount
            stake_period: Duration the stake was held
            time_params: Time value parameters
            
        Returns:
            Time-adjusted profit
        """
        if stake_period.total_seconds() <= 0:
            return profit
        
        # Convert period to years
        period_years = Decimal(str(stake_period.total_seconds() / (365.25 * 24 * 3600)))
        
        # Apply discounting based on method
        if time_params.discounting_method == 'simple':
            # Simple discounting: FV = PV * (1 + r * t)
            discount_factor = Decimal('1') + time_params.annual_rate * period_years
        elif time_params.discounting_method == 'compound':
            # Compound discounting: FV = PV * (1 + r/n)^(n*t)
            n = time_params.compounding_frequency
            discount_factor = (Decimal('1') + time_params.annual_rate / n) ** (n * period_years)
        elif time_params.discounting_method == 'continuous':
            # Continuous discounting: FV = PV * e^(r*t)
            discount_factor = (time_params.annual_rate * period_years).exp()
        else:
            raise ValueError(f"Unknown discounting method: {time_params.discounting_method}")
        
        # Apply inflation adjustment
        inflation_adjustment = Decimal('1') - time_params.inflation_rate * period_years
        
        # Calculate time-adjusted profit
        time_adjusted_profit = profit * discount_factor * inflation_adjustment
        
        return time_adjusted_profit.quantize(Decimal('0.01'))

    def calculate_currency_adjusted_profit(
        self,
        profit: Decimal,
        original_currency: str,
        exchange_rate: ExchangeRate,
        conversion_fees: Optional[Decimal] = None
    ) -> Decimal:
        """
        Calculate profit adjusted for currency exchange and conversion fees.
        
        Args:
            profit: Profit amount in original currency
            original_currency: Currency of the original profit
            exchange_rate: Exchange rate information
            conversion_fees: Currency conversion fees
            
        Returns:
            Currency-adjusted profit in base currency
        """
        # Convert to base currency
        if exchange_rate.from_currency == original_currency and exchange_rate.to_currency == self.base_currency:
            # Direct conversion
            converted_profit = profit * exchange_rate.rate
        elif exchange_rate.to_currency == original_currency and exchange_rate.from_currency == self.base_currency:
            # Reverse conversion
            converted_profit = profit / exchange_rate.rate
        else:
            # Need to convert through intermediate currency
            intermediate_profit = profit
            if exchange_rate.from_currency != original_currency:
                # Find direct conversion rate or use inverse
                # This is a simplified implementation
                self.logger.warning(f"Complex currency conversion required: {original_currency} -> {exchange_rate.from_currency}")
                intermediate_profit = profit  # Simplified
            
            if exchange_rate.to_currency != self.base_currency:
                # Apply conversion
                intermediate_profit = intermediate_profit * exchange_rate.rate
            
            converted_profit = intermediate_profit
        
        # Apply conversion fees
        if conversion_fees:
            converted_profit -= conversion_fees
        
        return converted_profit.quantize(Decimal('0.01'))

    def calculate_risk_adjusted_profit(
        self,
        profit: Decimal,
        stake: Decimal,
        risk_metrics: Dict[str, Decimal]
    ) -> Decimal:
        """
        Calculate risk-adjusted profit using various risk metrics.
        
        Args:
            profit: Absolute profit
            stake: Amount staked
            risk_metrics: Risk metrics (volatility, max drawdown, etc.)
            
        Returns:
            Risk-adjusted profit
        """
        if stake <= 0:
            return profit
        
        # Calculate basic return
        basic_return = profit / stake
        
        # Risk adjustments
        adjustments = Decimal('1')
        
        # Volatility adjustment
        if 'volatility' in risk_metrics:
            volatility_adjustment = Decimal('1') - (risk_metrics['volatility'] / Decimal('100'))
            adjustments *= max(volatility_adjustment, Decimal('0.1'))  # Minimum 10% of return
        
        # Maximum drawdown adjustment
        if 'max_drawdown' in risk_metrics:
            drawdown_adjustment = Decimal('1') - (risk_metrics['max_drawdown'] / Decimal('100'))
            adjustments *= max(drawdown_adjustment, Decimal('0.1'))
        
        # Value at Risk adjustment
        if 'var_95' in risk_metrics:
            var_adjustment = Decimal('1') - (risk_metrics['var_95'] / Decimal('100'))
            adjustments *= max(var_adjustment, Decimal('0.1'))
        
        # Calculate risk-adjusted return
        risk_adjusted_return = basic_return * adjustments
        
        return (risk_adjusted_return * stake).quantize(Decimal('0.01'))

    def calculate_annualized_return(
        self,
        profit: Decimal,
        stake: Decimal,
        period_duration: timedelta
    ) -> Decimal:
        """
        Calculate annualized return from profit over a period.
        
        Args:
            profit: Profit earned during period
            stake: Initial stake
            period_duration: Duration of the period
            
        Returns:
            Annualized return as percentage
        """
        if stake <= 0 or period_duration.total_seconds() <= 0:
            return Decimal('0')
        
        # Calculate period return
        period_return = profit / stake
        
        # Convert to annual return
        period_years = Decimal(str(period_duration.total_seconds() / (365.25 * 24 * 3600)))
        
        if period_years <= 0:
            return Decimal('0')
        
        # Compound annual growth rate (CAGR)
        annualized_return = ((Decimal('1') + period_return) ** (Decimal('1') / period_years) - Decimal('1')) * Decimal('100')
        
        return annualized_return.quantize(Decimal('0.01'))

    def calculate_portfolio_metrics(
        self,
        profit_calculations: List[ProfitCalculation],
        time_periods: Optional[List[timedelta]] = None
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive portfolio-level profit metrics.
        
        Args:
            profit_calculations: List of ProfitCalculation objects
            time_periods: Optional list of time periods for each calculation
            
        Returns:
            Dictionary containing portfolio metrics
        """
        if not profit_calculations:
            return {}
        
        # Calculate basic metrics
        total_gross_profit = sum(calc.gross_profit for calc in profit_calculations)
        total_net_profit = sum(calc.net_profit for calc in profit_calculations)
        total_fees = sum(calc.total_fees for calc in profit_calculations)
        
        # Calculate average metrics
        avg_roi = sum(calc.roi_percentage for calc in profit_calculations) / len(profit_calculations)
        
        # Calculate return distribution
        roi_values = [float(calc.roi_percentage) for calc in profit_calculations]
        roi_std = np.std(roi_values) if len(roi_values) > 1 else 0
        roi_percentiles = {
            'p25': np.percentile(roi_values, 25),
            'p50': np.percentile(roi_values, 50),
            'p75': np.percentile(roi_values, 75),
            'p95': np.percentile(roi_values, 95)
        }
        
        # Calculate win rate
        profitable_bets = sum(1 for calc in profit_calculations if calc.net_profit > 0)
        win_rate = (profitable_bets / len(profit_calculations)) * Decimal('100')
        
        # Calculate profit factor
        gross_profits = [calc.gross_profit for calc in profit_calculations if calc.gross_profit > 0]
        gross_losses = [-calc.gross_profit for calc in profit_calculations if calc.gross_profit < 0]
        
        total_gross_profits = sum(gross_profits)
        total_gross_losses = sum(gross_losses)
        profit_factor = total_gross_profits / total_gross_losses if total_gross_losses > 0 else float('inf')
        
        # Calculate time-weighted metrics if time periods provided
        annualized_returns = []
        if time_periods:
            stakes = [calc.calculation_metadata.get('total_stake', Decimal('0')) for calc in profit_calculations]
            for calc, period in zip(profit_calculations, time_periods):
                if period.total_seconds() > 0:
                    annual_return = self.calculate_annualized_return(calc.net_profit, calc.calculation_metadata.get('total_stake', Decimal('1')), period)
                    annualized_returns.append(annual_return)
        
        avg_annualized_return = sum(annualized_returns) / len(annualized_returns) if annualized_returns else None
        
        return {
            'summary_metrics': {
                'total_bets': len(profit_calculations),
                'total_gross_profit': float(total_gross_profit),
                'total_net_profit': float(total_net_profit),
                'total_fees': float(total_fees),
                'average_roi': float(avg_roi),
                'win_rate_percentage': float(win_rate),
                'profit_factor': profit_factor
            },
            'distribution_metrics': {
                'roi_std_dev': roi_std,
                'roi_percentiles': roi_percentiles,
                'best_roi': max(roi_values),
                'worst_roi': min(roi_values)
            },
            'time_weighted_metrics': {
                'average_annualized_return': float(avg_annualized_return) if avg_annualized_return else None,
                'annualized_returns_count': len(annualized_returns)
            },
            'risk_metrics': {
                'consecutive_losses': self._calculate_max_consecutive_losses(profit_calculations),
                'largest_single_loss': min([float(calc.net_profit) for calc in profit_calculations]),
                'largest_single_win': max([float(calc.net_profit) for calc in profit_calculations])
            }
        }

    def _calculate_max_consecutive_losses(self, calculations: List[ProfitCalculation]) -> int:
        """Calculate maximum consecutive losses in the sequence."""
        if not calculations:
            return 0
        
        max_consecutive = 0
        current_consecutive = 0
        
        for calc in calculations:
            if calc.net_profit < 0:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
        
        return max_consecutive

    def add_exchange_rate(self, exchange_rate: ExchangeRate):
        """Add an exchange rate to the cache."""
        self._exchange_rates[f"{exchange_rate.from_currency}_{exchange_rate.to_currency}"] = exchange_rate

    def get_exchange_rate(self, from_currency: str, to_currency: str) -> Optional[ExchangeRate]:
        """Get exchange rate from cache."""
        key = f"{from_currency}_{to_currency}"
        reverse_key = f"{to_currency}_{from_currency}"
        
        if key in self._exchange_rates:
            return self._exchange_rates[key]
        elif reverse_key in self._exchange_rates:
            rate = self._exchange_rates[reverse_key]
            # Return inverse rate
            return ExchangeRate(
                from_currency=from_currency,
                to_currency=to_currency,
                rate=Decimal('1') / rate.rate,
                timestamp=rate.timestamp,
                source=rate.source,
                confidence_level=rate.confidence_level
            )
        else:
            return None

    def calculate_fee_impact_analysis(
        self,
        base_profit: Decimal,
        fee_structures: List[CommissionStructure],
        stake_amounts: List[Decimal]
    ) -> Dict[str, Any]:
        """
        Analyze the impact of different fee structures on profitability.
        
        Args:
            base_profit: Base profit without fees
            fee_structures: List of fee structures to analyze
            stake_amounts: List of stake amounts to test
            
        Returns:
            Analysis results
        """
        analysis_results = {}
        
        for fee_structure in fee_structures:
            structure_name = fee_structure.platform_name
            
            impact_analysis = {
                'fee_structure': structure_name,
                'impact_by_stake': []
            }
            
            for stake in stake_amounts:
                # Calculate commission impact
                commission_impact = stake * fee_structure.commission_type.percentage_rate or Decimal('0')
                
                # Calculate withdrawal fee impact (one-time)
                withdrawal_fee_impact = fee_structure.withdrawal_fees.fixed_amount or Decimal('0')
                
                # Calculate total fee impact
                total_fee_impact = commission_impact + withdrawal_fee_impact
                
                # Calculate impact percentage
                impact_percentage = (total_fee_impact / base_profit * Decimal('100')) if base_profit > 0 else Decimal('0')
                
                impact_analysis['impact_by_stake'].append({
                    'stake_amount': float(stake),
                    'commission_impact': float(commission_impact),
                    'withdrawal_fee_impact': float(withdrawal_fee_impact),
                    'total_fee_impact': float(total_fee_impact),
                    'impact_percentage': float(impact_percentage)
                })
            
            analysis_results[structure_name] = impact_analysis
        
        return analysis_results


def create_profit_calculator(base_currency: str = 'USD') -> AdvancedProfitCalculator:
    """
    Factory function to create and configure a profit calculator.
    
    Args:
        base_currency: Base currency for calculations
        
    Returns:
        Configured AdvancedProfitCalculator instance
    """
    return AdvancedProfitCalculator(base_currency=base_currency)