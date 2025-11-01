// ARBitech Dashboard JavaScript

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
});