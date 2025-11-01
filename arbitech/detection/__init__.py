"""
ARBitech Detection Module

This module contains detection functionality for the ARBitech framework.
Includes intelligent opportunity ranking, filtering, quality assessment systems,
comprehensive opportunity scanner using VLM infrastructure, and multi-bookmaker
data aggregation system.
"""

__version__ = "1.0.0"

# Import Multi-Bookmaker Data Aggregation Components
from .bookmaker_manager import (
    BookmakerManager,
    get_bookmaker_manager,
    shutdown_bookmaker_manager,
    BookmakerStatus,
    DataSourceType,
    PriorityLevel,
    HealthMetrics,
    DataSource,
    BookmakerIntegration,
    BookmakerAPIInterface,
    RESTAPIClient,
    VLMExtractionClient,
    create_api_client
)

from .data_aggregator import (
    DataAggregator,
    get_data_aggregator,
    shutdown_data_aggregator,
    AggregationStrategy,
    DataQualityLevel,
    UpdateFrequency,
    MarketOdds,
    MarketData,
    AggregatedEvent,
    AggregationStats,
    OddsNormalizer,
    DataQualityAssessor
)

from .data_synchronizer import (
    DataSynchronizer,
    get_data_synchronizer,
    shutdown_data_synchronizer,
    SyncStatus,
    ConflictResolutionStrategy,
    SyncEventType,
    SyncEvent,
    DataChange,
    SyncState,
    ConflictDetector,
    ConflictResolver,
    StreamProcessor
)

from .market_data_store import (
    MarketDataStore,
    get_market_data_store,
    shutdown_market_data_store,
    StorageType,
    CompressionType,
    CacheStrategy,
    StorageMetrics,
    DataRecord,
    LRUCache,
    TTLCache,
    DataCompressor,
    SQLiteStorage
)

# Import main components
from .opportunity_ranker import (
    OpportunityRanker,
    RankingStrategy,
    RankingWeights,
    OpportunityScore,
    ProfitScoreCalculator,
    RiskScoreCalculator,
    LiquidityScoreCalculator,
    TimeScoreCalculator,
    ExecutionScoreCalculator
)

from .filtering_engine import (
    FilteringEngine,
    ProfitMarginFilter,
    RiskTierFilter,
    SportFilter,
    BookmakerFilter,
    MarketTypeFilter,
    StakeAmountFilter,
    TimeFilter,
    LiquidityFilter,
    CustomFilter,
    FilterRule,
    FilterGroup,
    FilterOperator,
    create_profit_filter,
    create_risk_filter,
    create_sport_filter,
    create_bookmaker_filter,
    create_time_filter,
    create_liquidity_filter
)

from .priority_queue import (
    PriorityQueue,
    OpportunityQueueManager,
    QueueEntry,
    QueueMetrics,
    BatchProcessingResult,
    PriorityStrategy,
    QueueStatus
)

from .quality_scorer import (
    QualityScorer,
    QualityAssessment,
    QualityDimension,
    QualityLevel,
    ReliabilityScore,
    ReliabilityScorer,
    ProfitStabilityScorer,
    ExecutionComplexityScorer,
    MarketConditionsScorer,
    HistoricalPerformanceScorer,
    create_quality_assessment,
    batch_quality_assessment
)

# Import opportunity scanner components
from .opportunity_scanner import (
    OpportunityScanner,
    ScannerEvent,
    ScannerEventType,
    ScanMetrics,
    create_scanner,
    get_scanner_metrics
)

from .scanner_engine import (
    ScannerEngine,
    ScanTask,
    ScanStatus,
    ScanType,
    ScanResult,
    EngineMetrics,
    ScanPriority,
    create_scan_batch,
    get_engine_performance_summary
)

from .market_monitor import (
    MarketMonitor,
    MarketEvent,
    MarketEventType,
    MarketOdds,
    ArbitrageCalculator,
    create_market_monitor,
    get_market_performance_metrics
)

from .scan_scheduler import (
    ScanScheduler,
    ScheduleConfig,
    ScheduleType,
    ScheduleStatus,
    ScanPriority as SchedulerScanPriority,
    ScheduledScan,
    ResourceMonitor,
    create_scheduler,
    create_quick_scan_schedule,
    create_cron_scan_schedule,
    get_scheduler_performance_summary
)

# Import mathematical calculation engines
from .arbitrage_math import (
    AdvancedArbitrageMath,
    ArbitrageOpportunity,
    MarketLeg,
    StakeAllocation,
    ArbitrageStrategy,
    MarketType,
    create_arbitrage_math_engine
)

from .profit_calculator import (
    AdvancedProfitCalculator,
    ProfitCalculation,
    CommissionStructure,
    FeeStructureConfig,
    ExchangeRate,
    TimeValueParameters,
    ProfitType as ProfitCalculationType,
    FeeStructureType as FeeStructureEnum,
    CurrencyType,
    create_profit_calculator
)

