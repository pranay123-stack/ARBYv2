# ARBitech Telegram Bot Integration

A comprehensive Telegram bot integration for the ARBitech arbitrage trading platform, providing real-time notifications, interactive trade approval workflows, and complete trading management through Telegram.

## 🚀 Features

### Bot Commands & Interface

| Command | Description | Parameters |
|---------|-------------|------------|
| `/start` | Initialize bot and authentication | None |
| `/help` | Show available commands and usage | None |
| `/menu` | Open interactive main menu | None |
| `/opportunities` | View recent arbitrage opportunities | Limit (optional) |
| `/approve <trade_id>` | Approve a pending trade | Trade ID |
| `/reject <trade_id>` | Reject a pending trade | Trade ID |
| `/performance` | View trading performance metrics | None |
| `/status` | Check system status | None |
| `/settings` | Configure user preferences | None |
| `/alerts` | Manage notification alerts | None |
| `/logout` | Log out safely | None |

### Bot Features

- **Real-time Notifications**: Instant alerts for arbitrage opportunities with profit details
- **Interactive Approval**: Quick approve/reject buttons for trade decisions
- **Performance Analytics**: Comprehensive trading performance reports with charts
- **Multi-user Support**: Role-based access control (Admin, Trader, Viewer, Approver)
- **System Monitoring**: Real-time health checks and status updates
- **Conversation States**: Complex workflow management
- **Rate Limiting**: Built-in protection against spam and abuse
- **Error Handling**: Comprehensive error recovery and logging
- **Multimedia Support**: Charts, screenshots, and rich media notifications
- **Authentication**: Secure user verification and session management

### Integration
- **ARBitech Phases 3-8**: Seamless integration with all system components
- **Supabase Backend**: Full data persistence and real-time subscriptions
- **HITL System**: Human-in-the-loop approval workflows
- **Risk Management**: Automated risk alerts and monitoring
- **Audit Trail**: Complete logging of all bot interactions

## 📋 Table of Contents

