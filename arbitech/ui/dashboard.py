"""
Comprehensive ARBitech Dashboard UI System

A modern, responsive web-based dashboard providing real-time monitoring and control
for the ARBitech arbitrage trading platform. Features live updates, interactive
visualizations, and comprehensive system management.

Features:
- Real-time WebSocket integration for live updates
- Opportunity viewer with advanced filtering and sorting
- Trade monitoring with execution tracking
- Performance analytics with interactive charts
- System health monitoring with real-time status
- User management and preference settings
- Notification preferences and alert management
- Integration with all ARBITech phases
- Responsive design for desktop and mobile

Author: ARBitech Development Team
Version: 1.0.0
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import websockets
from concurrent.futures import ThreadPoolExecutor

# ARBITech component imports
try:
    from notifications.dashboard_updates import DashboardManager, UpdateType
    from storage.models import ArbitrageOpportunity, Trade, TradeStatus, NotificationType
    from detection.scanner_engine import ScannerEngine
    from automation.trade_coordinator import TradeCoordinator
    from risk.monitoring_system import MonitoringSystem
except ImportError as e:
    logging.warning(f"Some ARBITech components not available: {e}")
    
    # Define fallback enums when ARBITech components are not available
    from enum import Enum
    
    class UpdateType(str, Enum):
        """Fallback UpdateType enum when ARBITech components not available."""
        OPPORTUNITY = "opportunity"
        TRADE = "trade"
        SYSTEM_HEALTH = "system_health"
        PERFORMANCE_METRICS = "performance_metrics"
        USER_PRESENCE = "user_presence"
        NOTIFICATION = "notification"
        PROFIT_CALCULATION = "profit_calculation"
        RISK_ALERT = "risk_alert"
        COLLABORATION = "collaboration"
    
    class TradeStatus(str, Enum):
        """Fallback TradeStatus enum."""
        PENDING = "pending"
        PLACING_BETS = "placing_bets"
        FILLED = "filled"
        EXECUTING = "executing"
        COMPLETED = "completed"
        FAILED = "failed"
    
    # Create mock classes
    class ArbitrageOpportunity:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    class Trade:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    class NotificationType(str, Enum):
        """Fallback NotificationType enum."""
        OPPORTUNITY_ALERT = "opportunity_alert"
        SYSTEM_ERROR = "system_error"
    
    # Mock classes for when components are not available
    class DashboardManager:
        """Mock DashboardManager for when ARBITech components not available."""
        def __init__(self, *args, **kwargs):
            self.ws_port = 8765
        
        async def start(self, host, port):
            pass
        
        async def stop(self):
            pass
        
        def get_stats(self):
            return {"connected_clients": 0}
    
    class ScannerEngine:
        def __init__(self):
            pass
    
    class TradeCoordinator:
        def __init__(self):
            pass
    
    class MonitoringSystem:
        def __init__(self):
            pass

logger = logging.getLogger(__name__)


@dataclass
class UserSession:
    """User session data for dashboard clients."""
    user_id: str
    username: str
    preferences: Dict[str, Any]
    subscriptions: Set[UpdateType]
    last_active: datetime
    collaboration_partners: List[str]
    notification_settings: Dict[str, Any]


@dataclass
class DashboardStats:
    """Real-time dashboard statistics."""
    active_sessions: int
    total_opportunities: int
    active_trades: int
    system_health_score: float
    performance_metrics: Dict[str, float]
    connected_users: List[str]


class DashboardUI:
    """
    Main dashboard UI controller providing web interface and real-time updates.
    
    This class manages the web dashboard interface, handles WebSocket connections,
    and coordinates with ARBITech components for real-time data streaming.
    """
    
    def __init__(self, 
                 dashboard_manager: Optional[DashboardManager] = None,
                 port: int = 8080,
                 host: str = "0.0.0.0"):
        """
        Initialize the dashboard UI system.
        
        Args:
            dashboard_manager: Existing DashboardManager instance for WebSocket handling
            port: Port to serve the web dashboard on
            host: Host interface to bind to
        """
        self.dashboard_manager = dashboard_manager
        self.port = port
        self.host = host
        
        # User session management
        self.sessions: Dict[str, UserSession] = {}
        self.websocket_connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        
        # Dashboard state
        self.is_running = False
        self.server: Optional[HTTPServer] = None
        
        # Performance tracking
        self.stats = DashboardStats(
            active_sessions=0,
            total_opportunities=0,
            active_trades=0,
            system_health_score=100.0,
            performance_metrics={},
            connected_users=[]
        )
        
        # Create web assets
        self._setup_web_assets()
        
        # Initialize ARBITech integration
        self._init_arbittech_components()
        
        logger.info(f"Dashboard UI initialized on {host}:{port}")
    
    def _setup_web_assets(self):
        """Setup static web assets for the dashboard."""
        self.web_dir = Path("/workspace/arbitech/ui/web")
        self.web_dir.mkdir(parents=True, exist_ok=True)
        
        # Create HTML template
        self._create_dashboard_html()
        
        # Create CSS styles
        self._create_dashboard_css()
        
        # Create JavaScript for real-time functionality
        self._create_dashboard_js()
        
        # Create assets directory
        (self.web_dir / "assets").mkdir(exist_ok=True)
        
        logger.info("Web assets created successfully")
    
    def _create_dashboard_html(self):
        """Create the main dashboard HTML template."""
        html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ARBitech Dashboard - Real-Time Trading Monitor</title>
    <link rel="stylesheet" href="/static/dashboard.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/socket.io@4.6.1/dist/socket.io.js"></script>
</head>
<body>
    <!-- Navigation Header -->
    <header class="dashboard-header">
        <div class="header-left">
            <h1><i class="fas fa-chart-line"></i> ARBitech Dashboard</h1>
            <div class="connection-status">
                <span id="connectionIndicator" class="status-indicator disconnected">
                    <i class="fas fa-circle"></i>
                </span>
                <span id="connectionText">Disconnected</span>
            </div>
        </div>
        <div class="header-right">
            <div class="user-info">
                <span id="currentUser">Guest User</span>
                <div class="user-menu">
                    <button class="user-menu-btn"><i class="fas fa-user-circle"></i></button>
                    <div class="user-dropdown">
                        <a href="#" onclick="showUserSettings()"><i class="fas fa-cog"></i> Settings</a>
                        <a href="#" onclick="showPreferences()"><i class="fas fa-bell"></i> Notifications</a>
                        <a href="#" onclick="logout()"><i class="fas fa-sign-out-alt"></i> Logout</a>
                    </div>
                </div>
            </div>
        </div>
    </header>

    <!-- Main Dashboard Container -->
    <div class="dashboard-container">
        <!-- Sidebar Navigation -->
        <nav class="sidebar">
            <div class="nav-section">
                <h3>Trading</h3>
                <ul>
                    <li><a href="#" class="nav-link active" data-view="overview">
                        <i class="fas fa-home"></i> Overview
                    </a></li>
                    <li><a href="#" class="nav-link" data-view="opportunities">
                        <i class="fas fa-search"></i> Opportunities
                    </a></li>
                    <li><a href="#" class="nav-link" data-view="trades">
                        <i class="fas fa-exchange-alt"></i> Active Trades
                    </a></li>
                    <li><a href="#" class="nav-link" data-view="history">
                        <i class="fas fa-history"></i> Trade History
                    </a></li>
                </ul>
            </div>
            <div class="nav-section">
                <h3>Analytics</h3>
                <ul>
                    <li><a href="#" class="nav-link" data-view="performance">
                        <i class="fas fa-chart-bar"></i> Performance
                    </a></li>
                    <li><a href="#" class="nav-link" data-view="profit">
                        <i class="fas fa-dollar-sign"></i> Profit Analysis
                    </a></li>
                    <li><a href="#" class="nav-link" data-view="risk">
                        <i class="fas fa-shield-alt"></i> Risk Management
                    </a></li>
                </ul>
            </div>
            <div class="nav-section">
                <h3>System</h3>
                <ul>
                    <li><a href="#" class="nav-link" data-view="health">
                        <i class="fas fa-heartbeat"></i> System Health
                    </a></li>
                    <li><a href="#" class="nav-link" data-view="monitoring">
                        <i class="fas fa-desktop"></i> Monitoring
                    </a></li>
                    <li><a href="#" class="nav-link" data-view="logs">
                        <i class="fas fa-list"></i> System Logs
                    </a></li>
                </ul>
            </div>
        </nav>

        <!-- Main Content Area -->
        <main class="main-content">
            <!-- Overview Dashboard -->
            <div id="overview" class="content-view active">
                <div class="dashboard-widgets">
                    <!-- Key Metrics Row -->
                    <div class="metrics-row">
                        <div class="metric-card">
                            <div class="metric-icon">
                                <i class="fas fa-search-dollar"></i>
                            </div>
                            <div class="metric-content">
                                <h3 id="totalOpportunities">0</h3>
                                <p>Active Opportunities</p>
                            </div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-icon">
                                <i class="fas fa-exchange-alt"></i>
                            </div>
                            <div class="metric-content">
                                <h3 id="activeTrades">0</h3>
                                <p>Active Trades</p>
                            </div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-icon">
                                <i class="fas fa-dollar-sign"></i>
                            </div>
                            <div class="metric-content">
                                <h3 id="dailyProfit">$0.00</h3>
                                <p>Today's Profit</p>
                            </div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-icon">
                                <i class="fas fa-percentage"></i>
                            </div>
                            <div class="metric-content">
                                <h3 id="successRate">0%</h3>
                                <p>Success Rate</p>
                            </div>
                        </div>
                    </div>

                    <!-- Charts Row -->
                    <div class="charts-row">
                        <div class="chart-container">
                            <h3>Live Opportunities</h3>
                            <canvas id="opportunitiesChart"></canvas>
                        </div>
                        <div class="chart-container">
                            <h3>Profit Trends</h3>
                            <canvas id="profitChart"></canvas>
                        </div>
                    </div>

                    <!-- System Health -->
                    <div class="system-status">
                        <h3>System Status</h3>
                        <div id="systemHealth" class="health-indicators">
                            <div class="health-item">
                                <span class="health-label">Scanner Engine</span>
                                <span class="health-status online"><i class="fas fa-check-circle"></i> Online</span>
                            </div>
                            <div class="health-item">
                                <span class="health-label">Trade Executor</span>
                                <span class="health-status online"><i class="fas fa-check-circle"></i> Online</span>
                            </div>
                            <div class="health-item">
                                <span class="health-label">Risk Monitor</span>
                                <span class="health-status online"><i class="fas fa-check-circle"></i> Online</span>
                            </div>
                            <div class="health-item">
                                <span class="health-label">Database</span>
                                <span class="health-status online"><i class="fas fa-check-circle"></i> Online</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Opportunities View -->
            <div id="opportunities" class="content-view">
                <div class="view-header">
                    <h2>Arbitrage Opportunities</h2>
                    <div class="filters-panel">
                        <select id="sportFilter">
                            <option value="">All Sports</option>
                            <option value="football">Football</option>
                            <option value="basketball">Basketball</option>
                            <option value="tennis">Tennis</option>
                        </select>
                        <select id="riskFilter">
                            <option value="">All Risk Levels</option>
                            <option value="tier_a">Tier A (Low Risk)</option>
                            <option value="tier_b">Tier B</option>
                            <option value="tier_c">Tier C</option>
                            <option value="tier_d">Tier D (High Risk)</option>
                        </select>
                        <input type="number" id="minProfit" placeholder="Min Profit %" min="0" max="50">
                        <button class="filter-btn" onclick="applyFilters()">
                            <i class="fas fa-filter"></i> Filter
                        </button>
                        <button class="refresh-btn" onclick="refreshOpportunities()">
                            <i class="fas fa-sync-alt"></i> Refresh
                        </button>
                    </div>
                </div>
                <div class="opportunities-table-container">
                    <table id="opportunitiesTable" class="data-table">
                        <thead>
                            <tr>
                                <th>Event</th>
                                <th>Sport</th>
                                <th>Profit %</th>
                                <th>Expected Profit</th>
                                <th>Risk</th>
                                <th>Time Left</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="opportunitiesTableBody">
                            <!-- Dynamic content -->
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Active Trades View -->
            <div id="trades" class="content-view">
                <div class="view-header">
                    <h2>Active Trades</h2>
                    <button class="action-btn" onclick="showTradeModal()">
                        <i class="fas fa-plus"></i> New Trade
                    </button>
                </div>
                <div class="trades-grid" id="activeTradesGrid">
                    <!-- Dynamic trade cards -->
                </div>
            </div>

            <!-- Performance Analytics -->
            <div id="performance" class="content-view">
                <div class="view-header">
                    <h2>Performance Analytics</h2>
                    <div class="date-range">
                        <input type="date" id="perfStartDate">
                        <input type="date" id="perfEndDate">
                        <button onclick="updatePerformanceCharts()">Update</button>
                    </div>
                </div>
                <div class="analytics-grid">
                    <div class="chart-container large">
                        <h3>Profit Over Time</h3>
                        <canvas id="performanceChart"></canvas>
                    </div>
                    <div class="chart-container">
                        <h3>Win Rate</h3>
                        <canvas id="winRateChart"></canvas>
                    </div>
                    <div class="chart-container">
                        <h3>Risk Distribution</h3>
                        <canvas id="riskChart"></canvas>
                    </div>
                    <div class="metrics-summary">
                        <h3>Key Metrics</h3>
                        <div class="metric-item">
                            <span>Total Profit:</span>
                            <span id="totalProfit">$0.00</span>
                        </div>
                        <div class="metric-item">
                            <span>Average ROI:</span>
                            <span id="avgROI">0%</span>
                        </div>
                        <div class="metric-item">
                            <span>Best Day:</span>
                            <span id="bestDay">$0.00</span>
                        </div>
                        <div class="metric-item">
                            <span>Sharpe Ratio:</span>
                            <span id="sharpeRatio">0.00</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- System Health View -->
            <div id="health" class="content-view">
                <div class="view-header">
                    <h2>System Health Monitor</h2>
                    <div class="health-controls">
                        <button onclick="toggleSystemMonitoring()">Start Monitoring</button>
                        <button onclick="showSystemLogs()">View Logs</button>
                    </div>
                </div>
                <div class="health-grid">
                    <div class="health-card">
                        <h3>CPU Usage</h3>
                        <canvas id="cpuChart" width="200" height="100"></canvas>
                        <div class="health-value" id="cpuValue">0%</div>
                    </div>
                    <div class="health-card">
                        <h3>Memory Usage</h3>
                        <canvas id="memoryChart" width="200" height="100"></canvas>
                        <div class="health-value" id="memoryValue">0%</div>
                    </div>
                    <div class="health-card">
                        <h3>Database Response</h3>
                        <canvas id="dbChart" width="200" height="100"></canvas>
                        <div class="health-value" id="dbValue">0ms</div>
                    </div>
                    <div class="health-card">
                        <h3>Network Latency</h3>
                        <canvas id="networkChart" width="200" height="100"></canvas>
                        <div class="health-value" id="networkValue">0ms</div>
                    </div>
                </div>
            </div>

            <!-- Notifications Panel -->
            <div id="notificationsPanel" class="slide-panel">
                <div class="panel-header">
                    <h3>Notifications</h3>
                    <button onclick="closeNotifications()">×</button>
                </div>
                <div class="panel-content">
                    <div id="notificationsList">
                        <!-- Dynamic notifications -->
                    </div>
                </div>
            </div>

            <!-- Settings Modal -->
            <div id="settingsModal" class="modal">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>User Settings</h3>
                        <button onclick="closeSettingsModal()">×</button>
                    </div>
                    <div class="modal-body">
                        <form id="settingsForm">
                            <div class="form-group">
                                <label>Username:</label>
                                <input type="text" id="username" placeholder="Enter username">
                            </div>
                            <div class="form-group">
                                <label>Email Notifications:</label>
                                <input type="checkbox" id="emailNotifications">
                            </div>
                            <div class="form-group">
                                <label>Push Notifications:</label>
                                <input type="checkbox" id="pushNotifications">
                            </div>
                            <div class="form-group">
                                <label>Alert Threshold:</label>
                                <select id="alertThreshold">
                                    <option value="low">Low Priority</option>
                                    <option value="medium">Medium Priority</option>
                                    <option value="high">High Priority</option>
                                    <option value="critical">Critical Only</option>
                                </select>
                            </div>
                            <button type="submit" class="action-btn">Save Settings</button>
                        </form>
                    </div>
                </div>
            </div>
        </main>
    </div>

    <!-- Toast Notifications -->
    <div id="toastContainer" class="toast-container"></div>

    <!-- Loading Overlay -->
    <div id="loadingOverlay" class="loading-overlay">
        <div class="spinner"></div>
        <p>Loading dashboard data...</p>
    </div>

    <!-- Scripts -->
    <script src="/static/dashboard.js"></script>
</body>
</html>"""

        with open(self.web_dir / "dashboard.html", "w") as f:
            f.write(html_content)
    
    def _create_dashboard_css(self):
        """Create comprehensive CSS styles for the dashboard."""
        css_content = """/* ARBitech Dashboard Styles */

:root {
    --primary-color: #1a73e8;
    --secondary-color: #34a853;
    --warning-color: #fbbc04;
    --error-color: #ea4335;
    --dark-bg: #1e1e1e;
    --dark-surface: #2d2d2d;
    --dark-border: #3d3d3d;
    --light-text: #ffffff;
    --gray-text: #9aa0a6;
    --success-color: #34a853;
    --border-radius: 8px;
    --shadow: 0 2px 8px rgba(0,0,0,0.1);
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background-color: var(--dark-bg);
    color: var(--light-text);
    line-height: 1.6;
}

/* Header Styles */
.dashboard-header {
    background-color: var(--dark-surface);
    padding: 1rem 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--dark-border);
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 1000;
}

.header-left h1 {
    color: var(--primary-color);
    margin-right: 1rem;
    font-size: 1.5rem;
}

.header-left {
    display: flex;
    align-items: center;
}

.connection-status {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.status-indicator {
    display: flex;
    align-items: center;
    gap: 0.25rem;
}

.status-indicator.connected .fa-circle {
    color: var(--success-color);
}

.status-indicator.disconnected .fa-circle {
    color: var(--error-color);
}

.user-info {
    display: flex;
    align-items: center;
    gap: 1rem;
}

.user-menu {
    position: relative;
}

.user-menu-btn {
    background: none;
    border: none;
    color: var(--light-text);
    font-size: 1.5rem;
    cursor: pointer;
    padding: 0.5rem;
}

.user-dropdown {
    position: absolute;
    top: 100%;
    right: 0;
    background-color: var(--dark-surface);
    border: 1px solid var(--dark-border);
    border-radius: var(--border-radius);
    padding: 0.5rem 0;
    min-width: 200px;
    display: none;
    box-shadow: var(--shadow);
}

.user-dropdown a {
    display: block;
    padding: 0.75rem 1rem;
    color: var(--light-text);
    text-decoration: none;
    border-bottom: 1px solid var(--dark-border);
}

.user-dropdown a:last-child {
    border-bottom: none;
}

.user-dropdown a:hover {
    background-color: var(--dark-bg);
}

/* Dashboard Layout */
.dashboard-container {
    display: flex;
    margin-top: 80px;
    min-height: calc(100vh - 80px);
}

/* Sidebar Styles */
.sidebar {
    width: 250px;
    background-color: var(--dark-surface);
    border-right: 1px solid var(--dark-border);
    padding: 1rem 0;
    position: fixed;
    top: 80px;
    bottom: 0;
    overflow-y: auto;
}

.nav-section {
    margin-bottom: 2rem;
}

.nav-section h3 {
    color: var(--gray-text);
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 0.5rem;
    padding: 0 1rem;
}

.sidebar ul {
    list-style: none;
}

.sidebar li {
    margin-bottom: 0.25rem;
}

.nav-link {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    color: var(--light-text);
    text-decoration: none;
    transition: background-color 0.2s;
    border-left: 3px solid transparent;
}

.nav-link:hover {
    background-color: var(--dark-bg);
    border-left-color: var(--primary-color);
}

.nav-link.active {
    background-color: var(--primary-color);
    border-left-color: var(--primary-color);
}

.nav-link i {
    width: 20px;
    text-align: center;
}

/* Main Content */
.main-content {
    margin-left: 250px;
    padding: 2rem;
    flex: 1;
}

.content-view {
    display: none;
}

.content-view.active {
    display: block;
}

/* Metrics Row */
.metrics-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1rem;
    margin-bottom: 2rem;
}

.metric-card {
    background-color: var(--dark-surface);
    border: 1px solid var(--dark-border);
    border-radius: var(--border-radius);
    padding: 1.5rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    transition: transform 0.2s, box-shadow 0.2s;
}

.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow);
}

.metric-icon {
    background-color: var(--primary-color);
    color: white;
    width: 60px;
    height: 60px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
}

.metric-content h3 {
    font-size: 2rem;
    margin-bottom: 0.25rem;
}

.metric-content p {
    color: var(--gray-text);
    font-size: 0.9rem;
}

/* Charts */
.charts-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2rem;
    margin-bottom: 2rem;
}

.chart-container {
    background-color: var(--dark-surface);
    border: 1px solid var(--dark-border);
    border-radius: var(--border-radius);
    padding: 1.5rem;
}

.chart-container.large {
    grid-column: span 2;
}

.chart-container h3 {
    margin-bottom: 1rem;
    color: var(--light-text);
}

/* Data Tables */
.view-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
}

.view-header h2 {
    color: var(--light-text);
}

.filters-panel {
    display: flex;
    gap: 1rem;
    align-items: center;
}

.filters-panel select,
.filters-panel input {
    padding: 0.5rem;
    border: 1px solid var(--dark-border);
    border-radius: var(--border-radius);
    background-color: var(--dark-surface);
    color: var(--light-text);
}

.data-table-container {
    background-color: var(--dark-surface);
    border: 1px solid var(--dark-border);
    border-radius: var(--border-radius);
    overflow: hidden;
}

.data-table {
    width: 100%;
    border-collapse: collapse;
}

.data-table th,
.data-table td {
    padding: 1rem;
    text-align: left;
    border-bottom: 1px solid var(--dark-border);
}

.data-table th {
    background-color: var(--dark-bg);
    font-weight: 600;
    color: var(--gray-text);
    text-transform: uppercase;
    font-size: 0.85rem;
    letter-spacing: 1px;
}

.data-table tbody tr:hover {
    background-color: var(--dark-bg);
}

/* Buttons */
.action-btn,
.filter-btn,
.refresh-btn {
    background-color: var(--primary-color);
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: var(--border-radius);
    cursor: pointer;
    font-size: 0.9rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    transition: background-color 0.2s;
}

.action-btn:hover,
.filter-btn:hover,
.refresh-btn:hover {
    background-color: #1557b0;
}

/* System Health */
.system-status {
    background-color: var(--dark-surface);
    border: 1px solid var(--dark-border);
    border-radius: var(--border-radius);
    padding: 1.5rem;
}

.system-status h3 {
    margin-bottom: 1rem;
}

.health-indicators {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}

.health-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.health-label {
    font-weight: 500;
}

.health-status {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.25rem 0.75rem;
    border-radius: 1rem;
    font-size: 0.85rem;
}

.health-status.online {
    background-color: rgba(52, 168, 83, 0.2);
    color: var(--success-color);
}

.health-status.offline {
    background-color: rgba(234, 67, 53, 0.2);
    color: var(--error-color);
}

/* Analytics Grid */
.analytics-grid {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 2rem;
}

.metrics-summary {
    background-color: var(--dark-surface);
    border: 1px solid var(--dark-border);
    border-radius: var(--border-radius);
    padding: 1.5rem;
}

.metric-item {
    display: flex;
    justify-content: space-between;
    padding: 0.75rem 0;
    border-bottom: 1px solid var(--dark-border);
}

.metric-item:last-child {
    border-bottom: none;
}

/* Health Grid */
.health-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.5rem;
}

.health-card {
    background-color: var(--dark-surface);
    border: 1px solid var(--dark-border);
    border-radius: var(--border-radius);
    padding: 1.5rem;
    text-align: center;
}

.health-card h3 {
    margin-bottom: 1rem;
}

.health-value {
    font-size: 1.5rem;
    font-weight: bold;
    color: var(--primary-color);
    margin-top: 0.5rem;
}

/* Trades Grid */
.trades-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1.5rem;
}

.trade-card {
    background-color: var(--dark-surface);
    border: 1px solid var(--dark-border);
    border-radius: var(--border-radius);
    padding: 1.5rem;
}

.trade-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
}

.trade-status {
    padding: 0.25rem 0.75rem;
    border-radius: 1rem;
    font-size: 0.85rem;
    font-weight: 500;
}

.trade-status.pending {
    background-color: rgba(251, 188, 4, 0.2);
    color: var(--warning-color);
}

.trade-status.executing {
    background-color: rgba(26, 115, 232, 0.2);
    color: var(--primary-color);
}

.trade-status.completed {
    background-color: rgba(52, 168, 83, 0.2);
    color: var(--success-color);
}

.trade-status.failed {
    background-color: rgba(234, 67, 53, 0.2);
    color: var(--error-color);
}

/* Modal Styles */
.modal {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.7);
    z-index: 2000;
}

.modal-content {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background-color: var(--dark-surface);
    border-radius: var(--border-radius);
    width: 90%;
    max-width: 500px;
    max-height: 90vh;
    overflow-y: auto;
}

.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem;
    border-bottom: 1px solid var(--dark-border);
}

.modal-body {
    padding: 1.5rem;
}

/* Form Styles */
.form-group {
    margin-bottom: 1rem;
}

.form-group label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
}

.form-group input,
.form-group select {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid var(--dark-border);
    border-radius: var(--border-radius);
    background-color: var(--dark-bg);
    color: var(--light-text);
}

/* Toast Notifications */
.toast-container {
    position: fixed;
    top: 100px;
    right: 2rem;
    z-index: 3000;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.toast {
    background-color: var(--dark-surface);
    border: 1px solid var(--dark-border);
    border-radius: var(--border-radius);
    padding: 1rem;
    min-width: 300px;
    box-shadow: var(--shadow);
    animation: slideIn 0.3s ease-out;
}

.toast.success {
    border-left: 4px solid var(--success-color);
}

.toast.warning {
    border-left: 4px solid var(--warning-color);
}

.toast.error {
    border-left: 4px solid var(--error-color);
}

@keyframes slideIn {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

/* Loading Overlay */
.loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.8);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    z-index: 4000;
}

.spinner {
    width: 50px;
    height: 50px;
    border: 3px solid var(--dark-border);
    border-top: 3px solid var(--primary-color);
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 1rem;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* Slide Panel */
.slide-panel {
    position: fixed;
    top: 0;
    right: -400px;
    width: 400px;
    height: 100vh;
    background-color: var(--dark-surface);
    border-left: 1px solid var(--dark-border);
    z-index: 1500;
    transition: right 0.3s ease;
    overflow-y: auto;
}

.slide-panel.open {
    right: 0;
}

.panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem;
    border-bottom: 1px solid var(--dark-border);
}

/* Responsive Design */
@media (max-width: 1200px) {
    .charts-row {
        grid-template-columns: 1fr;
    }
    
    .chart-container.large {
        grid-column: span 1;
    }
    
    .analytics-grid {
        grid-template-columns: 1fr;
    }
}

@media (max-width: 768px) {
    .dashboard-container {
        flex-direction: column;
    }
    
    .sidebar {
        position: static;
        width: 100%;
        height: auto;
    }
    
    .main-content {
        margin-left: 0;
    }
    
    .dashboard-header {
        padding: 1rem;
    }
    
    .header-left h1 {
        font-size: 1.2rem;
    }
    
    .metrics-row {
        grid-template-columns: 1fr;
    }
    
    .filters-panel {
        flex-wrap: wrap;
        gap: 0.5rem;
    }
    
    .trades-grid {
        grid-template-columns: 1fr;
    }
    
    .health-grid {
        grid-template-columns: 1fr 1fr;
    }
    
    .slide-panel {
        width: 100%;
        right: -100%;
    }
}

@media (max-width: 480px) {
    .main-content {
        padding: 1rem;
    }
    
    .view-header {
        flex-direction: column;
        align-items: stretch;
        gap: 1rem;
    }
    
    .health-grid {
        grid-template-columns: 1fr;
    }
    
    .modal-content {
        width: 95%;
        margin: 1rem;
    }
}

/* Dark Theme Variables */
@media (prefers-color-scheme: light) {
    :root {
        --dark-bg: #ffffff;
        --dark-surface: #f8f9fa;
        --dark-border: #dee2e6;
        --light-text: #212529;
        --gray-text: #6c757d;
    }
}"""

        with open(self.web_dir / "dashboard.css", "w") as f:
            f.write(css_content)
    
    def _create_dashboard_js(self):
        """Create JavaScript for real-time dashboard functionality."""
        js_content = """// ARBitech Dashboard JavaScript

class DashboardClient {
    constructor() {
        this.socket = null;
        this.userId = localStorage.getItem('arbitech_user_id') || this.generateUserId();
        this.session = null;
        this.preferences = this.loadPreferences();
        this.charts = {};
        this.updateIntervals = {};
        
        this.init();
    }
    
    generateUserId() {
        const id = 'user_' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('arbitech_user_id', id);
        return id;
    }
    
    loadPreferences() {
        const defaults = {
            subscriptions: ['opportunity', 'trade', 'system_health', 'performance_metrics'],
            sports: [],
            min_profit: 0,
            max_risk_tier: 'tier_d',
            alert_threshold: 'medium',
            email_notifications: true,
            push_notifications: true
        };
        
        const saved = localStorage.getItem('arbitech_preferences');
        return saved ? { ...defaults, ...JSON.parse(saved) } : defaults;
    }
    
    async init() {
        try {
            // Initialize WebSocket connection
            await this.connect();
            
            // Setup event listeners
            this.setupEventListeners();
            
            // Initialize charts
            this.initializeCharts();
            
            // Start real-time updates
            this.startRealTimeUpdates();
            
            // Authenticate with server
            await this.authenticate();
            
            // Load initial data
            await this.loadInitialData();
            
            console.log('Dashboard initialized successfully');
        } catch (error) {
            console.error('Dashboard initialization failed:', error);
            this.showToast('Failed to connect to dashboard server', 'error');
        }
    }
    
    async connect() {
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsHost = window.location.hostname;
        const wsPort = 8765;
        
        return new Promise((resolve, reject) => {
            this.socket = new WebSocket(`${wsProtocol}//${wsHost}:${wsPort}`);
            
            this.socket.onopen = () => {
                console.log('WebSocket connected');
                this.updateConnectionStatus(true);
                resolve();
            };
            
            this.socket.onclose = () => {
                console.log('WebSocket disconnected');
                this.updateConnectionStatus(false);
                this.attemptReconnect();
            };
            
            this.socket.onerror = (error) => {
                console.error('WebSocket error:', error);
                reject(error);
            };
            
            this.socket.onmessage = (event) => {
                this.handleMessage(JSON.parse(event.data));
            };
        });
    }
    
    updateConnectionStatus(connected) {
        const indicator = document.getElementById('connectionIndicator');
        const text = document.getElementById('connectionText');
        
        if (connected) {
            indicator.className = 'status-indicator connected';
            text.textContent = 'Connected';
        } else {
            indicator.className = 'status-indicator disconnected';
            text.textContent = 'Disconnected';
        }
    }
    
    attemptReconnect() {
        setTimeout(() => {
            console.log('Attempting to reconnect...');
            this.connect();
        }, 5000);
    }
    
    async authenticate() {
        const authData = {
            type: 'authenticate',
            user_id: this.userId,
            preferences: this.preferences
        };
        
        this.socket.send(JSON.stringify(authData));
    }
    
    handleMessage(message) {
        const { type, data } = message;
        
        switch (type) {
            case 'opportunity_update':
                this.handleOpportunityUpdate(data);
                break;
            case 'trade_update':
                this.handleTradeUpdate(data);
                break;
            case 'system_health_update':
                this.handleSystemHealthUpdate(data);
                break;
            case 'performance_metrics_update':
                this.handlePerformanceUpdate(data);
                break;
            case 'notification':
                this.handleNotification(data);
                break;
            case 'risk_alert':
                this.handleRiskAlert(data);
                break;
            default:
                console.log('Unknown message type:', type);
        }
    }
    
    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const view = e.currentTarget.dataset.view;
                this.switchView(view);
            });
        });
        
        // User menu
        const userMenuBtn = document.querySelector('.user-menu-btn');
        const userDropdown = document.querySelector('.user-dropdown');
        
        userMenuBtn.addEventListener('click', () => {
            userDropdown.style.display = userDropdown.style.display === 'block' ? 'none' : 'block';
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.user-menu')) {
                userDropdown.style.display = 'none';
            }
        });
        
        // Form submissions
        const settingsForm = document.getElementById('settingsForm');
        if (settingsForm) {
            settingsForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveSettings();
            });
        }
        
        // Filter changes
        document.getElementById('sportFilter')?.addEventListener('change', this.applyFilters.bind(this));
        document.getElementById('riskFilter')?.addEventListener('change', this.applyFilters.bind(this));
        document.getElementById('minProfit')?.addEventListener('input', this.applyFilters.bind(this));
    }
    
    switchView(viewId) {
        // Update navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        document.querySelector(`[data-view="${viewId}"]`)?.classList.add('active');
        
        // Update content
        document.querySelectorAll('.content-view').forEach(view => {
            view.classList.remove('active');
        });
        document.getElementById(viewId)?.classList.add('active');
        
        // Load view-specific data
        this.loadViewData(viewId);
    }
    
    async loadViewData(viewId) {
        switch (viewId) {
            case 'opportunities':
                await this.loadOpportunities();
                break;
            case 'trades':
                await this.loadActiveTrades();
                break;
            case 'performance':
                await this.loadPerformanceData();
                break;
            case 'health':
                await this.loadSystemHealth();
                break;
        }
    }
    
    initializeCharts() {
        // Opportunities Chart
        const opportunitiesCtx = document.getElementById('opportunitiesChart');
        if (opportunitiesCtx) {
            this.charts.opportunities = new Chart(opportunitiesCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Active Opportunities',
                        data: [],
                        borderColor: '#1a73e8',
                        backgroundColor: 'rgba(26, 115, 232, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }
        
        // Profit Chart
        const profitCtx = document.getElementById('profitChart');
        if (profitCtx) {
            this.charts.profit = new Chart(profitCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Profit ($)',
                        data: [],
                        borderColor: '#34a853',
                        backgroundColor: 'rgba(52, 168, 83, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        }
        
        // Performance Chart
        const performanceCtx = document.getElementById('performanceChart');
        if (performanceCtx) {
            this.charts.performance = new Chart(performanceCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [
                        {
                            label: 'Total Profit',
                            data: [],
                            borderColor: '#34a853',
                            yAxisID: 'y'
                        },
                        {
                            label: 'Win Rate (%)',
                            data: [],
                            borderColor: '#1a73e8',
                            yAxisID: 'y1'
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            type: 'linear',
                            display: true,
                            position: 'left',
                        },
                        y1: {
                            type: 'linear',
                            display: true,
                            position: 'right',
                            grid: {
                                drawOnChartArea: false,
                            },
                        }
                    }
                }
            });
        }
    }
    
    startRealTimeUpdates() {
        // Update metrics every 5 seconds
        this.updateIntervals.metrics = setInterval(() => {
            this.updateMetrics();
        }, 5000);
        
        // Update charts every 10 seconds
        this.updateIntervals.charts = setInterval(() => {
            this.updateCharts();
        }, 10000);
        
        // Update system health every 2 seconds
        this.updateIntervals.health = setInterval(() => {
            this.updateSystemHealth();
        }, 2000);
    }
    
    async loadInitialData() {
        // Show loading overlay
        this.showLoading(true);
        
        try {
            await Promise.all([
                this.updateMetrics(),
                this.loadOpportunities(),
                this.loadActiveTrades(),
                this.loadSystemHealth()
            ]);
        } finally {
            this.showLoading(false);
        }
    }
    
    async updateMetrics() {
        // Mock data - in real implementation, fetch from API
        const metrics = {
            totalOpportunities: Math.floor(Math.random() * 50) + 10,
            activeTrades: Math.floor(Math.random() * 10),
            dailyProfit: (Math.random() * 1000).toFixed(2),
            successRate: (Math.random() * 100).toFixed(1)
        };
        
        Object.entries(metrics).forEach(([key, value]) => {
            const element = document.getElementById(key);
            if (element) {
                element.textContent = key === 'dailyProfit' ? `$${value}` : `${value}%` === value ? `${value}%` : value;
            }
        });
    }
    
    async loadOpportunities() {
        // Mock data - in real implementation, fetch from API
        const opportunities = [
            {
                id: 1,
                event: 'Manchester United vs Liverpool',
                sport: 'football',
                profit: 5.2,
                expected_profit: 125.50,
                risk: 'tier_a',
                time_left: '25m'
            },
            {
                id: 2,
                event: 'Lakers vs Warriors',
                sport: 'basketball',
                profit: 3.8,
                expected_profit: 89.20,
                risk: 'tier_b',
                time_left: '45m'
            }
        ];
        
        const tbody = document.getElementById('opportunitiesTableBody');
        if (tbody) {
            tbody.innerHTML = opportunities.map(opp => `
                <tr>
                    <td>${opp.event}</td>
                    <td>${opp.sport}</td>
                    <td class="profit-positive">${opp.profit}%</td>
                    <td>$${opp.expected_profit}</td>
                    <td><span class="risk-tier risk-${opp.risk}">${opp.risk.replace('_', ' ').toUpperCase()}</span></td>
                    <td>${opp.time_left}</td>
                    <td>
                        <button class="action-btn small" onclick="dashboardClient.viewOpportunity(${opp.id})">
                            <i class="fas fa-eye"></i> View
                        </button>
                    </td>
                </tr>
            `).join('');
        }
    }
    
    async loadActiveTrades() {
        // Mock data - in real implementation, fetch from API
        const trades = [
            {
                id: 1,
                event: 'Real Madrid vs Barcelona',
                status: 'executing',
                progress: 75,
                expected_profit: 95.30,
                start_time: '10:30 AM'
            },
            {
                id: 2,
                event: 'Djokovic vs Nadal',
                status: 'pending',
                progress: 0,
                expected_profit: 67.80,
                start_time: '11:00 AM'
            }
        ];
        
        const grid = document.getElementById('activeTradesGrid');
        if (grid) {
            grid.innerHTML = trades.map(trade => `
                <div class="trade-card">
                    <div class="trade-header">
                        <h4>${trade.event}</h4>
                        <span class="trade-status ${trade.status}">${trade.status.toUpperCase()}</span>
                    </div>
                    <div class="trade-progress">
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${trade.progress}%"></div>
                        </div>
                        <span>${trade.progress}% Complete</span>
                    </div>
                    <div class="trade-details">
                        <div>Expected Profit: $${trade.expected_profit}</div>
                        <div>Started: ${trade.start_time}</div>
                    </div>
                    <div class="trade-actions">
                        <button class="action-btn small" onclick="dashboardClient.viewTrade(${trade.id})">
                            <i class="fas fa-info-circle"></i> Details
                        </button>
                    </div>
                </div>
            `).join('');
        }
    }
    
    async loadPerformanceData() {
        // Mock data for performance charts
        const performanceCtx = document.getElementById('performanceChart');
        if (performanceCtx && this.charts.performance) {
            const now = new Date();
            const labels = [];
            const profitData = [];
            const winRateData = [];
            
            for (let i = 6; i >= 0; i--) {
                const date = new Date(now.getTime() - i * 24 * 60 * 60 * 1000);
                labels.push(date.toLocaleDateString());
                profitData.push((Math.random() * 500) + 100);
                winRateData.push(Math.random() * 40 + 60);
            }
            
            this.charts.performance.data.labels = labels;
            this.charts.performance.data.datasets[0].data = profitData;
            this.charts.performance.data.datasets[1].data = winRateData;
            this.charts.performance.update();
        }
        
        // Update metrics
        document.getElementById('totalProfit').textContent = '$' + (Math.random() * 5000 + 1000).toFixed(2);
        document.getElementById('avgROI').textContent = (Math.random() * 20 + 5).toFixed(1) + '%';
        document.getElementById('bestDay').textContent = '$' + (Math.random() * 1000 + 500).toFixed(2);
        document.getElementById('sharpeRatio').textContent = (Math.random() * 2 + 1).toFixed(2);
    }
    
    async loadSystemHealth() {
        // Mock system health data
        const components = [
            { name: 'Scanner Engine', status: 'online' },
            { name: 'Trade Executor', status: 'online' },
            { name: 'Risk Monitor', status: 'online' },
            { name: 'Database', status: 'online' }
        ];
        
        const healthContainer = document.getElementById('systemHealth');
        if (healthContainer) {
            healthContainer.innerHTML = components.map(comp => `
                <div class="health-item">
                    <span class="health-label">${comp.name}</span>
                    <span class="health-status ${comp.status}">
                        <i class="fas fa-check-circle"></i> ${comp.status.charAt(0).toUpperCase() + comp.status.slice(1)}
                    </span>
                </div>
            `).join('');
        }
    }
    
    handleOpportunityUpdate(data) {
        console.log('New opportunity:', data);
        this.updateOpportunitiesChart();
        this.showToast(`New opportunity detected: ${data.event || 'Unknown event'}`, 'success');
    }
    
    handleTradeUpdate(data) {
        console.log('Trade update:', data);
        this.updateActiveTrades();
    }
    
    handleSystemHealthUpdate(data) {
        console.log('System health update:', data);
        this.updateHealthCharts(data);
    }
    
    handlePerformanceUpdate(data) {
        console.log('Performance update:', data);
        this.updatePerformanceChart();
    }
    
    handleNotification(data) {
        this.showNotification(data.message, data.type || 'info');
    }
    
    handleRiskAlert(data) {
        this.showToast(data.message, 'warning');
    }
    
    applyFilters() {
        const sportFilter = document.getElementById('sportFilter')?.value || '';
        const riskFilter = document.getElementById('riskFilter')?.value || '';
        const minProfit = document.getElementById('minProfit')?.value || 0;
        
        // Filter opportunities table
        const rows = document.querySelectorAll('#opportunitiesTableBody tr');
        rows.forEach(row => {
            const sport = row.children[1]?.textContent.toLowerCase();
            const profit = parseFloat(row.children[2]?.textContent) || 0;
            const risk = row.children[4]?.textContent.toLowerCase().replace(' ', '_');
            
            const sportMatch = !sportFilter || sport === sportFilter;
            const profitMatch = profit >= minProfit;
            const riskMatch = !riskFilter || risk === riskFilter;
            
            row.style.display = (sportMatch && profitMatch && riskMatch) ? '' : 'none';
        });
    }
    
    showSettingsModal() {
        const modal = document.getElementById('settingsModal');
        if (modal) {
            modal.style.display = 'block';
            
            // Populate form with current preferences
            document.getElementById('username').value = this.preferences.username || '';
            document.getElementById('emailNotifications').checked = this.preferences.email_notifications;
            document.getElementById('pushNotifications').checked = this.preferences.push_notifications;
            document.getElementById('alertThreshold').value = this.preferences.alert_threshold;
        }
    }
    
    saveSettings() {
        this.preferences = {
            ...this.preferences,
            username: document.getElementById('username').value,
            email_notifications: document.getElementById('emailNotifications').checked,
            push_notifications: document.getElementById('pushNotifications').checked,
            alert_threshold: document.getElementById('alertThreshold').value
        };
        
        localStorage.setItem('arbitech_preferences', JSON.stringify(this.preferences));
        this.showToast('Settings saved successfully', 'success');
        this.closeSettingsModal();
        
        // Send updated preferences to server
        this.socket?.send(JSON.stringify({
            type: 'update_preferences',
            preferences: this.preferences
        }));
    }
    
    closeSettingsModal() {
        const modal = document.getElementById('settingsModal');
        if (modal) {
            modal.style.display = 'none';
        }
    }
    
    showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div class="toast-header">
                <strong>${type.charAt(0).toUpperCase() + type.slice(1)}</strong>
                <button onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
            <div class="toast-body">${message}</div>
        `;
        
        container.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, 5000);
    }
    
    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.style.display = show ? 'flex' : 'none';
        }
    }
    
    // Action handlers
    viewOpportunity(id) {
        this.showToast(`Viewing opportunity ${id}`, 'info');
        // In real implementation, open opportunity details
    }
    
    viewTrade(id) {
        this.showToast(`Viewing trade ${id}`, 'info');
        // In real implementation, open trade details
    }
    
    refreshOpportunities() {
        this.loadOpportunities();
        this.showToast('Opportunities refreshed', 'success');
    }
    
    updateCharts() {
        // Update opportunities chart
        if (this.charts.opportunities) {
            const now = new Date();
            const labels = this.charts.opportunities.data.labels;
            
            if (labels.length > 20) {
                labels.shift();
                this.charts.opportunities.data.datasets[0].data.shift();
            }
            
            labels.push(now.toLocaleTimeString());
            this.charts.opportunities.data.datasets[0].data.push(Math.floor(Math.random() * 50) + 10);
            
            this.charts.opportunities.update('none');
        }
        
        // Update profit chart
        if (this.charts.profit) {
            const now = new Date();
            const labels = this.charts.profit.data.labels;
            
            if (labels.length > 20) {
                labels.shift();
                this.charts.profit.data.datasets[0].data.shift();
            }
            
            labels.push(now.toLocaleTimeString());
            this.charts.profit.data.datasets[0].data.push((Math.random() * 1000).toFixed(2));
            
            this.charts.profit.update('none');
        }
    }
    
    updateSystemHealth() {
        // Mock system health updates
        const healthComponents = document.querySelectorAll('.health-item');
        healthComponents.forEach(item => {
            // Randomly change some component statuses for demo
            if (Math.random() < 0.05) { // 5% chance of status change
                const statusElement = item.querySelector('.health-status');
                const isOnline = statusElement.classList.contains('online');
                
                if (isOnline && Math.random() < 0.5) {
                    statusElement.className = 'health-status offline';
                    statusElement.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Offline';
                    this.showToast('Component went offline', 'warning');
                } else if (!isOnline) {
                    statusElement.className = 'health-status online';
                    statusElement.innerHTML = '<i class="fas fa-check-circle"></i> Online';
                    this.showToast('Component came back online', 'success');
                }
            }
        });
    }
}

// Global functions for HTML event handlers
function showUserSettings() {
    if (window.dashboardClient) {
        window.dashboardClient.showSettingsModal();
    }
}

function closeSettingsModal() {
    if (window.dashboardClient) {
        window.dashboardClient.closeSettingsModal();
    }
}

function applyFilters() {
    if (window.dashboardClient) {
        window.dashboardClient.applyFilters();
    }
}

function refreshOpportunities() {
    if (window.dashboardClient) {
        window.dashboardClient.refreshOpportunities();
    }
}

function showTradeModal() {
    window.dashboardClient?.showToast('New trade functionality coming soon', 'info');
}

function toggleSystemMonitoring() {
    const btn = event.target;
    if (btn.textContent.includes('Start')) {
        btn.textContent = 'Stop Monitoring';
        window.dashboardClient?.showToast('System monitoring started', 'success');
    } else {
        btn.textContent = 'Start Monitoring';
        window.dashboardClient?.showToast('System monitoring stopped', 'info');
    }
}

function showSystemLogs() {
    window.dashboardClient?.showToast('System logs view coming soon', 'info');
}

function updatePerformanceCharts() {
    if (window.dashboardClient) {
        window.dashboardClient.loadPerformanceData();
        window.dashboardClient.showToast('Performance charts updated', 'success');
    }
}

function closeNotifications() {
    const panel = document.getElementById('notificationsPanel');
    if (panel) {
        panel.classList.remove('open');
    }
}

function logout() {
    localStorage.removeItem('arbitech_user_id');
    localStorage.removeItem('arbitech_preferences');
    location.reload();
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.dashboardClient = new DashboardClient();
});"""

        with open(self.web_dir / "dashboard.js", "w") as f:
            f.write(js_content)
    
    def _init_arbittech_components(self):
        """Initialize ARBITech components integration."""
        try:
            self.scanner_engine = ScannerEngine()
            self.trade_coordinator = TradeCoordinator()
            self.risk_monitor = MonitoringSystem()
            logger.info("ARBITech components initialized")
        except Exception as e:
            logger.warning(f"Some ARBITech components not available: {e}")
            self.scanner_engine = None
            self.trade_coordinator = None
            self.risk_monitor = None
    
    async def start(self):
        """Start the dashboard UI server."""
        if self.is_running:
            return
        
        self.is_running = True
        
        # Start HTTP server for web interface
        self.server = HTTPServer((self.host, self.port), DashboardHTTPHandler)
        
        # Set the dashboard instance for the HTTP handler
        DashboardHTTPHandler.dashboard = self
        
        # Start WebSocket server if not provided
        if not self.dashboard_manager:
            self.dashboard_manager = DashboardManager()
            await self.dashboard_manager.start(self.host, 8765)
        
        # Start background tasks
        self.executor = ThreadPoolExecutor(max_workers=5)
        
        logger.info(f"Dashboard UI starting on http://{self.host}:{self.port}")
        logger.info(f"WebSocket server running on ws://{self.host}:8765")
        
        # Start server
        self.server.serve_forever()
    
    async def stop(self):
        """Stop the dashboard UI server."""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.server:
            self.server.shutdown()
            self.server = None
        
        if self.dashboard_manager:
            await self.dashboard_manager.stop()
        
        if hasattr(self, 'executor'):
            self.executor.shutdown()
        
        logger.info("Dashboard UI stopped")
    
    def get_stats(self) -> DashboardStats:
        """Get current dashboard statistics."""
        self.stats.active_sessions = len(self.sessions)
        self.stats.connected_users = list(self.sessions.keys())
        
        # Update from dashboard manager if available
        if self.dashboard_manager:
            try:
                manager_stats = self.dashboard_manager.get_stats()
                if hasattr(manager_stats, 'connected_clients'):
                    self.stats.active_sessions = manager_stats.connected_clients
            except:
                pass
        
        return self.stats
    
    def create_mock_data(self):
        """Create mock data for demonstration purposes."""
        return {
            'opportunities': [
                {
                    'id': str(uuid.uuid4()),
                    'event': 'Manchester United vs Liverpool',
                    'sport': 'football',
                    'profit_margin': 0.052,
                    'expected_profit': 125.50,
                    'risk_tier': 'tier_a',
                    'time_remaining': 1500,
                    'legs': []
                },
                {
                    'id': str(uuid.uuid4()),
                    'event': 'Lakers vs Warriors',
                    'sport': 'basketball',
                    'profit_margin': 0.038,
                    'expected_profit': 89.20,
                    'risk_tier': 'tier_b',
                    'time_remaining': 2700,
                    'legs': []
                }
            ],
            'trades': [
                {
                    'id': str(uuid.uuid4()),
                    'status': 'executing',
                    'progress': 75,
                    'expected_profit': 95.30,
                    'start_time': datetime.now().isoformat(),
                    'legs': []
                }
            ],
            'system_health': {
                'scanner_engine': {'status': 'online', 'response_time': 45},
                'trade_executor': {'status': 'online', 'response_time': 23},
                'risk_monitor': {'status': 'online', 'response_time': 12},
                'database': {'status': 'online', 'response_time': 8}
            }
        }


class DashboardHTTPHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the dashboard web interface."""
    
    dashboard = None  # Will be set by the dashboard instance
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/' or path == '/dashboard.html':
            self.serve_dashboard()
        elif path == '/static/dashboard.css':
            self.serve_css()
        elif path == '/static/dashboard.js':
            self.serve_js()
        elif path.startswith('/api/'):
            self.serve_api(path, parsed_path.query)
        else:
            self.send_error(404)
    
    def serve_dashboard(self):
        """Serve the main dashboard HTML."""
        try:
            html_path = self.dashboard.web_dir / "dashboard.html"
            with open(html_path, 'r') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(content.encode())
        except Exception as e:
            self.send_error(500, f"Error serving dashboard: {e}")
    
    def serve_css(self):
        """Serve CSS styles."""
        try:
            css_path = self.dashboard.web_dir / "dashboard.css"
            with open(css_path, 'r') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/css')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(content.encode())
        except Exception as e:
            self.send_error(500, f"Error serving CSS: {e}")
    
    def serve_js(self):
        """Serve JavaScript."""
        try:
            js_path = self.dashboard.web_dir / "dashboard.js"
            with open(js_path, 'r') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/javascript')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(content.encode())
        except Exception as e:
            self.send_error(500, f"Error serving JavaScript: {e}")
    
    def serve_api(self, path: str, query: str):
        """Serve API endpoints."""
        try:
            if path == '/api/stats':
                stats = self.dashboard.get_stats()
                self.send_json_response(asdict(stats))
            elif path == '/api/opportunities':
                mock_data = self.dashboard.create_mock_data()
                self.send_json_response(mock_data['opportunities'])
            elif path == '/api/trades':
                mock_data = self.dashboard.create_mock_data()
                self.send_json_response(mock_data['trades'])
            elif path == '/api/health':
                mock_data = self.dashboard.create_mock_data()
                self.send_json_response(mock_data['system_health'])
            else:
                self.send_error(404, "API endpoint not found")
        except Exception as e:
            self.send_error(500, f"API error: {e}")
    
    def send_json_response(self, data: dict):
        """Send JSON response."""
        response = json.dumps(data, default=str)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        self.wfile.write(response.encode())
    
    def log_message(self, format, *args):
        """Override to reduce log noise."""
        pass


async def main():
    """Main function to start the dashboard."""
    import argparse
    
    parser = argparse.ArgumentParser(description='ARBitech Dashboard UI')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8080, help='Port to bind to')
    parser.add_argument('--ws-port', type=int, default=8765, help='WebSocket port')
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and start dashboard
    dashboard = DashboardUI(
        port=args.port,
        host=args.host
    )
    
    dashboard.dashboard_manager.ws_port = args.ws_port
    
    try:
        await dashboard.start()
    except KeyboardInterrupt:
        logger.info("Shutting down dashboard...")
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
    finally:
        await dashboard.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Dashboard stopped")
    except Exception as e:
        logger.error(f"Failed to start dashboard: {e}")