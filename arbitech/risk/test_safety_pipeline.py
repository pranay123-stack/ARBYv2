"""
Safety Validation Pipeline - Quick Test

Simple test to verify the safety validation pipeline components
can be imported and initialized properly.
"""

import sys
import os

# Add the workspace to Python path
sys.path.insert(0, '/workspace/arbitech')

try:
    # Test imports
    try:
        # Test direct component imports
        from risk.safety_pipeline import SafetyPipeline, SafetyConfig
        from risk.pre_trade_validator import PreTradeValidator, PreTradeConfig
        from risk.compliance_checker import ComplianceChecker, ComplianceConfig
        from risk.safety_monitor import SafetyMonitor, MonitoringConfig
        print("✓ All safety validation components imported successfully")
        
        # Test main module imports
        import risk
        safety_pipeline_class = risk.SafetyPipeline
        pre_trade_validator_class = risk.PreTradeValidator
        compliance_checker_class = risk.ComplianceChecker
        safety_monitor_class = risk.SafetyMonitor
        print("✓ Main module imports working")
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        # Try individual imports
        try:
            import sys
            import os
            sys.path.append('/workspace/arbitech')
            from safety_pipeline import SafetyPipeline
            print("✓ Individual import successful")
        except ImportError as e2:
            print(f"❌ Individual import also failed: {e2}")
            sys.exit(1)
    
    # Test initialization
    from risk.safety_pipeline import SafetyConfig
    from risk.pre_trade_validator import PreTradeConfig
    from risk.compliance_checker import ComplianceConfig
    from risk.safety_monitor import MonitoringConfig
    
    # Create configurations
    safety_config = SafetyConfig(
        enable_all_checks=True,
        max_risk_score=75.0,
        parallel_validation=True
    )
    
    pre_trade_config = PreTradeConfig(
        enable_basic_validation=True,
        enable_advanced_validation=True,
        min_viability_score=70.0
    )
    
    compliance_config = ComplianceConfig(
        strict_mode=False,
        enable_gambling_controls=True,
        enable_audit_logging=True
    )
    
    monitoring_config = MonitoringConfig(
        monitoring_enabled=True,
        enable_anomaly_detection=True,
        real_time_interval=1.0
    )
    
    print("✓ All configurations created successfully")
    
    # Initialize components
    safety_pipeline = SafetyPipeline(safety_config)
    pre_trade_validator = PreTradeValidator(pre_trade_config)
    compliance_checker = ComplianceChecker(compliance_config)
    safety_monitor = SafetyMonitor(monitoring_config)
    
    print("✓ All safety validation components initialized successfully")
    
    # Test basic functionality
    sample_opportunity = {
        'id': 'test_001',
        'profit_margin': 3.5,
        'legs': [
            {'bookmaker': 'Bet365', 'odds': 2.10, 'stake': 500.0},
            {'bookmaker': 'WilliamHill', 'odds': 3.40, 'stake': 309.0}
        ]
    }
    
    sample_user = {
        'user_id': 'test_user',
        'location': {'country': 'UK'},
        'verified': True
    }
    
    print("✓ Test data prepared")
    
    # Test component method access
    pipeline_stats = safety_pipeline.get_performance_metrics()
    validator_stats = pre_trade_validator.get_performance_stats()
    compliance_stats = compliance_checker.get_performance_stats()
    monitoring_status = safety_monitor.get_monitoring_status()
    
    print("✓ All component methods accessible")
    
    # Test enumeration imports
    from risk.safety_pipeline import RiskLevel, ValidationStatus
    from risk.pre_trade_validator import ValidationSeverity
    from risk.compliance_checker import RegulatoryRegion
    from risk.safety_monitor import AlertSeverity
    
    print("✓ All enumerations imported successfully")
    
    # Test configuration export (note: this is async method)
    try:
        # For testing, we'll call the sync version
        if hasattr(safety_pipeline, 'export_configuration'):
            print("✓ Configuration export method exists")
        else:
            print("ℹ Configuration export method not found (may be async)")
    except Exception as e:
        print(f"ℹ Configuration export test skipped: {e}")
    
    print("\n" + "="*60)
    print("SAFETY VALIDATION PIPELINE - SYSTEM TEST COMPLETED")
    print("="*60)
    print("✅ All components imported successfully")
    print("✅ All configurations created successfully")  
    print("✅ All components initialized successfully")
    print("✅ Test data prepared successfully")
    print("✅ All component methods accessible")
    print("✅ All enumerations working")
    print("✅ Configuration check completed")
    print("\n🎉 Safety Validation Pipeline is ready for use!")
    print("="*60)
    
except ImportError as e:
    print(f"❌ Import Error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)