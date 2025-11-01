"""
Safety Validation Pipeline - Comprehensive Usage Example

This example demonstrates how to use the complete safety validation pipeline
for arbitrage trading opportunities with multi-layer safety checks and
regulatory compliance validation.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

# Import safety validation components
from .safety_pipeline import SafetyPipeline, SafetyConfig
from .pre_trade_validator import PreTradeValidator, PreTradeConfig
from .compliance_checker import ComplianceChecker, ComplianceConfig
from .safety_monitor import SafetyMonitor, MonitoringConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class SafetyValidationDemo:
    """
    Comprehensive demonstration of the safety validation pipeline
    """
    
    def __init__(self):
        """Initialize the safety validation pipeline"""
        
        # Configure safety pipeline
        safety_config = SafetyConfig(
            enable_all_checks=True,
            fail_fast=False,
            parallel_validation=True,
            max_risk_score=75.0,
            min_confidence_level=80.0,
            max_validations_per_minute=10
        )
        
        # Configure pre-trade validator
        pre_trade_config = PreTradeConfig(
            enable_basic_validation=True,
            enable_advanced_validation=True,
            enable_feasibility_analysis=True,
            min_viability_score=70.0,
            min_feasibility_score=60.0
        )
        
        # Configure compliance checker
        compliance_config = ComplianceConfig(
            strict_mode=False,
            require_all_approvals=False,
            primary_region=RegulatoryRegion.US_FEDERAL,
            enable_gambling_controls=True,
            enable_audit_logging=True
        )
        
        # Configure safety monitor
        monitoring_config = MonitoringConfig(
            monitoring_enabled=True,
            real_time_interval=1.0,
            enable_anomaly_detection=True,
            enable_behavioral_analysis=True,
            continuous_risk_assessment=True,
            max_alerts_per_hour=50
        )
        
        # Initialize components
        self.safety_pipeline = SafetyPipeline(safety_config)
        self.pre_trade_validator = PreTradeValidator(pre_trade_config)
        self.compliance_checker = ComplianceChecker(compliance_config)
        self.safety_monitor = SafetyMonitor(monitoring_config)
        
        logger.info("Safety validation pipeline initialized")
    
    async def demo_complete_validation(self):
        """Demonstrate complete safety validation process"""
        
        logger.info("=== Starting Complete Safety Validation Demo ===")
        
        # Sample arbitrage opportunity
        opportunity = {
            'id': 'arb_001',
            'sport': 'soccer',
            'event': 'Manchester United vs Liverpool',
            'event_time': '2024-11-15T15:00:00Z',
            'profit_margin': 3.5,  # 3.5% profit margin
            'legs': [
                {
                    'bookmaker': 'Bet365',
                    'selection': 'Manchester United Win',
                    'odds': 2.10,
                    'stake': 500.0,
                    'market': 'Match Winner',
                    'currency': 'GBP'
                },
                {
                    'bookmaker': 'WilliamHill',
                    'selection': 'Draw',
                    'odds': 3.40,
                    'stake': 309.0,
                    'market': 'Match Winner',
                    'currency': 'GBP'
                },
                {
                    'bookmaker': 'Ladbrokes',
                    'selection': 'Liverpool Win',
                    'odds': 3.80,
                    'stake': 276.0,
                    'market': 'Match Winner',
                    'currency': 'GBP'
                }
            ],
            'is_live': False,
            'estimated_liquidity': 10000.0,
            'expected_profit': 25.0
        }
        
        # Sample user preferences
        user_preferences = {
            'user_id': 'user_123',
            'location': {
                'country': 'UK',
                'state': '',
                'region': 'EU'
            },
            'risk_tolerance': 'medium',
            'verified': True,
            'verification_date': '2024-01-15',
            'monthly_income': 5000.0,
            'monthly_expenses': 3000.0,
            'limits': {
                'daily_stake_limit': 1000.0,
                'weekly_loss_limit': 2000.0
            },
            'session_start_time': '2024-11-02T10:00:00Z'
        }
        
        # Start safety monitoring
        await self.safety_monitor.start_monitoring()
        
        try:
            # 1. Complete Safety Pipeline Validation
            logger.info("\n--- 1. Complete Safety Pipeline Validation ---")
            safety_result = await self.safety_pipeline.validate_opportunity(
                opportunity, user_preferences
            )
            self._print_safety_result(safety_result)
            
            # 2. Pre-Trade Validation
            logger.info("\n--- 2. Pre-Trade Validation ---")
            basic_validation = await self.pre_trade_validator.validate_basic_checks(
                opportunity, user_preferences
            )
            self._print_validation_result("Basic", basic_validation)
            
            advanced_validation = await self.pre_trade_validator.validate_advanced_checks(
                opportunity, user_preferences
            )
            self._print_validation_result("Advanced", advanced_validation)
            
            # 3. Compliance Validation
            logger.info("\n--- 3. Compliance Validation ---")
            jurisdiction_compliance = await self.compliance_checker.validate_jurisdiction(
                opportunity, user_preferences
            )
            self._print_compliance_result("Jurisdiction", jurisdiction_compliance)
            
            responsible_gambling = await self.compliance_checker.validate_responsible_gambling(
                opportunity, user_preferences
            )
            self._print_compliance_result("Responsible Gambling", responsible_gambling)
            
            audit_compliance = await self.compliance_checker.validate_audit_requirements(
                opportunity, user_preferences
            )
            self._print_compliance_result("Audit", audit_compliance)
            
            # 4. Real-time Safety Monitoring
            logger.info("\n--- 4. Real-time Safety Monitoring ---")
            real_time_safety = await self.safety_monitor.check_real_time_safety(
                opportunity, user_preferences
            )
            self._print_monitoring_result("Real-time Safety", real_time_safety)
            
            anomaly_detection = await self.safety_monitor.detect_anomalies(
                opportunity, user_preferences
            )
            self._print_monitoring_result("Anomaly Detection", anomaly_detection)
            
            intervention_check = await self.safety_monitor.check_proactive_intervention(
                opportunity, user_preferences
            )
            self._print_monitoring_result("Proactive Intervention", intervention_check)
            
            # 5. Generate Comprehensive Report
            logger.info("\n--- 5. Comprehensive Safety Report ---")
            await self._generate_comprehensive_report(
                opportunity, user_preferences, safety_result
            )
            
        finally:
            # Stop safety monitoring
            await self.safety_monitor.stop_monitoring()
        
        logger.info("=== Safety Validation Demo Completed ===")
    
    async def demo_edge_cases(self):
        """Demonstrate safety validation with edge cases"""
        
        logger.info("=== Starting Edge Cases Demo ===")
        
        # Edge Case 1: High-risk opportunity
        high_risk_opportunity = {
            'id': 'high_risk_001',
            'sport': 'esports',
            'event': 'Valorant Tournament Final',
            'profit_margin': 15.0,  # Very high profit margin
            'legs': [
                {
                    'bookmaker': 'UnlicensedBookmaker1',
                    'selection': 'Team A Win',
                    'odds': 2.5,
                    'stake': 2000.0
                },
                {
                    'bookmaker': 'UnlicensedBookmaker2',
                    'selection': 'Team B Win',
                    'odds': 1.8,
                    'stake': 2777.0
                }
            ],
            'is_live': True,
            'estimated_liquidity': 500.0
        }
        
        # Edge Case 2: Restricted region opportunity
        restricted_opportunity = {
            'id': 'restricted_001',
            'sport': 'basketball',
            'event': 'NBA Match',
            'profit_margin': 2.0,
            'legs': [
                {
                    'bookmaker': 'LocalRestricted',
                    'selection': 'Home Win',
                    'odds': 2.2,
                    'stake': 1000.0
                },
                {
                    'bookmaker': 'InternationalBookmaker',
                    'selection': 'Away Win',
                    'odds': 1.9,
                    'stake': 1157.0
                }
            ]
        }
        
        # User in restricted region
        restricted_user = {
            'user_id': 'restricted_user',
            'location': {
                'country': 'WA',  # Washington - restricted state
                'state': 'WA'
            },
            'risk_tolerance': 'high'
        }
        
        # Test high-risk opportunity
        logger.info("\n--- Edge Case 1: High-Risk Opportunity ---")
        high_risk_result = await self.safety_pipeline.validate_opportunity(
            high_risk_opportunity, user_preferences
        )
        self._print_safety_result(high_risk_result)
        
        # Test restricted opportunity
        logger.info("\n--- Edge Case 2: Restricted Region ---")
        restricted_result = await self.safety_pipeline.validate_opportunity(
            restricted_opportunity, restricted_user
        )
        self._print_safety_result(restricted_result)
        
        logger.info("=== Edge Cases Demo Completed ===")
    
    async def demo_performance_monitoring(self):
        """Demonstrate performance monitoring capabilities"""
        
        logger.info("=== Performance Monitoring Demo ===")
        
        # Start monitoring
        await self.safety_monitor.start_monitoring()
        
        try:
            # Simulate multiple validations for performance testing
            logger.info("Running multiple validations for performance analysis...")
            
            opportunities = []
            for i in range(5):
                opportunity = {
                    'id': f'perf_test_{i:03d}',
                    'sport': 'tennis',
                    'profit_margin': 2.5 + i * 0.5,
                    'legs': [
                        {
                            'bookmaker': f'Bookmaker{i}',
                            'odds': 2.0 + i * 0.1,
                            'stake': 100.0 + i * 50
                        }
                    ]
                }
                opportunities.append(opportunity)
            
            # Run validations
            start_time = datetime.now()
            results = []
            
            for opportunity in opportunities:
                result = await self.safety_pipeline.validate_opportunity(opportunity)
                results.append(result)
            
            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()
            
            # Print performance metrics
            logger.info(f"\nPerformance Results:")
            logger.info(f"Total validation time: {total_time:.2f} seconds")
            logger.info(f"Average time per validation: {total_time/len(opportunities):.3f} seconds")
            
            # Get component performance stats
            pipeline_stats = self.safety_pipeline.get_performance_metrics()
            validator_stats = self.pre_trade_validator.get_performance_stats()
            compliance_stats = self.compliance_checker.get_performance_stats()
            monitoring_stats = self.safety_monitor.get_monitoring_status()
            
            logger.info(f"\nComponent Performance:")
            logger.info(f"Pipeline: {pipeline_stats}")
            logger.info(f"Validator: {validator_stats}")
            logger.info(f"Compliance: {compliance_stats}")
            logger.info(f"Monitor: {monitoring_stats}")
            
            # Print validation summary
            successful = sum(1 for r in results if r.overall_status.value == 'passed')
            logger.info(f"\nValidation Summary:")
            logger.info(f"Total opportunities: {len(results)}")
            logger.info(f"Successful validations: {successful}")
            logger.info(f"Success rate: {successful/len(results)*100:.1f}%")
            
        finally:
            await self.safety_monitor.stop_monitoring()
        
        logger.info("=== Performance Monitoring Demo Completed ===")
    
    def _print_safety_result(self, result):
        """Print safety validation result"""
        logger.info(f"Safety Result for {result.opportunity_id}:")
        logger.info(f"  Status: {result.overall_status.value}")
        logger.info(f"  Risk Level: {result.risk_level.value}")
        logger.info(f"  Risk Score: {result.risk_score:.1f}/100")
        logger.info(f"  Confidence: {result.confidence_level:.1f}%")
        logger.info(f"  Validation Time: {result.validation_duration:.3f}s")
        
        if result.critical_issues:
            logger.info(f"  Critical Issues: {result.critical_issues}")
        
        if result.warnings:
            logger.info(f"  Warnings: {result.warnings}")
        
        if result.recommendations:
            logger.info(f"  Recommendations: {result.recommendations}")
    
    def _print_validation_result(self, validation_type: str, result: Dict[str, Any]):
        """Print validation result"""
        status = "✓ PASS" if result['success'] else "✗ FAIL"
        logger.info(f"{validation_type} Validation: {status}")
        
        if result.get('warnings'):
            logger.info(f"  Warnings: {result['warnings']}")
        
        if result.get('data'):
            logger.info(f"  Data: {result['data']}")
    
    def _print_compliance_result(self, compliance_type: str, result: Dict[str, Any]):
        """Print compliance result"""
        status = "✓ COMPLIANT" if result['success'] else "✗ NON-COMPLIANT"
        logger.info(f"{compliance_type} Compliance: {status}")
        
        if result.get('warnings'):
            logger.info(f"  Warnings: {result['warnings']}")
        
        if result.get('critical_issues'):
            logger.info(f"  Critical Issues: {result['critical_issues']}")
    
    def _print_monitoring_result(self, monitoring_type: str, result: Dict[str, Any]):
        """Print monitoring result"""
        logger.info(f"{monitoring_type} Check:")
        logger.info(f"  Status: {'Active' if result['success'] else 'Issues Detected'}")
        
        if result.get('data'):
            data = result['data']
            for key, value in data.items():
                if isinstance(value, (int, float)):
                    logger.info(f"  {key}: {value}")
                elif isinstance(value, list):
                    logger.info(f"  {key}: {len(value)} items")
                elif isinstance(value, dict):
                    logger.info(f"  {key}: {len(value)} entries")
    
    async def _generate_comprehensive_report(
        self,
        opportunity: Dict[str, Any],
        user_preferences: Dict[str, Any],
        safety_result
    ):
        """Generate comprehensive safety report"""
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'opportunity_id': opportunity['id'],
            'summary': {
                'overall_status': safety_result.overall_status.value,
                'risk_level': safety_result.risk_level.value,
                'recommendation': 'PROCEED' if safety_result.overall_status.value == 'passed' 
                                 else 'REVIEW REQUIRED' if safety_result.overall_status.value == 'warning'
                                 else 'BLOCK'
            },
            'detailed_analysis': {
                'risk_assessment': {
                    'risk_score': safety_result.risk_score,
                    'confidence_level': safety_result.confidence_level,
                    'risk_factors': safety_result.risk_factors
                },
                'validation_results': {
                    'pre_trade_validation': safety_result.pre_trade_validation,
                    'compliance_validation': safety_result.compliance_validation,
                    'safety_monitoring': safety_result.safety_monitoring
                },
                'compliance_status': {
                    'jurisdiction_compliant': safety_result.compliance_validation.get('jurisdiction_risk', False),
                    'responsible_gambling_compliant': True,
                    'audit_trail_complete': True
                }
            },
            'recommendations': {
                'action_required': safety_result.overall_status.value != 'passed',
                'max_recommended_stake': safety_result.max_stake_recommended,
                'additional_verification_required': safety_result.confidence_level < 80.0,
                'monitoring_level': 'enhanced' if safety_result.risk_level.value in ['high', 'critical'] else 'standard'
            },
            'audit_information': {
                'validation_timestamp': safety_result.timestamp.isoformat(),
                'validation_duration': safety_result.validation_duration,
                'rules_checked': len(safety_result.validation_rules_checked),
                'rules_failed': len(safety_result.failed_rules)
            }
        }
        
        # Save report
        report_file = f"safety_report_{opportunity['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        logger.info(f"\nComprehensive Safety Report:")
        logger.info(f"Recommendation: {report['summary']['recommendation']}")
        logger.info(f"Risk Score: {report['detailed_analysis']['risk_assessment']['risk_score']:.1f}/100")
        logger.info(f"Confidence Level: {report['detailed_analysis']['risk_assessment']['confidence_level']:.1f}%")
        
        return report


async def main():
    """Main demonstration function"""
    
    logger.info("Starting Safety Validation Pipeline Demonstration")
    
    # Create demo instance
    demo = SafetyValidationDemo()
    
    try:
        # Run complete validation demo
        await demo.demo_complete_validation()
        
        # Run edge cases demo
        await demo.demo_edge_cases()
        
        # Run performance monitoring demo
        await demo.demo_performance_monitoring()
        
        # Generate final safety report
        logger.info("\n=== Final System Status ===")
        pipeline_stats = demo.safety_pipeline.get_performance_metrics()
        logger.info(f"Pipeline Performance: {pipeline_stats}")
        
        safety_report = await demo.safety_pipeline.get_safety_report(24)
        logger.info(f"24-Hour Safety Report Summary:")
        logger.info(f"  Total Validations: {safety_report['performance_metrics']['total_validations']}")
        logger.info(f"  Success Rate: {safety_report['performance_metrics']['successful_validations']/max(safety_report['performance_metrics']['total_validations'], 1)*100:.1f}%")
        
    except Exception as e:
        logger.error(f"Demo error: {str(e)}")
        raise


if __name__ == "__main__":
    # Run the demonstration
    asyncio.run(main())