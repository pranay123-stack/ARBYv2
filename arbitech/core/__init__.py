"""
ARBitech Core Module

This module contains the core functionality for the ARBitech framework.
"""

__version__ = "1.0.0"

from .config_manager import (
    ConfigManager,
    ConfigError,
    init_config,
    get_config_manager,
    get_config,
    set_config,
    reload_config
)

__all__ = [
    "ConfigManager",
    "ConfigError",
    "init_config",
    "get_config_manager",
    "get_config",
    "set_config",
    "reload_config"
]