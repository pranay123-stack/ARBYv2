"""
Bookmaker Automation Handlers Package

This package contains specialized handlers for different betting platforms:
- Betfair: Exchange trading and market making
- Pinnacle: Asian handicaps and live betting
- BetDex: Cryptocurrency integration
- Average: Regional markets and local payment methods

Each handler provides bookmaker-specific automation with:
- Common interface for consistent operation
- Authentication and session management
- Bookmaker-specific betting markets support
- Error handling and recovery mechanisms
- Logging and monitoring capabilities
- Configuration management
"""

from .handler_base import BaseBookmakerHandler
from .handler_manager import BookmakerHandlerManager

__version__ = "1.0.0"

__all__ = [
    "BaseBookmakerHandler",
    "BookmakerHandlerManager"
]