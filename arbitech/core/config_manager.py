"""
Configuration Management System for Arbitech

This module provides a comprehensive configuration management system with YAML-based
configuration loading, environment variable overrides, validation, and hot-reload capabilities.
"""

import os
import yaml
import logging
from typing import Any, Dict, Optional, List, Callable
from pathlib import Path
from threading import Lock
from datetime import datetime
import json


class ConfigError(Exception):
    """Custom exception for configuration-related errors"""
    pass


class ConfigManager:
    """
    Main configuration manager class that handles YAML configuration loading,
    environment variable overrides, validation, and hot-reload functionality.
    """
    
    def __init__(self, config_path: str = None, watch_for_changes: bool = True):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Path to the configuration file. If None, uses default location.
            watch_for_changes: Whether to enable file watching for hot-reload.
        """
        self.config_path = config_path or self._get_default_config_path()
        self._config: Dict[str, Any] = {}
        self._watch_for_changes = watch_for_changes
        self._file_watcher = None
        self._lock = Lock()
        self._callbacks: List[Callable] = []
        self._last_modified = None
        self.logger = logging.getLogger(__name__)
        
        # Load configuration on initialization
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get the default configuration file path."""
        return os.path.join(os.path.dirname(__file__), "..", "..", "config", "config.yaml")
    
    def _load_config(self) -> None:
        """Load configuration from YAML file and apply environment overrides."""
        try:
            # Load YAML configuration
            config_file = Path(self.config_path)
            
            if not config_file.exists():
                raise ConfigError(f"Configuration file not found: {self.config_path}")
            
            with open(config_file, 'r') as f:
                raw_config = yaml.safe_load(f)
            
            # Store file modification time
            self._last_modified = config_file.stat().st_mtime
            
            # Apply environment variable overrides
            self._config = self._apply_env_overrides(raw_config)
            
            # Validate configuration
            self._validate_config()
            
            self.logger.info(f"Configuration loaded successfully from {self.config_path}")
            
        except Exception as e:
            raise ConfigError(f"Failed to load configuration: {str(e)}")
    
    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply environment variable overrides to configuration.
        Environment variables should be prefixed with ARBITECH_ and use double underscores
        to denote nested keys (e.g., ARBITECH_SYSTEM__MAX_CONCURRENT_SCANS).
        """
        # Flatten config for easier processing
        flat_config = self._flatten_config(config)
        
        # Apply environment variable overrides
        for env_key, env_value in os.environ.items():
            if env_key.startswith('ARBITECH_'):
                # Remove prefix and convert to nested key
                config_key = env_key[9:]  # Remove 'ARBITECH_' prefix
                nested_key = config_key.replace('__', '.')
                
                # Parse the environment value
                parsed_value = self._parse_env_value(env_value)
                
                # Set the value in flat config
                flat_config[nested_key] = parsed_value
        
        # Reconstruct nested config
        return self._expand_config(flat_config)
    
    def _flatten_config(self, config: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, str]:
        """
        Flatten a nested dictionary into a single-level dictionary with dot-separated keys.
        """
        items = []
        for k, v in config.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_config(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    def _expand_config(self, flat_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Expand a flat dictionary back into a nested dictionary structure.
        """
        result = {}
        for key, value in flat_config.items():
            keys = key.split('.')
            current = result
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            current[keys[-1]] = value
        return result
    
    def _parse_env_value(self, value: str) -> Any:
        """
        Parse environment variable value into appropriate Python type.
        Supports JSON format for complex types.
        """
        # Try JSON parsing first
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            pass
        
        # Handle common string formats
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        elif value.lower() in ('none', 'null'):
            return None
        else:
            try:
                # Try to convert to int
                return int(value)
            except ValueError:
                try:
                    # Try to convert to float
                    return float(value)
                except ValueError:
                    # Return as string
                    return value
    
    def _validate_config(self) -> None:
        """
        Validate the loaded configuration against expected structure and types.
        Raises ConfigError if validation fails.
        """
        required_sections = [
            'user.risk',
            'system',
            'bookmakers',
            'notifications',
            'logging'
        ]
        
        # Check required sections exist
        for section in required_sections:
            if not self._get_nested_value(section):
                raise ConfigError(f"Missing required configuration section: {section}")
        
        # Validate user risk configuration
        self._validate_risk_config()
        
        # Validate system configuration
        self._validate_system_config()
        
        # Validate bookmaker configurations
        self._validate_bookmaker_config()
        
        # Validate notification configuration
        self._validate_notification_config()
        
        # Validate logging configuration
        self._validate_logging_config()
    
    def _validate_risk_config(self) -> None:
        """Validate user risk configuration."""
        risk_config = self._config.get('user', {}).get('risk', {})
        
        # Validate max_stake
        max_stake = risk_config.get('max_stake')
        if max_stake is not None and (not isinstance(max_stake, (int, float)) or max_stake <= 0):
            raise ConfigError("user.risk.max_stake must be a positive number")
        
        # Validate risk_percentage
        risk_pct = risk_config.get('risk_percentage')
        if risk_pct is not None:
            if not isinstance(risk_pct, (int, float)) or risk_pct < 0 or risk_pct > 100:
                raise ConfigError("user.risk.risk_percentage must be a number between 0 and 100")
        
        # Validate min_odds and max_odds
        min_odds = risk_config.get('min_odds')
        max_odds = risk_config.get('max_odds')
        if min_odds and max_odds and min_odds >= max_odds:
            raise ConfigError("user.risk.min_odds must be less than max_odds")
    
    def _validate_system_config(self) -> None:
        """Validate system configuration."""
        sys_config = self._config.get('system', {})
        
        # Validate scan intervals
        scan_intervals = sys_config.get('scan_intervals', {})
        for interval_name, interval_value in scan_intervals.items():
            if not isinstance(interval_value, (int, float)) or interval_value <= 0:
                raise ConfigError(f"system.scan_intervals.{interval_name} must be a positive number")
        
        # Validate max_concurrent_scans
        max_scans = sys_config.get('max_concurrent_scans')
        if max_scans is not None and (not isinstance(max_scans, int) or max_scans <= 0):
            raise ConfigError("system.max_concurrent_scans must be a positive integer")
    
    def _validate_bookmaker_config(self) -> None:
        """Validate bookmaker configurations."""
        bookmakers = self._config.get('bookmakers', {})
        for bookmaker_name, bookmaker_config in bookmakers.items():
            if not isinstance(bookmaker_config, dict):
                raise ConfigError(f"bookmakers.{bookmaker_name} must be a dictionary")
            
            # Check for required fields
            if not bookmaker_config.get('enabled', True):
                continue
            
            # Validate API credentials
            if 'api_key' not in bookmaker_config and 'username' not in bookmaker_config:
                raise ConfigError(f"bookmakers.{bookmaker_name} must have either api_key or username")
    
    def _validate_notification_config(self) -> None:
        """Validate notification configuration."""
        notifications = self._config.get('notifications', {})
        
        # Validate email settings if enabled
        email_enabled = notifications.get('email', {}).get('enabled', False)
        if email_enabled:
            email_config = notifications.get('email', {})
            if not email_config.get('smtp_server'):
                raise ConfigError("notifications.email.smtp_server is required when email is enabled")
        
        # Validate webhook URLs
        webhooks = notifications.get('webhooks', {})
        for webhook_name, webhook_config in webhooks.items():
            if webhook_config.get('enabled', False):
                webhook_url = webhook_config.get('url')
                if not webhook_url or not webhook_url.startswith(('http://', 'https://')):
                    raise ConfigError(f"notifications.webhooks.{webhook_name}.url must be a valid HTTP URL")
    
    def _validate_logging_config(self) -> None:
        """Validate logging configuration."""
        logging_config = self._config.get('logging', {})
        
        # Validate log level
        log_level = logging_config.get('level', 'INFO')
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if log_level.upper() not in valid_levels:
            raise ConfigError(f"logging.level must be one of: {', '.join(valid_levels)}")
    
    def _get_nested_value(self, path: str) -> Any:
        """
        Get a value from the configuration using dot notation.
        
        Args:
            path: Dot-separated path to the configuration value (e.g., 'user.risk.max_stake')
            
        Returns:
            The value at the specified path, or None if not found.
        """
        keys = path.split('.')
        current = self._config
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current
    
    def get(self, path: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.
        
        Args:
            path: Dot-separated path to the configuration value.
            default: Default value to return if path is not found.
            
        Returns:
            The configuration value or default.
        """
        with self._lock:
            value = self._get_nested_value(path)
            return value if value is not None else default
    
    def set(self, path: str, value: Any) -> None:
        """
        Set a configuration value using dot notation.
        
        Args:
            path: Dot-separated path to the configuration value.
            value: Value to set.
        """
        with self._lock:
            keys = path.split('.')
            current = self._config
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            current[keys[-1]] = value
    
    def reload(self) -> None:
        """Reload configuration from file."""
        with self._lock:
            old_config = self._config.copy()
            self._load_config()
            
            # Notify callbacks about configuration changes
            if self._callbacks:
                self._notify_callbacks(old_config, self._config)
    
    def _notify_callbacks(self, old_config: Dict[str, Any], new_config: Dict[str, Any]) -> None:
        """Notify registered callbacks about configuration changes."""
        for callback in self._callbacks:
            try:
                callback(old_config, new_config)
            except Exception as e:
                self.logger.error(f"Configuration callback error: {str(e)}")
    
    def register_callback(self, callback: Callable[[Dict[str, Any], Dict[str, Any]], None]) -> None:
        """
        Register a callback function to be called when configuration is reloaded.
        
        Args:
            callback: Function that takes old_config and new_config as arguments.
        """
        with self._lock:
            if callback not in self._callbacks:
                self._callbacks.append(callback)
    
    def unregister_callback(self, callback: Callable) -> None:
        """Unregister a previously registered callback."""
        with self._lock:
            if callback in self._callbacks:
                self._callbacks.remove(callback)
    
    def get_user_config(self) -> Dict[str, Any]:
        """Get user configuration section."""
        return self.get('user', {})
    
    def get_risk_config(self) -> Dict[str, Any]:
        """Get user risk configuration."""
        return self.get_user_config().get('risk', {})
    
    def get_system_config(self) -> Dict[str, Any]:
        """Get system configuration section."""
        return self.get('system', {})
    
    def get_vlm_config(self) -> Dict[str, Any]:
        """Get VLM (Virtual Live Model) configuration."""
        return self.get_system_config().get('vlm', {})
    
    def get_bookmaker_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get all bookmaker configurations."""
        return self.get('bookmakers', {})
    
    def get_bookmaker_config(self, bookmaker_name: str) -> Dict[str, Any]:
        """Get configuration for a specific bookmaker."""
        return self.get_bookmaker_configs().get(bookmaker_name, {})
    
    def get_notification_config(self) -> Dict[str, Any]:
        """Get notification configuration."""
        return self.get('notifications', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return self.get('logging', {})
    
    def get_active_bookmakers(self) -> List[str]:
        """Get list of active (enabled) bookmaker names."""
        active_bookmakers = []
        for name, config in self.get_bookmaker_configs().items():
            if config.get('enabled', True):  # Default to enabled if not specified
                active_bookmakers.append(name)
        return active_bookmakers
    
    def is_bookmaker_enabled(self, bookmaker_name: str) -> bool:
        """Check if a bookmaker is enabled."""
        config = self.get_bookmaker_config(bookmaker_name)
        return config.get('enabled', True)
    
    def get_scan_interval(self, interval_name: str) -> float:
        """Get a specific scan interval configuration."""
        intervals = self.get_system_config().get('scan_intervals', {})
        return intervals.get(interval_name, 60.0)  # Default to 60 seconds
    
    def get_max_concurrent_scans(self) -> int:
        """Get maximum number of concurrent scans."""
        return self.get_system_config().get('max_concurrent_scans', 10)
    
    def get_risk_limits(self) -> Dict[str, Any]:
        """Get user risk limits configuration."""
        return self.get_risk_config()
    
    def get_notification_channels(self) -> Dict[str, Any]:
        """Get notification channels configuration."""
        return self.get_notification_config()
    
    def configure_logging(self) -> None:
        """Configure Python logging based on configuration."""
        logging_config = self.get_logging_config()
        
        # Set log level
        level = logging_config.get('level', 'INFO').upper()
        numeric_level = getattr(logging, level, logging.INFO)
        
        # Configure root logger
        logging.basicConfig(
            level=numeric_level,
            format=logging_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            datefmt=logging_config.get('date_format', '%Y-%m-%d %H:%M:%S')
        )
        
        # Configure file handler if specified
        log_file = logging_config.get('file')
        if log_file:
            from logging.handlers import RotatingFileHandler
            max_bytes = logging_config.get('max_file_size', 10485760)  # 10MB default
            backup_count = logging_config.get('backup_count', 5)
            
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count
            )
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(logging.Formatter(
                logging_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            ))
            
            logging.getLogger().addHandler(file_handler)
    
    def to_dict(self) -> Dict[str, Any]:
        """Return the entire configuration as a dictionary."""
        with self._lock:
            return self._config.copy()
    
    def save_to_file(self, file_path: str = None) -> None:
        """
        Save current configuration to a YAML file.
        
        Args:
            file_path: Path to save the configuration. Uses default path if None.
        """
        save_path = file_path or self.config_path
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        with open(save_path, 'w') as f:
            yaml.dump(self._config, f, default_flow_style=False, sort_keys=False)
        
        self.logger.info(f"Configuration saved to {save_path}")


# Global configuration manager instance
_config_manager: Optional[ConfigManager] = None
_lock = Lock()


def get_config_manager(config_path: str = None, create_if_none: bool = True) -> ConfigManager:
    """
    Get or create the global configuration manager instance.
    
    Args:
        config_path: Path to configuration file. Only used when creating new instance.
        create_if_none: Whether to create a new instance if none exists.
        
    Returns:
        The global configuration manager instance.
    """
    global _config_manager
    
    with _lock:
        if _config_manager is None and create_if_none:
            _config_manager = ConfigManager(config_path=config_path)
        return _config_manager


def init_config(config_path: str = None, watch_for_changes: bool = True) -> ConfigManager:
    """
    Initialize the global configuration manager.
    
    Args:
        config_path: Path to configuration file.
        watch_for_changes: Whether to enable file watching for hot-reload.
        
    Returns:
        The initialized configuration manager.
    """
    global _config_manager
    
    _config_manager = ConfigManager(config_path=config_path, watch_for_changes=watch_for_changes)
    return _config_manager


def get_config(path: str = None, default: Any = None) -> Any:
    """
    Get a configuration value using dot notation from the global config manager.
    
    Args:
        path: Dot-separated path to the configuration value.
        default: Default value to return if path is not found.
        
    Returns:
        The configuration value or default.
    """
    manager = get_config_manager()
    if manager is None:
        raise ConfigError("Configuration manager not initialized. Call init_config() first.")
    
    if path is None:
        return manager.to_dict()
    return manager.get(path, default)


def set_config(path: str, value: Any) -> None:
    """
    Set a configuration value using dot notation in the global config manager.
    
    Args:
        path: Dot-separated path to the configuration value.
        value: Value to set.
    """
    manager = get_config_manager()
    if manager is None:
        raise ConfigError("Configuration manager not initialized. Call init_config() first.")
    
    manager.set(path, value)


def reload_config() -> None:
    """Reload configuration from file using the global config manager."""
    manager = get_config_manager()
    if manager is None:
        raise ConfigError("Configuration manager not initialized. Call init_config() first.")
    
    manager.reload()


def get_user_config() -> Dict[str, Any]:
    """Get user configuration from the global config manager."""
    return get_config('user', {})


def get_system_config() -> Dict[str, Any]:
    """Get system configuration from the global config manager."""
    return get_config('system', {})


def get_bookmaker_configs() -> Dict[str, Dict[str, Any]]:
    """Get bookmaker configurations from the global config manager."""
    return get_config('bookmakers', {})


def get_notification_config() -> Dict[str, Any]:
    """Get notification configuration from the global config manager."""
    return get_config('notifications', {})


def get_logging_config() -> Dict[str, Any]:
    """Get logging configuration from the global config manager."""
    return get_config('logging', {})


# Convenience functions for common configuration access
def get_risk_limits() -> Dict[str, Any]:
    """Get user risk limits configuration."""
    return get_user_config().get('risk', {})


def get_scan_intervals() -> Dict[str, float]:
    """Get scan intervals configuration."""
    return get_system_config().get('scan_intervals', {})


def get_active_bookmakers() -> List[str]:
    """Get list of active bookmaker names."""
    manager = get_config_manager()
    if manager:
        return manager.get_active_bookmakers()
    return []


def is_bookmaker_enabled(bookmaker_name: str) -> bool:
    """Check if a bookmaker is enabled."""
    manager = get_config_manager()
    if manager:
        return manager.is_bookmaker_enabled(bookmaker_name)
    return False


# For backwards compatibility
__all__ = [
    'ConfigManager',
    'ConfigError',
    'get_config_manager',
    'init_config',
    'get_config',
    'set_config',
    'reload_config',
    'get_user_config',
    'get_system_config',
    'get_bookmaker_configs',
    'get_notification_config',
    'get_logging_config',
    'get_risk_limits',
    'get_scan_intervals',
    'get_active_bookmakers',
    'is_bookmaker_enabled',
]
