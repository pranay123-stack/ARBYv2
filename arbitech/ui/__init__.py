"""
ARBitech UI Module

Comprehensive dashboard UI system for the ARBitech arbitrage trading platform.
Provides real-time monitoring, control, and analytics through a modern web interface.

Main Components:
- DashboardUI: Main dashboard controller and web server
- Real-time WebSocket integration for live updates
- Interactive charts and data visualizations
- User management and preference settings
- System health monitoring
- Performance analytics

Usage:
    from ui.dashboard import DashboardUI
    import asyncio
    
    async def start_dashboard():
        dashboard = DashboardUI(port=8080, host="0.0.0.0")
        await dashboard.start()
    
    asyncio.run(start_dashboard())

Author: ARBitech Development Team
Version: 1.0.0
"""

from .dashboard import DashboardUI, UserSession, DashboardStats
from .dashboard import DashboardHTTPHandler

__version__ = "1.0.0"
__author__ = "ARBitech Development Team"

__all__ = [
    "DashboardUI",
    "UserSession", 
    "DashboardStats",
    "DashboardHTTPHandler"
]