1. [Installation](#installation)
2. [Configuration](#configuration)
3. [Usage](#usage)
4. [Bot Commands](#bot-commands)
5. [Integration Guide](#integration-guide)
6. [API Reference](#api-reference)
7. [Deployment](#deployment)
8. [Monitoring](#monitoring)
9. [Troubleshooting](#troubleshooting)

## 🛠 Installation

### Prerequisites

- Python 3.8+
- ARBitech system installed and configured
- Supabase project with required tables
- Telegram Bot Token from [@BotFather](https://t.me/BotFather)

### Step 1: Install Dependencies

```bash
cd /workspace/arbitech/notifications
pip install -r requirements.txt
```

### Step 2: Set Up Environment Variables

```bash
# Required
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_ANON_KEY="your_anon_key"
export SUPABASE_SERVICE_ROLE_KEY="your_service_role_key"

# Optional Configuration
export BOT_MODE="production"
export LOG_LEVEL="INFO"
export ENABLE_AUTO_APPROVAL="false"
export MAX_NOTIFICATIONS_PER_MINUTE="30"
```

### Step 3: Create Telegram Bot

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` command
3. Follow instructions to create your bot
4. Save the bot token provided
5. Set your bot token as `TELEGRAM_BOT_TOKEN` environment variable

## ⚙️ Configuration

### Configuration Files

The bot supports configuration through:

1. **Environment Variables** (Recommended for production)
2. **Configuration Files** (JSON/YAML)
3. **Python Configuration** (For development)

### Environment Variables

```bash
# Bot Configuration
TELEGRAM_BOT_TOKEN="123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
BOT_MODE="production"

# Supabase Integration
SUPABASE_URL="https://apailklayaphzswnxgya.supabase.co"
SUPABASE_ANON_KEY="your_anon_key"
SUPABASE_SERVICE_ROLE_KEY="your_service_key"

# Rate Limiting
DEFAULT_RATE_LIMIT="10"
MAX_NOTIFICATIONS_PER_MINUTE="30"
BURST_LIMIT="20"

# Feature Toggles
ENABLE_OPPORTUNITY_NOTIFICATIONS="true"
ENABLE_TRADE_APPROVALS="true"
ENABLE_PERFORMANCE_REPORTS="true"
ENABLE_AUTO_APPROVAL="false"

# User Management
ADMIN_CODES="ADMIN2024,TRADER2024,VIEW2024"
ALLOWED_USER_IDS="123456789,987654321"
```

### Configuration Classes

```python
from notifications.telegram_config import config_manager

# Load configuration
config_manager.load_from_environment()

# Access configurations
telegram_config = config_manager.telegram_config
notification_config = config_manager.notification_config
feature_config = config_manager.feature_config
integration_config = config_manager.integration_config

# Validate configuration
errors = config_manager.validate_all_configs(
    telegram_config, notification_config, feature_config, integration_config
)
```

## 🚀 Usage

### Basic Usage

```python
import asyncio
from notifications.telegram_bot import create_arbitech_bot

async def main():
    # Create bot with token from environment
    bot = create_arbitech_bot(os.getenv("TELEGRAM_BOT_TOKEN"))
    
    # Initialize bot
    await bot.initialize()
    
    # Run bot (blocking call)
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())
```

### Integration Example

```python
from notifications.telegram_bot import ARBITechTelegramBot
from storage.supabase_layer import SupabaseDataLayer
from storage.models import ArbitrageOpportunity, Sport

async def integrate_bot():
    # Initialize data layer
    data_layer = SupabaseDataLayer()
    
    # Create bot
    bot = ARBITechTelegramBot(token="your_token", data_layer=data_layer)
    await bot.initialize()
    
    # Create opportunity notification
    opportunity = ArbitrageOpportunity(
        sport=Sport.FOOTBALL,
        event_name="Liverpool vs Arsenal",
        profit_margin=Decimal("2.5"),
        total_stake=Decimal("1000.0")
    )
    
    # Send notification
    await bot.send_opportunity_alert(opportunity)
    
    # Run bot
    await bot.run()
```

### Demo Script

Run the complete demonstration:

```bash
cd /workspace/arbitech/notifications
python telegram_bot_example.py
```

This demo includes:
- Bot initialization and configuration
- Simulated opportunity detection
- Trade approval workflows
- Risk alerts
- Performance reporting
- Interactive testing mode

### Example Usage Flow

```
1. User sends /start
2. Bot sends welcome message
3. User authenticates with code (e.g., VIEW2024)
4. User can now use /menu to access features
5. User receives opportunity notifications in real-time
6. User can approve/reject trades via inline buttons
```

### Authentication Codes

- **ADMIN2024** - Full access to all features
- **TRADER2024** - Trading privileges (approve trades, view all data)
- **VIEW2024** - Read-only access (view opportunities and performance)

## 🤖 Bot Commands

### User Commands

| Command | Description | Parameters |
|---------|-------------|------------|
| `/start` | Initialize bot and authentication | None |
| `/help` | Show available commands and usage | None |
| `/menu` | Open interactive main menu | None |
| `/opportunities` | View recent arbitrage opportunities | Limit (optional) |
| `/approve <trade_id>` | Approve a pending trade | Trade ID |
| `/reject <trade_id>` | Reject a pending trade | Trade ID |
| `/performance` | View trading performance metrics | None |
| `/status` | Check system status | None |
| `/settings` | Configure user preferences | None |
| `/alerts` | Manage notification alerts | None |
| `/logout` | Log out safely | None |

### Inline Keyboard Actions

When viewing opportunities or pending trades:

- ✅ **Approve** - Approve the trade immediately
- ❌ **Reject** - Reject with confirmation
- 📊 **Details** - View detailed opportunity information

## 🔗 Integration Guide

### ARBitech System Integration

The bot integrates with all ARBitech phases:

#### Phase 3: Detection & Scanning
```python
from detection.opportunity_scanner import OpportunityScanner

scanner = OpportunityScanner()

# When new opportunity is detected
opportunities = await scanner.scan_markets()
for opp in opportunities:
    await bot.send_opportunity_alert(opp)
```

#### Phase 4: Risk Management
```python
from risk.risk_analyzer import RiskAnalyzer

analyzer = RiskAnalyzer()

# Send risk alerts
risk_result = analyzer.analyze_opportunity(opp)
if risk_result.severity == 'high':
    await bot.send_risk_alert({
        'alert_type': 'high_risk',
        'severity': 'high',
        'description': risk_result.description
    })
```

#### Phase 5: Browser Automation
```python
from automation.arbitrage_executor import ArbitrageExecutor

executor = ArbitrageExecutor()

# Update trade status
trade = await executor.execute_opportunity(opp)
await bot.send_trade_update(trade, "Trade Executed")
```

#### Phase 6: HITL Approval
```python
from hitl.approval_workflow import ApprovalWorkflow

workflow = ApprovalWorkflow()

# Process approval through bot
decision = await workflow.present_opportunity(opp)
await data_layer.log_hitl_decision(
    opportunity_id=opp.id,
    user_id=user_id,
    decision=decision.decision,
    source="telegram_bot"
)
```

### Supabase Integration

```python
from storage.supabase_layer import SupabaseDataLayer

data_layer = SupabaseDataLayer()

# Subscribe to real-time updates
async def handle_opportunity_update(opportunity):
    await bot.send_opportunity_alert(opportunity)

await data_layer.subscribe_to_opportunities(handle_opportunity_update)
```

### Custom Integrations

#### Custom Notification Handler

```python
class CustomBotHandler:
    def __init__(self, bot):
        self.bot = bot
    
    async def handle_custom_event(self, event_data):
        # Create custom notification
        notification = BotNotification(
            notification_id=str(uuid4()),
            user_id=event_data['user_id'],
            type=MessageType.NOTIFICATION,
            title=event_data['title'],
            content=event_data['message'],
            data=event_data,
            priority=NotificationPriority.HIGH,
            timestamp=datetime.utcnow()
        )
        
        await self.bot.notification_queue.put(notification)
```

## 📖 API Reference

### ARBITechTelegramBot Class

#### Methods

##### Initialization
```python
def __init__(self, token: str, data_layer: SupabaseDataLayer)
async def initialize() -> None
async def run() -> None
async def shutdown() -> None
```

##### User Management
```python
def _get_user_session(self, telegram_id: int) -> Optional[UserSession]
async def _start_authentication(self, update: Update, context: CallbackContext)
```

##### Notification Methods
```python
async def send_opportunity_alert(self, opportunity: ArbitrageOpportunity)
async def send_trade_update(self, trade: Trade, update_type: str)
async def send_risk_alert(self, alert_data: Dict[str, Any])
```

##### Command Handlers
```python
async def _cmd_start(self, update: Update, context: CallbackContext)
async def _cmd_menu(self, update: Update, context: CallbackContext)
async def _cmd_opportunities(self, update: Update, context: CallbackContext)
async def _cmd_performance(self, update: Update, context: CallbackContext)
```

### Data Models

#### UserSession
```python
@dataclass
class UserSession:
    user_id: str
    telegram_id: int
    username: str
    role: UserRole
    authorized: bool
    preferences: Dict[str, Any]
    current_opportunity_id: Optional[str]
    state: BotState
    last_activity: datetime
```

#### BotNotification
```python
@dataclass
class BotNotification:
    notification_id: str
    user_id: str
    type: MessageType
    title: str
    content: str
    data: Dict[str, Any]
    priority: NotificationPriority
    timestamp: datetime
    read: bool
    buttons: List[Dict[str, str]]
```

### Configuration Classes

#### TelegramConfig
```python
@dataclass
class TelegramConfig:
    bot_token: str
    mode: BotMode
    rate_limit_enabled: bool
    max_notifications_per_minute: int
    admin_codes: List[str]
```

#### NotificationConfig
```python
@dataclass
class NotificationConfig:
    telegram_enabled: bool
    use_emojis: bool
    min_profit_threshold: float
    max_stake_threshold: float
    allowed_risk_tiers: List[str]
```

## 🚀 Deployment

### Development Environment

```bash
# Clone and setup
git clone <repository>
cd arbitech/notifications

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export TELEGRAM_BOT_TOKEN="your_token"
export SUPABASE_URL="your_url"

# Run in development mode
export BOT_MODE="development"
python telegram_bot_example.py
```

### Production Deployment

#### 1. Environment Setup

```bash
# Production environment variables
export TELEGRAM_BOT_TOKEN="your_production_token"
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="your_service_key"
export BOT_MODE="production"
export LOG_LEVEL="INFO"
```

#### 2. Service Configuration

Create a systemd service file `/etc/systemd/system/arbitech-bot.service`:

```ini
[Unit]
Description=ARBitech Telegram Bot
After=network.target

[Service]
Type=simple
User=arbitech
WorkingDirectory=/opt/arbitech/notifications
Environment=TELEGRAM_BOT_TOKEN=your_token
ExecStart=/usr/bin/python3 /opt/arbitech/notifications/telegram_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 3. Start Service

```bash
# Enable and start service
sudo systemctl enable arbitech-bot
sudo systemctl start arbitech-bot
sudo systemctl status arbitech-bot

# View logs
sudo journalctl -u arbitech-bot -f
```

#### 4. Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8080

CMD ["python", "telegram_bot.py"]
```

```bash
# Build and run
docker build -t arbitech-bot .
docker run -d \
  --name arbitech-bot \
  -e TELEGRAM_BOT_TOKEN=your_token \
  -e SUPABASE_URL=your_url \
  arbitech-bot
```

### Cloud Deployment

#### AWS ECS

```json
{
  "family": "arbitech-bot",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::account:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "arbitech-bot",
      "image": "your-account.dkr.ecr.region.amazonaws.com/arbitech-bot:latest",
      "portMappings": [
        {
          "containerPort": 8080,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "TELEGRAM_BOT_TOKEN", "value": "your_token"},
        {"name": "SUPABASE_URL", "value": "your_url"}
      ]
    }
  ]
}
```

#### Google Cloud Run

```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: arbitech-bot
  annotations:
    run.googleapis.com/ingress: all
spec:
  template:
    metadata:
      annotations:
        run.googleapis.com/cpu-throttling: "false"
    spec:
      containerConcurrency: 80
      containers:
      - image: gcr.io/your-project/arbitech-bot:latest
        ports:
        - containerPort: 8080
        env:
        - name: TELEGRAM_BOT_TOKEN
          value: "your_token"
        - name: SUPABASE_URL
          value: "your_url"
        resources:
          limits:
            cpu: "500m"
            memory: "1Gi"
```

## 📊 Monitoring

### Health Checks

```python
# Check bot health
health = await bot.health_check()
print(f"Status: {health['status']}")
print(f"Active users: {health['active_users']}")
print(f"Queue size: {health['queue_size']}")
```

### Metrics

The bot tracks several key metrics:

- **Total messages sent**
- **Total notifications sent**
- **Active user sessions**
- **Error count and rate**
- **Queue size**
- **Response times**

### Logging

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/workspace/arbitech/logs/telegram_bot.log'),
        logging.StreamHandler()
    ]
)

# Log events
await bot.audit_logger.log_event(
    event_type="bot_connection",
    user_id=user_id,
    data={"telegram_id": telegram_id}
)
```

### Prometheus Metrics

```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
messages_sent = Counter('telegram_messages_sent_total', 'Total messages sent')
notifications_sent = Counter('telegram_notifications_sent_total', 'Total notifications sent')
active_users = Gauge('telegram_active_users', 'Number of active users')
error_count = Counter('telegram_errors_total', 'Total errors')

# Track metrics
messages_sent.inc()
active_users.set(len(bot.users))
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Bot Token Invalid

**Error**: `Invalid token`

**Solution**:
```python
# Verify token format
token = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
if not token.startswith(('1', '2')):
    raise ValueError("Invalid bot token format")
```

#### 2. Authentication Issues

**Error**: User cannot authenticate

**Solution**:
```bash
# Check admin codes
echo $ADMIN_CODES
# Should output: ADMIN2024,TRADER2024,VIEW2024

# Or verify in code
from notifications.telegram_config import config_manager
config_manager.load_from_environment()
print(config_manager.telegram_config.admin_codes)
```

#### 3. Supabase Connection

**Error**: Database connection failed

**Solution**:
```python
# Test connection
data_layer = SupabaseDataLayer()
health = await data_layer.health_check()
print(f"Database connected: {health}")

# Check environment variables
import os
print(f"SUPABASE_URL: {os.getenv('SUPABASE_URL')}")
print(f"SUPABASE_ANON_KEY: {os.getenv('SUPABASE_ANON_KEY')[:10]}...")
```

#### 4. Rate Limiting

**Error**: Rate limit exceeded

**Solution**:
```python
# Check rate limits
user_id = update.effective_user.id
allowed = bot._check_rate_limit(user_id, "opportunities")
print(f"Rate limit check: {allowed}")

# Adjust rate limits in config
from notifications.telegram_config import config_manager
config_manager.notification_config.max_notifications_per_minute = 50
```

#### 5. Notification Queue Full

**Error**: Queue is full, notifications dropped

**Solution**:
```python
# Check queue size
queue_size = bot.notification_queue.qsize()
print(f"Queue size: {queue_size}")

# Increase queue size
bot.notification_queue = asyncio.Queue(maxsize=2000)

# Process queue manually
while not bot.notification_queue.empty():
    notification = await bot.notification_queue.get()
    await bot._send_notification(notification)
```

### Debug Mode

Enable debug mode for detailed logging:

```bash
export DEBUG_MODE="true"
export LOG_LEVEL="DEBUG"
python telegram_bot.py
```

### Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/test_telegram_bot.py -v

# Run with coverage
pytest tests/ --cov=notifications.telegram_bot --cov-report=html
```

### Log Analysis

```bash
# View recent logs
tail -f /workspace/arbitech/logs/telegram_bot.log

# Search for errors
grep "ERROR" /workspace/arbitech/logs/telegram_bot.log

# Count messages by user
grep "bot_connection" /workspace/arbitech/logs/telegram_bot.log | wc -l
```

## 🤝 Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Install development dependencies
4. Make your changes
5. Run tests and linting
6. Submit a pull request

### Code Style

```bash
# Format code
black notifications/
isort notifications/

# Lint code
flake8 notifications/
```

### Testing Guidelines

- Write tests for all new features
- Include integration tests
- Test error handling paths
- Mock external dependencies

## 📄 File Structure

```
notifications/
├── telegram_bot.py              # Main bot implementation
├── telegram_config.py           # Configuration management
├── telegram_bot_example.py      # Demo and usage examples
├── requirements.txt             # Dependencies
├── README.md                    # This documentation
├── __init__.py                  # Module exports
├── multi_channel_delivery.py    # Legacy multi-channel system
├── config_examples.py           # Configuration examples
├── demo.py                      # Legacy demo script
├── example_integration.py       # Legacy integration examples
└── notification_filters.py      # Legacy filtering system
```

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For support and questions:

1. Check the troubleshooting section above
2. Review the logs for error details
3. Run the demo script to test integration
4. Check the GitHub issues page
5. Contact the ARBitech development team

## 🔄 Changelog

### Version 1.0.0

**Features**:
- Complete Telegram bot integration
- Real-time opportunity notifications
- Interactive trade approval workflows
- Performance reporting with charts
- Multi-user authentication and roles
- Comprehensive error handling and logging
- Rate limiting and spam protection
- Integration with all ARBitech phases 3-8

**Integration**:
- Supabase data layer
- HITL approval workflows
- Risk management system
- Scanner and detector components
- Audit logging

**Deployment**:
- Production-ready configuration
- Docker support
- Cloud deployment guides
- Systemd service configuration

---

Built with ❤️ for the ARBitech arbitrage trading platform.