from .market_analysis import (
    AdvancedMarketAnalysis,
    MarketDataPoint,
    LiquidityAnalysis,
    MarketEfficiencyAnalysis,
    PriceMovementPrediction,
    MarketMicrostructure,
    MarketEfficiency,
    LiquidityLevel,
    PriceMovementType,
    create_market_analyzer
)

from .mathematical_models import (
    AdvancedMathematicalModels,
    RiskMetrics,
    PerformanceMetrics,
    ExpectedUtilityResult,
    PortfolioOptimizationResult,
    RiskMetric,
    OptimizationObjective,
    create_mathematical_models
)

# Convenience factory function for complete arbitrage engine
def create_complete_arbitrage_engine(
    risk_tolerance: float = 0.1,
    base_currency: str = "USD", 
    risk_free_rate: float = 0.02,
    analysis_window_hours: int = 24
):
    """
    Create a complete arbitrage mathematical analysis engine.
    
    Args:
        risk_tolerance: Risk tolerance for calculations (0.0 to 1.0)
        base_currency: Base currency for profit calculations
        risk_free_rate: Risk-free rate for risk-adjusted calculations
        analysis_window_hours: Time window for market analysis
        
    Returns:
        Dictionary containing all mathematical engine components
    """
    from decimal import Decimal
    from datetime import timedelta
    
    engines = {
        'arbitrage_math': create_arbitrage_math_engine(
            risk_tolerance=Decimal(str(risk_tolerance))
        ),
        'profit_calculator': create_profit_calculator(base_currency=base_currency),
        'market_analysis': create_market_analyzer(
            analysis_window=timedelta(hours=analysis_window_hours)
        ),
        'mathematical_models': create_mathematical_models(
            risk_free_rate=Decimal(str(risk_free_rate))
        )
    }
    
    return engines

# Quick utility functions
def quick_arbitrage_check(odds_list: list, bookmakers: list = None, minimum_margin: float = 0.5) -> dict:
    """
    Quick arbitrage opportunity check for a list of odds.
    
    Args:
        odds_list: List of decimal odds
        bookmakers: Optional list of bookmaker names  
        minimum_margin: Minimum profit margin required
        
    Returns:
        Dictionary with arbitrage analysis results
    """
    import sys
    sys.path.append('/workspace/arbitech/utils')
    try:
        from math_helpers import calculate_profit_margin
        profit_margin = calculate_profit_margin(odds_list)
        is_arbitrage = profit_margin > minimum_margin
        
        return {
            'is_arbitrage': is_arbitrage,
            'profit_margin': profit_margin,
            'total_implied_probability': sum([1/odds for odds in odds_list]),
            'message': 'Arbitrage opportunity found' if is_arbitrage else 'No arbitrage opportunity'
        }
    except Exception as e:
        return {'error': str(e), 'is_arbitrage': False}

def calculate_kelly_stakes(
    bankroll: float,
    odds: float, 
    win_probability: float,
    conservative_factor: float = 0.5
) -> dict:
    """
    Calculate Kelly criterion stakes with optional conservative adjustment.
    
    Args:
        bankroll: Available bankroll
        odds: Decimal odds
        win_probability: True probability of winning  
        conservative_factor: Factor to apply to full Kelly
        
    Returns:
        Dictionary with Kelly stake recommendations
    """
    try:
        from decimal import Decimal
        models = create_mathematical_models()
        kelly_result = models.calculate_kelly_criterion(
            odds=Decimal(str(odds)),
            win_probability=Decimal(str(win_probability)), 
            bankroll=Decimal(str(bankroll))
        )
        
        conservative_stake = kelly_result['optimal_stake'] * Decimal(str(conservative_factor))
        
        return {
            'full_kelly_fraction': float(kelly_result['kelly_fraction']),
            'full_kelly_stake': float(kelly_result['optimal_stake']),
            'conservative_stake': float(conservative_stake),
            'expected_growth_rate': float(kelly_result['expected_growth_rate']),
            'edge': float(kelly_result['edge'])
        }
    except Exception as e:
        return {'error': str(e)}

