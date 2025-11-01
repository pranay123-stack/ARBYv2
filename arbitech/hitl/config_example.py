"""
Configuration Example for HITL Result Logger

This file demonstrates how to configure the comprehensive trade result logging system
for different deployment scenarios including development, testing, and production.
"""

# HITL Result Logger Configuration
HITL_RESULT_LOGGER_CONFIG = {
    # Core logging settings
    'logs_directory': '/workspace/arbitech/logs',
    'hitl_directory': '/workspace/arbitech/logs/hitl',
    
    # Real-time features
    'enable_real_time_dashboards': True,
    'dashboard_update_interval': 5,  # seconds
    
    # Analytics settings
    'enable_user_behavior_analysis': True,
    'enable_performance_prediction': True,
    'enable_pattern_detection': True,
    'enable_anomaly_detection': True,
    
    # Data retention and performance
    'retention_days': 90,
    'max_cache_size': 10000,
    'batch_size': 100,
    
    # Export and reporting
    'enable_export_capabilities': True,
    'export_formats': ['json', 'csv', 'xlsx'],
    'enable_compression': True,
    
    # Security and compliance
    'enable_audit_trail': True,
    'enable_data_encryption': False,  # Set to True in production
    'redact_sensitive_data': True,
    
    # Formatting and logging
    'json_pretty_print': False,  # Set to True for development
    'enable_structured_logging': True,
    
    # Integration settings
    'enable_risk_integration': True,
    'enable_execution_integration': True,
    'enable_audit_integration': True,
    
    # Alerting and monitoring
    'enable_alerting': True,
    'alert_thresholds': {
        'decision_timeout_rate': 0.1,  # 10%
        'trade_failure_rate': 0.05,    # 5%
        'profit_loss_threshold': 1000, # $1000
        'decision_time_threshold': 30   # 30 seconds
    },
    
    # Performance thresholds
    'performance_thresholds': {
        'max_decision_time_ms': 60000,    # 1 minute
        'max_execution_time_ms': 300000,  # 5 minutes
        'min_success_rate': 0.7,          # 70%
        'max_risk_level': 0.8             # 80%
    },
    
    # Dashboard settings
    'dashboard': {
        'refresh_interval': 5,  # seconds
        'max_data_points': 1000,
        'enable_websocket': False,  # For real-time updates
        'chart_types': ['line', 'bar', 'pie', 'heatmap']
    },
    
    # Export settings
    'export': {
        'default_format': 'json',
        'include_metadata': True,
        'compress_exports': True,
        'max_export_size_mb': 100
    }
}

# Environment-specific configurations
DEVELOPMENT_CONFIG = {
    **HITL_RESULT_LOGGER_CONFIG,
    'json_pretty_print': True,
    'enable_debug_logging': True,
    'retention_days': 7,
    'dashboard_update_interval': 2
}

TESTING_CONFIG = {
    **HITL_RESULT_LOGGER_CONFIG,
    'enable_real_time_dashboards': False,
    'enable_user_behavior_analysis': False,
    'enable_export_capabilities': False,
    'retention_days': 1,
    'dashboard_update_interval': 10
}

PRODUCTION_CONFIG = {
    **HITL_RESULT_LOGGER_CONFIG,
    'enable_data_encryption': True,
    'enable_audit_trail': True,
    'retention_days': 365,
    'enable_compression': True,
    'dashboard_update_interval': 5,
    'max_cache_size': 50000
}

# Risk integration configuration
RISK_INTEGRATION_CONFIG = {
    'risk_analyzer_endpoint': 'http://localhost:8000/risk/analyze',
    'enable_risk_alerts': True,
    'risk_threshold_levels': {
        'low': 0.3,
        'medium': 0.6,
        'high': 0.8,
        'critical': 0.95
    },
    'alert_escalation': {
        'low': 'log_only',
        'medium': 'log_and_notify',
        'high': 'log_notify_and_halt',
        'critical': 'emergency_stop'
    }
}

# Execution tracking integration configuration
EXECUTION_INTEGRATION_CONFIG = {
    'execution_tracker_endpoint': 'http://localhost:8001/execution/track',
    'enable_detailed_tracking': True,
    'track_performance_metrics': True,
    'enable_result_correlation': True,
    'tracking_levels': {
        'basic': 'execution_outcomes',
        'detailed': 'execution_outcomes_timing',
        'comprehensive': 'all_metrics_and_context',
        'verbose': 'everything_with_debug_info'
    }
}

# Audit integration configuration
AUDIT_INTEGRATION_CONFIG = {
    'audit_logger_endpoint': 'http://localhost:8002/audit/log',
    'enable_audit_correlation': True,
    'audit_levels': {
        'trade_decisions': 'all_decisions',
        'execution_results': 'all_results',
        'system_events': 'critical_only',
        'user_actions': 'all_actions'
    },
    'compliance_settings': {
        'gdpr_compliance': True,
        'sox_compliance': True,
        'data_retention_policy': 'strict',
        'anonymization_required': False
    }
}

# Dashboard configuration
DASHBOARD_CONFIG = {
    'default_dashboard': 'performance_overview',
    'available_dashboards': [
        'performance_overview',
        'user_behavior',
        'risk_analysis',
        'execution_tracking',
        'audit_trail',
        'real_time_alerts',
        'compliance_report'
    ],
    'dashboard_permissions': {
        'trader': ['performance_overview', 'user_behavior'],
        'manager': ['performance_overview', 'risk_analysis', 'execution_tracking'],
        'admin': ['all_dashboards'],
        'compliance': ['audit_trail', 'compliance_report']
    },
    'real_time_features': {
        'enable_websocket_updates': True,
        'update_frequency': 1,  # seconds
        'max_concurrent_users': 100
    }
}