# Update public API
__all__ = [
    # Multi-Bookmaker Data Aggregation
    'BookmakerManager',
    'get_bookmaker_manager',
    'shutdown_bookmaker_manager',
    'BookmakerStatus',
    'DataSourceType',
    'PriorityLevel',
    'HealthMetrics',
    'DataSource',
    'BookmakerIntegration',
    'BookmakerAPIInterface',
    'RESTAPIClient',
    'VLMExtractionClient',
    'create_api_client',
    
    'DataAggregator',
    'get_data_aggregator',
    'shutdown_data_aggregator',
    'AggregationStrategy',
    'DataQualityLevel',
    'UpdateFrequency',
    'MarketOdds',
    'MarketData',
    'AggregatedEvent',
    'AggregationStats',
    'OddsNormalizer',
    'DataQualityAssessor',
    
    'DataSynchronizer',
    'get_data_synchronizer',
    'shutdown_data_synchronizer',
    'SyncStatus',
    'ConflictResolutionStrategy',
    'SyncEventType',
    'SyncEvent',
    'DataChange',
    'SyncState',
    'ConflictDetector',
    'ConflictResolver',
    'StreamProcessor',
    
    'MarketDataStore',
    'get_market_data_store',
    'shutdown_market_data_store',
    'StorageType',
    'CompressionType',
    'CacheStrategy',
    'StorageMetrics',
    'DataRecord',
    'LRUCache',
    'TTLCache',
    'DataCompressor',
    'SQLiteStorage',
    
    # Opportunity Ranking
    'OpportunityRanker',
    'RankingStrategy', 
    'RankingWeights',
    'OpportunityScore',
    'ProfitScoreCalculator',
    'RiskScoreCalculator',
    'LiquidityScoreCalculator',
    'TimeScoreCalculator',
    'ExecutionScoreCalculator',
    
    # Filtering Engine
    'FilteringEngine',
    'ProfitMarginFilter',
    'RiskTierFilter',
    'SportFilter',
    'BookmakerFilter',
    'MarketTypeFilter',
    'StakeAmountFilter',
    'TimeFilter',
    'LiquidityFilter',
    'CustomFilter',
    'FilterRule',
    'FilterGroup',
    'FilterOperator',
    'create_profit_filter',
    'create_risk_filter',
    'create_sport_filter',
    'create_bookmaker_filter',
    'create_time_filter',
    'create_liquidity_filter',
    
    # Priority Queue
    'PriorityQueue',
    'OpportunityQueueManager',
    'QueueEntry',
    'QueueMetrics',
    'BatchProcessingResult',
    'PriorityStrategy',
    'QueueStatus',
    
    # Quality Scoring
    'QualityScorer',
    'QualityAssessment',
    'QualityDimension',
    'QualityLevel',
    'ReliabilityScore',
    'ReliabilityScorer',
    'ProfitStabilityScorer',
    'ExecutionComplexityScorer',
    'MarketConditionsScorer',
    'HistoricalPerformanceScorer',
    'create_quality_assessment',
    'batch_quality_assessment',
    
    # Opportunity Scanner
    'OpportunityScanner',
    'ScannerEvent',
    'ScannerEventType', 
    'ScanMetrics',
    'create_scanner',
    'get_scanner_metrics',
    
    # Scanner Engine
    'ScannerEngine',
    'ScanTask',
    'ScanStatus',
    'ScanType',
    'ScanResult',
    'EngineMetrics',
    'ScanPriority',
    'create_scan_batch',
    'get_engine_performance_summary',
    
    # Market Monitor
    'MarketMonitor',
    'MarketEvent',
    'MarketEventType',
    'MarketOdds',
    'ArbitrageCalculator',
    'create_market_monitor',
    'get_market_performance_metrics',
    
    # Scan Scheduler
    'ScanScheduler',
    'ScheduleConfig',
    'ScheduleType',
    'ScheduleStatus',
    'SchedulerScanPriority',
    'ScheduledScan',
    'ResourceMonitor',
    'create_scheduler',
    'create_quick_scan_schedule',
    'create_cron_scan_schedule',
    'get_scheduler_performance_summary',
    
    # Mathematical Calculation Engines
    'AdvancedArbitrageMath',
    'ArbitrageOpportunity',
    'MarketLeg', 
    'StakeAllocation',
    'ArbitrageStrategy',
    'MarketType',
    'create_arbitrage_math_engine',
    
    'AdvancedProfitCalculator',
    'ProfitCalculation',
    'CommissionStructure',
    'FeeStructureConfig',
    'ExchangeRate',
    'TimeValueParameters',
    'ProfitCalculationType',
    'FeeStructureEnum',
    'CurrencyType',
    'create_profit_calculator',
    
    'AdvancedMarketAnalysis',
    'MarketDataPoint',
    'LiquidityAnalysis',
    'MarketEfficiencyAnalysis',
    'PriceMovementPrediction',
    'MarketMicrostructure',
    'MarketEfficiency',
    'LiquidityLevel',
    'PriceMovementType',
    'create_market_analyzer',
    
    'AdvancedMathematicalModels',
    'RiskMetrics',
    'PerformanceMetrics',
    'ExpectedUtilityResult',
    'PortfolioOptimizationResult',
    'RiskMetric',
    'OptimizationObjective',
    'create_mathematical_models',
    
    # Convenience Functions
    'create_complete_arbitrage_engine',
    'quick_arbitrage_check',
    'calculate_kelly_stakes'
]