# Performance monitoring configuration
PERFORMANCE_CONFIG = {
    'metrics_collection': {
        'decision_metrics': True,
        'execution_metrics': True,
        'system_metrics': True,
        'user_behavior_metrics': True
    },
    'aggregation_intervals': {
        'real_time': 1,      # seconds
        'hourly': 3600,      # seconds
        'daily': 86400,      # seconds
        'weekly': 604800,    # seconds
        'monthly': 2592000   # seconds
    },
    'alert_conditions': {
        'high_latency': 5000,      # 5 seconds
        'low_success_rate': 0.8,   # 80%
        'high_error_rate': 0.05,   # 5%
        'memory_usage': 0.8,       # 80%
        'cpu_usage': 0.8           # 80%
    }
}

# Data export configuration
EXPORT_CONFIG = {
    'supported_formats': ['json', 'csv', 'xlsx', 'pdf'],
    'default_settings': {
        'json': {'indent': 2, 'ensure_ascii': False},
        'csv': {'delimiter': ',', 'quotechar': '"'},
        'xlsx': {'sheet_name': 'export_data'},
        'pdf': {'orientation': 'landscape', 'format': 'A4'}
    },
    'batch_processing': {
        'max_records_per_batch': 10000,
        'compression_enabled': True,
        'parallel_processing': True
    },
    'scheduled_exports': {
        'daily_summary': {'time': '00:00', 'format': 'pdf'},
        'weekly_report': {'day': 'monday', 'time': '09:00', 'format': 'xlsx'},
        'monthly_compliance': {'day': 1, 'time': '08:00', 'format': 'pdf'}
    }
}

# Security configuration
SECURITY_CONFIG = {
    'data_protection': {
        'encrypt_at_rest': False,
        'encrypt_in_transit': True,
        'key_rotation_days': 90,
        'access_logging': True
    },
    'access_control': {
        'role_based_access': True,
        'session_timeout_minutes': 480,
        'max_concurrent_sessions': 3,
        'require_mfa': False
    },
    'compliance': {
        'gdpr_compliance': True,
        'ccpa_compliance': True,
        'audit_retention_years': 7,
        'data_anonymization': False
    }
}

# Database configuration (if using database storage)
DATABASE_CONFIG = {
    'primary_storage': 'file',  # 'file' or 'database'
    'database_settings': {
        'engine': 'postgresql',
        'host': 'localhost',
        'port': 5432,
        'database': 'arbitech_hitl',
        'user': 'hitl_user',
        'password': '${DATABASE_PASSWORD}',
        'pool_size': 10,
        'max_overflow': 20
    },
    'table_settings': {
        'decisions_table': 'hitl_decisions',
        'results_table': 'hitl_results',
        'metrics_table': 'hitl_metrics',
        'patterns_table': 'hitl_patterns'
    },
    'indexing': {
        'timestamp_index': True,
        'user_id_index': True,
        'opportunity_id_index': True,
        'composite_indexes': True
    }
}

# Example usage function
def get_hitl_config(environment: str = 'development') -> dict:
    """Get configuration for specific environment."""
    configs = {
        'development': DEVELOPMENT_CONFIG,
        'testing': TESTING_CONFIG,
        'production': PRODUCTION_CONFIG
    }
    
    base_config = configs.get(environment, DEVELOPMENT_CONFIG)
    
    # Add integration configs
    base_config['risk_integration'] = RISK_INTEGRATION_CONFIG
    base_config['execution_integration'] = EXECUTION_INTEGRATION_CONFIG
    base_config['audit_integration'] = AUDIT_INTEGRATION_CONFIG
    base_config['dashboard'] = DASHBOARD_CONFIG
    base_config['performance'] = PERFORMANCE_CONFIG
    base_config['export'] = EXPORT_CONFIG
    base_config['security'] = SECURITY_CONFIG
    base_config['database'] = DATABASE_CONFIG
    
    return base_config

# Configuration validation
def validate_config(config: dict) -> tuple[bool, list[str]]:
    """Validate configuration settings."""
    errors = []
    
    required_keys = [
        'logs_directory', 'hitl_directory', 'retention_days', 
        'enable_real_time_dashboards', 'enable_export_capabilities'
    ]
    
    for key in required_keys:
        if key not in config:
            errors.append(f"Missing required configuration key: {key}")
    
    # Validate numeric values
    if config.get('retention_days', 0) <= 0:
        errors.append("retention_days must be positive")
    
    if config.get('dashboard_update_interval', 0) <= 0:
        errors.append("dashboard_update_interval must be positive")
    
    # Validate paths
    import os
    logs_dir = config.get('logs_directory', '')
    if logs_dir and not os.path.exists(logs_dir):
        try:
            os.makedirs(logs_dir, exist_ok=True)
        except Exception as e:
            errors.append(f"Cannot create logs directory: {e}")
    
    return len(errors) == 0, errors


if __name__ == "__main__":
    # Example usage
    print("🔧 HITL Result Logger Configuration Examples")
    print("=" * 50)
    
    # Show different environment configs
    for env in ['development', 'testing', 'production']:
        config = get_hitl_config(env)
        is_valid, errors = validate_config(config)
        
        print(f"\n📋 {env.upper()} Configuration:")
        print(f"  Valid: {is_valid}")
        if errors:
            print(f"  Errors: {errors}")
        else:
            print(f"  Dashboard: {config['enable_real_time_dashboards']}")
            print(f"  Export: {config['enable_export_capabilities']}")
            print(f"  Retention: {config['retention_days']} days")
    
    print("\n✅ Configuration examples completed!")