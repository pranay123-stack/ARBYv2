# ARBitech Automation System - Framework & Architecture Plan

## Executive Summary

**Project:** ARBitech - Autonomous Arbitrage Betting Agent with Vision-Based Chrome Tab Interaction  
**Platform:** DeepAgent on Abacus.AI ChatLLM  
**Version:** 2.0 (VLM-Enhanced)  
**Last Updated:** October 8, 2025

### Vision

ARBitech is an intelligent, autonomous arbitrage betting agent that leverages Vision Language Models (VLM) and browser automation to detect and execute risk-free arbitrage opportunities across global betting exchanges. The system operates exclusively through the AVO Tabs Chrome extension, providing a secure, controlled environment for automated trade execution with comprehensive risk management.

### Core Objectives

1. **Autonomous Operation:** Transition from HITL (Human-In-The-Loop) manual execution to fully autonomous trading based on configurable risk parameters
2. **100% AVO.bets Scanner Integration:** Direct visual interaction with AVO.bets scanner UI using VLM technology
3. **Multi-Exchange Coverage:** Support for centralized exchanges (Betfair, Pinnacle), P2P networks (BetDex, Aver), and casino applications
4. **Risk-First Approach:** All trades limited to risk-free arbitrage opportunities (A-grade trades only in autonomous mode)
5. **Cloud Architecture:** Leveraging Supabase for authentication, data persistence, and real-time synchronization
6. **Existing UI Integration:** Seamless integration with deployed dashboard at https://apps.abacus.ai/chatllm/?appId=3cb1afd5a&convoId=11d1c6aaed

### Key Differentiators

- **Vision-First Architecture:** VLM (Qwen-VL or equivalent) for reading and interacting with dynamic betting interfaces
- **Chrome Extension Constraint:** Exclusive operation through AVO Tabs for security and validation
- **Hybrid Data Strategy:** API calls for structured data, VLM for unstructured UI elements
- **DeepAgent Native:** Built specifically for DeepAgent's GUI automation and tool ecosystem

---

## System Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          USER CONTROL LAYER                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐  │
│  │  Existing UI     │  │  Configuration   │  │  Notification Hub    │  │
│  │  (Abacus.AI)     │◄─┤  Dashboard       │◄─┤  (Telegram/Email)   │  │
│  └────────┬─────────┘  └────────┬─────────┘  └──────────────────────┘  │
└───────────┼────────────────────┼──────────────────────────────────────┘
            │                    │
            ▼                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       ORCHESTRATION LAYER                                │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │               DeepAgent Core (LangGraph Orchestrator)            │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │  │
│  │  │ State       │  │ Workflow    │  │ Mode Controller         │  │  │
│  │  │ Manager     │  │ Engine      │  │ (HITL/Autonomous)       │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└───────────┬──────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         INTELLIGENCE LAYER                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │ VLM Agent    │  │ Arbitrage    │  │ Risk Engine  │  │ Validation │ │
│  │ (Vision)     │◄─┤ Detector     │◄─┤ (Rules)      │◄─┤ Module     │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └────────────┘ │
└─────────┼──────────────────┼──────────────────┼────────────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          EXECUTION LAYER                                 │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │              Playwright Browser Automation                        │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────────────────┐  │  │
│  │  │ Chrome      │  │ Tab         │  │ AVO Extension            │  │  │
│  │  │ Controller  │◄─┤ Manager     │◄─┤ Interface                │  │  │
│  │  └─────────────┘  └─────────────┘  └──────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└───────────┬──────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           DATA LAYER                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │ Supabase     │  │ API Sources  │  │ P2P Networks │  │ Log Store  │ │
│  │ (Auth + DB)  │  │ (Betfair)    │  │ (BetDex)     │  │ (Audit)    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

### Architecture Layers

#### 1. User Control Layer
- **Existing UI:** Abacus.AI hosted dashboard (no rebuild required)
- **Configuration Dashboard:** Parameter management interface
- **Notification Hub:** Multi-channel alerting system

#### 2. Orchestration Layer (DeepAgent Core)
- **State Manager:** Maintains agent state, user preferences, and active trades
- **Workflow Engine:** LangGraph-based state machine for decision flows
- **Mode Controller:** Manages HITL ↔ Autonomous mode transitions

#### 3. Intelligence Layer
- **VLM Agent:** Vision-based UI interpretation and interaction
- **Arbitrage Detector:** Mathematical opportunity identification
- **Risk Engine:** Rule-based safety validation
- **Validation Module:** Pre-execution verification

#### 4. Execution Layer
- **Playwright Automation:** Chrome browser control
- **Tab Manager:** AVO Tabs extension coordination
- **Extension Interface:** Direct communication with AVO.bets scanner

#### 5. Data Layer
- **Supabase:** Primary data store with auth and real-time sync
- **API Sources:** Direct exchange integrations
- **P2P Networks:** Decentralized exchange connectors
- **Log Store:** Comprehensive audit trail

---

## Component Breakdown

### 1. DeepAgent Core Orchestrator

**Purpose:** Central brain coordinating all system components

**Technology Stack:**
- LangGraph for state machine orchestration
- Python 3.11+ runtime
- AsyncIO for concurrent operations
- Redis for in-memory state (optional)

**Key Responsibilities:**
- Workflow state management
- Component coordination
- Error handling and recovery
- Mode switching (HITL ↔ Autonomous)

**Implementation Details:**

```python
# Conceptual State Machine
class ARBitechState:
    - mode: Literal["HITL", "AUTONOMOUS", "ARMED"]
    - active_scans: List[ScanSession]
    - pending_trades: List[Trade]
    - risk_config: RiskConfig
    - user_approval_queue: List[TradeRequest]
```

**State Transitions:**
```
IDLE ──[user_arms]──> ARMED ──[scan_complete]──> OPPORTUNITY_DETECTED
                                                         │
                          ┌──────────────────────────────┴──────────────┐
                          ▼                                             ▼
                    [HITL_MODE]                                  [AUTO_MODE]
                          │                                             │
                          ▼                                             ▼
              USER_APPROVAL_REQUIRED                        RISK_VALIDATION
                          │                                             │
                          ▼                                             ▼
                  EXECUTE_TRADE ◄───────────────────────────────► EXECUTE_TRADE
                          │                                             │
                          └──────────────────┬──────────────────────────┘
                                             ▼
                                      LOG_AND_NOTIFY
                                             ▼
                                      RETURN_TO_SCAN
```

---

### 2. VLM Agent (Vision Language Model)

**Purpose:** Visual interpretation and interaction with dynamic UIs

**Technology Options:**
1. **Qwen-VL** (Recommended): Open-source, fast, good OCR
2. **GPT-4V** (Fallback): Higher accuracy, API-based
3. **LLaVA**: Local deployment option

**Core Capabilities:**
- Screenshot analysis and element detection
- Text extraction from betting interfaces
- Button/input field identification
- Odds value parsing
- Dynamic UI change detection

**Integration Pattern:**

```python
# VLM Task Flow
1. Take screenshot of AVO scanner or tab
2. Send to VLM with structured prompt:
   "Identify all betting opportunities with odds > 1.5. 
    Return JSON: [{sport, event, bookmaker, odds, stake_input_coords}]"
3. Parse VLM response
4. Validate coordinates with safety bounds
5. Execute Playwright actions
```

**DeepAgent Integration:**
- Use `gui` tool for screenshots
- Use `analyze_image` tool for VLM processing
- Cache VLM responses for 5-10 seconds (UI changes slowly)

**Safety Measures:**
- Bounding box validation (ensure clicks within tab boundaries)
- OCR confidence thresholds (>85% for numeric values)
- Fallback to manual mode on repeated VLM failures

---

### 3. AVO.bets Scanner Interface Module

**Purpose:** Direct interaction with AVO.bets scanner UI and Chrome extension

**Key Features:**
- Tab identification and validation
- Scanner state monitoring
- Multi-link opening mode coordination
- Tab preset management

**Implementation Components:**

#### A. Tab Validator
```python
def validate_avo_tab(tab_url: str, tab_title: str) -> bool:
    """Ensure tab is AVO-managed"""
    - Check URL matches AVO-generated patterns
    - Verify extension injection markers
    - Validate tab metadata
```

#### B. Scanner State Monitor
```python
def monitor_scanner_state() -> ScannerState:
    """Real-time scanner status"""
    - Screenshot AVO scanner UI
    - VLM parse for active scans
    - Extract opportunity count
    - Identify active filters
```

#### C. Tab Preset Manager
```python
def apply_tab_preset(preset_name: str) -> List[Tab]:
    """Load predefined tab configurations"""
    - Invoke AVO extension API
    - Open bookmaker tabs per preset
    - Wait for tab initialization
    - Return tab references
```

**Browser Automation Strategy:**

```javascript
// Chrome Extension Interaction (Playwright context)
// Inject to communicate with AVO Tabs

window.addEventListener('AVO_TAB_READY', (event) => {
    // Tab fully loaded and AVO-injected
    window.postMessage({
        type: 'ARBITECH_READY',
        tabId: event.detail.tabId
    });
});

// Query AVO state
const avoState = await page.evaluate(() => {
    return window.AVO?.getState();
});
```

**AVO Extension API Hooks:**
- Multi-link opening: `AVO.openLinks(urls[])`
- Tab search: `AVO.searchBet(query)`
- Preset loading: `AVO.loadPreset(id)`
- State query: `AVO.getActiveScans()`

---

### 4. Risk Management Engine

**Purpose:** Enforce safety rules and prevent losses

**Risk Tiers:**

```
┌─────────────────────────────────────────────────────┐
│  Risk Tier    │  Mode Allowed  │  Conditions        │
├───────────────┼────────────────┼────────────────────┤
│  A (Risk-Free)│  HITL + AUTO   │  Guaranteed profit │
│  B (Low Risk) │  HITL only     │  >95% probability  │
│  C (Medium)   │  HITL + manual │  >80% probability  │
│  D (High)     │  DISABLED      │  Never execute     │
└─────────────────────────────────────────────────────┘
```

**Configuration Parameters:**

```yaml
risk_config:
  # Tier A (Autonomous Allowed)
  tier_a:
    min_profit_percentage: 0.5    # Minimum 0.5% guaranteed profit
    max_stake_per_trade: 500      # USD equivalent
    max_stake_percentage: 5       # % of total bankroll
    min_liquidity: 1000           # Minimum available liquidity
    
  # Tier B (HITL Required)
  tier_b:
    min_profit_percentage: 1.5
    max_stake_per_trade: 200
    require_user_approval: true
    
  # Global Limits
  global:
    max_daily_stake: 5000
    max_concurrent_trades: 3
    blacklist_bookmakers: []
    whitelist_sports: ["soccer", "basketball", "tennis"]
    
  # Failsafes
  failsafe:
    max_consecutive_losses: 2     # Pause after 2 losses
    cooldown_period_minutes: 30
    emergency_stop_loss: 1000     # Stop if daily loss exceeds
```

**Risk Validation Logic:**

```python
def validate_trade_risk(opportunity: ArbitrageOpportunity) -> RiskAssessment:
    """Multi-stage risk validation"""
    
    # Stage 1: Mathematical Validation
    implied_probabilities = [1/odd for odd in opportunity.odds]
    total_probability = sum(implied_probabilities)
    
    if total_probability >= 1.0:
        return RiskAssessment(tier="D", reason="No arbitrage exists")
    
    profit_margin = (1 / total_probability - 1) * 100
    
    # Stage 2: Liquidity Check
    if opportunity.available_stake < config.tier_a.min_liquidity:
        return RiskAssessment(tier="C", reason="Low liquidity")
    
    # Stage 3: Stake Calculation
    kelly_stakes = calculate_kelly_stakes(opportunity)
    if max(kelly_stakes) > config.tier_a.max_stake_per_trade:
        return RiskAssessment(tier="B", reason="Stake too high")
    
    # Stage 4: Bankroll Check
    current_bankroll = get_current_bankroll()
    if sum(kelly_stakes) > current_bankroll * (config.tier_a.max_stake_percentage / 100):
        return RiskAssessment(tier="B", reason="Bankroll limit")
    
    # Stage 5: Historical Performance
    bookmaker_reliability = check_bookmaker_history(opportunity.bookmakers)
    if bookmaker_reliability < 0.95:
        return RiskAssessment(tier="B", reason="Bookmaker reliability")
    
    # Tier A: All checks passed
    return RiskAssessment(
        tier="A",
        profit_margin=profit_margin,
        recommended_stakes=kelly_stakes,
        approved_for_auto=True
    )
```

**Emergency Protocols:**
- **Circuit Breaker:** Auto-pause after anomalies
- **Loss Limit:** Daily/weekly caps
- **Velocity Check:** Flag rapid repeated trades
- **Balance Reconciliation:** Verify wallet/account balances every 15 minutes

---

### 5. Data Storage & Supabase Integration

**Purpose:** Persistent, real-time data management with authentication

**Supabase Architecture:**

```
┌─────────────────────────────────────────────────────────┐
│                    Supabase Project                      │
│  ┌────────────────────────────────────────────────────┐ │
│  │  PostgreSQL Database (Primary Store)               │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │ │
│  │  │ Users/Auth   │  │ Trades       │  │ Config   │ │ │
│  │  └──────────────┘  └──────────────┘  └──────────┘ │ │
│  └────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Realtime (WebSocket subscriptions)                │ │
│  └────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Auth (User management & RLS)                      │ │
│  └────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Storage (Logs, screenshots, reports)              │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

**Database Schema:**

```sql
-- Users Table (managed by Supabase Auth)
CREATE TABLE public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id),
    email TEXT UNIQUE NOT NULL,
    subscription_tier TEXT CHECK (subscription_tier IN ('free', 'pro', 'enterprise')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ,
    metadata JSONB
);

-- Risk Configuration Table
CREATE TABLE public.risk_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    config_name TEXT NOT NULL,
    is_active BOOLEAN DEFAULT false,
    
    -- Tier A Settings
    tier_a_min_profit_pct DECIMAL(5,2) DEFAULT 0.5,
    tier_a_max_stake DECIMAL(10,2) DEFAULT 500,
    tier_a_max_stake_pct DECIMAL(5,2) DEFAULT 5,
    tier_a_min_liquidity DECIMAL(10,2) DEFAULT 1000,
    
    -- Global Limits
    max_daily_stake DECIMAL(10,2) DEFAULT 5000,
    max_concurrent_trades INT DEFAULT 3,
    
    -- Filters
    whitelist_sports TEXT[],
    blacklist_bookmakers TEXT[],
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(user_id, config_name)
);

-- Trades Table
CREATE TABLE public.trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    
    -- Trade Details
    sport TEXT NOT NULL,
    event_name TEXT NOT NULL,
    trade_type TEXT CHECK (trade_type IN ('arbitrage', 'value_bet', 'scalp')),
    risk_tier TEXT CHECK (risk_tier IN ('A', 'B', 'C', 'D')),
    
    -- Legs (JSON array of bet placements)
    legs JSONB NOT NULL,
    -- Example: [{"bookmaker": "Betfair", "selection": "Team A", "odds": 2.1, "stake": 100}]
    
    -- Financial
    total_stake DECIMAL(10,2) NOT NULL,
    expected_profit DECIMAL(10,2) NOT NULL,
    actual_profit DECIMAL(10,2),
    profit_margin_pct DECIMAL(5,2),
    
    -- Status
    status TEXT CHECK (status IN ('pending', 'placed', 'partially_placed', 'won', 'lost', 'void')) DEFAULT 'pending',
    execution_mode TEXT CHECK (execution_mode IN ('HITL', 'AUTONOMOUS')),
    
    -- Timestamps
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    executed_at TIMESTAMPTZ,
    settled_at TIMESTAMPTZ,
    
    -- Metadata
    scanner_source TEXT,
    avo_tab_ids TEXT[],
    screenshot_url TEXT,
    notes TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Scan Sessions Table
CREATE TABLE public.scan_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    
    session_start TIMESTAMPTZ DEFAULT NOW(),
    session_end TIMESTAMPTZ,
    
    opportunities_detected INT DEFAULT 0,
    trades_executed INT DEFAULT 0,
    total_profit DECIMAL(10,2) DEFAULT 0,
    
    scan_config JSONB,
    status TEXT CHECK (status IN ('active', 'completed', 'failed', 'stopped')),
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bookmaker Accounts Table
CREATE TABLE public.bookmaker_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    
    bookmaker_name TEXT NOT NULL,
    username TEXT,
    balance DECIMAL(10,2),
    currency TEXT DEFAULT 'USD',
    
    is_active BOOLEAN DEFAULT true,
    last_synced TIMESTAMPTZ,
    
    credentials_encrypted TEXT, -- Encrypted storage
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(user_id, bookmaker_name)
);

-- Notifications Queue Table
CREATE TABLE public.notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    
    notification_type TEXT CHECK (notification_type IN ('opportunity', 'trade_placed', 'trade_settled', 'error', 'system')),
    priority TEXT CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    data JSONB,
    
    channels TEXT[], -- ['telegram', 'email', 'dashboard']
    sent_at TIMESTAMPTZ,
    read_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audit Logs Table
CREATE TABLE public.audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    
    action TEXT NOT NULL,
    entity_type TEXT, -- 'trade', 'config', 'session'
    entity_id UUID,
    
    old_values JSONB,
    new_values JSONB,
    
    ip_address INET,
    user_agent TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for Performance
CREATE INDEX idx_trades_user_created ON public.trades(user_id, created_at DESC);
CREATE INDEX idx_trades_status ON public.trades(status);
CREATE INDEX idx_trades_risk_tier ON public.trades(risk_tier);
CREATE INDEX idx_notifications_user_unread ON public.notifications(user_id, read_at) WHERE read_at IS NULL;
CREATE INDEX idx_audit_logs_user_created ON public.audit_logs(user_id, created_at DESC);

-- Row Level Security (RLS)
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.risk_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.trades ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scan_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bookmaker_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;

-- RLS Policies (Example for trades table)
CREATE POLICY "Users can view own trades"
    ON public.trades FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own trades"
    ON public.trades FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own trades"
    ON public.trades FOR UPDATE
    USING (auth.uid() = user_id);
```

**Supabase Client Integration (Python):**

```python
from supabase import create_client, Client

class SupabaseManager:
    def __init__(self, url: str, key: str):
        self.client: Client = create_client(url, key)
    
    async def log_trade(self, user_id: str, trade_data: dict):
        """Insert new trade record"""
        response = self.client.table('trades').insert({
            'user_id': user_id,
            **trade_data
        }).execute()
        return response.data[0]
    
    async def get_active_risk_config(self, user_id: str):
        """Fetch user's active risk configuration"""
        response = self.client.table('risk_configs').select('*').eq(
            'user_id', user_id
        ).eq('is_active', True).execute()
        return response.data[0] if response.data else None
    
    async def subscribe_to_trades(self, user_id: str, callback):
        """Real-time trade updates"""
        self.client.table('trades').on('INSERT', callback).filter(
            'user_id', 'eq', user_id
        ).subscribe()
```

**Alternative: Airtable Integration**

If Airtable is preferred for non-technical users:

```python
from pyairtable import Api

class AirtableManager:
    def __init__(self, api_key: str, base_id: str):
        self.api = Api(api_key)
        self.base = self.api.base(base_id)
        
    def log_trade(self, trade_data: dict):
        trades_table = self.base.table('Trades')
        return trades_table.create(trade_data)
    
    def get_risk_config(self):
        config_table = self.base.table('Risk_Config')
        records = config_table.all(formula='{Active} = TRUE()')
        return records[0]['fields'] if records else None
```

**Data Flow:**
1. Agent detects opportunity → Insert to `scan_sessions`
2. Risk validation → Read `risk_configs`
3. User approves (HITL) → Update `trades.status`
4. Execution complete → Update `trades.executed_at`, insert `audit_logs`
5. Settlement → Update `trades.settled_at`, `actual_profit`
6. Dashboard → Real-time subscription to `trades` table

---

### 6. Notification System

**Purpose:** Multi-channel alerting for opportunities and trade events

**Supported Channels:**

```
┌─────────────────────────────────────────────────┐
│  Channel    │  Use Case           │  Priority   │
├─────────────┼─────────────────────┼─────────────┤
│  Telegram   │  Real-time alerts   │  High/Crit  │
│  Email      │  Daily summaries    │  Low/Medium │
│  Dashboard  │  In-app toasts      │  All        │
│  SMS        │  Critical failures  │  Critical   │
│  Webhook    │  External integr.   │  All        │
└─────────────────────────────────────────────────┘
```

**Notification Types:**

```python
class NotificationType(Enum):
    OPPORTUNITY_DETECTED = "opportunity"      # New arb found
    TRADE_PLACED = "trade_placed"            # Bet executed
    TRADE_SETTLED = "trade_settled"          # Result confirmed
    USER_APPROVAL_REQUIRED = "approval_req"  # HITL prompt
    ERROR_OCCURRED = "error"                 # System failure
    DAILY_SUMMARY = "summary"                # Performance report
    RISK_ALERT = "risk_alert"                # Threshold breached
    BALANCE_LOW = "balance_low"              # Bankroll warning
```

**Telegram Bot Integration:**

```python
import asyncio
from telegram import Bot

class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot = Bot(token=bot_token)
        self.chat_id = chat_id
    
    async def send_opportunity_alert(self, opportunity: dict):
        """Send formatted arbitrage opportunity"""
        message = f"""
🎯 **New Arbitrage Opportunity**

**Sport:** {opportunity['sport']}
**Event:** {opportunity['event_name']}
**Profit Margin:** {opportunity['profit_margin']:.2f}%
**Risk Tier:** {opportunity['risk_tier']}

**Legs:**
{self._format_legs(opportunity['legs'])}

**Action Required:** {'AUTO-EXECUTING' if opportunity['risk_tier'] == 'A' else 'Approve in dashboard'}
        """
        await self.bot.send_message(
            chat_id=self.chat_id,
            text=message,
            parse_mode='Markdown'
        )
    
    async def send_trade_result(self, trade: dict):
        """Send trade settlement notification"""
        emoji = "✅" if trade['actual_profit'] > 0 else "❌"
        message = f"""
{emoji} **Trade Settled**

**Event:** {trade['event_name']}
**Profit:** ${trade['actual_profit']:.2f}
**ROI:** {(trade['actual_profit']/trade['total_stake']*100):.2f}%

**Session Totals:**
- Trades: {trade['session_trades']}
- Profit: ${trade['session_profit']:.2f}
        """
        await self.bot.send_message(chat_id=self.chat_id, text=message)
```

**Email Notifications (Daily Summary):**

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailNotifier:
    def __init__(self, smtp_config: dict):
        self.config = smtp_config
    
    def send_daily_summary(self, user_email: str, summary: dict):
        """Send HTML email with performance summary"""
        html_content = f"""
        <html>
        <body>
            <h2>ARBitech Daily Summary - {summary['date']}</h2>
            <table>
                <tr><td>Total Trades:</td><td>{summary['total_trades']}</td></tr>
                <tr><td>Win Rate:</td><td>{summary['win_rate']:.1f}%</td></tr>
                <tr><td>Total Profit:</td><td>${summary['total_profit']:.2f}</td></tr>
                <tr><td>Average ROI:</td><td>{summary['avg_roi']:.2f}%</td></tr>
            </table>
            
            <h3>Top Performing Sports:</h3>
            <ul>
                {''.join([f"<li>{s['name']}: ${s['profit']:.2f}</li>" for s in summary['top_sports']])}
            </ul>
            
            <p><a href="https://apps.abacus.ai/chatllm/?appId=3cb1afd5a">View Full Dashboard</a></p>
        </body>
        </html>
        """
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"ARBitech Daily Summary - ${summary['total_profit']:.2f} Profit"
        msg['From'] = self.config['from_email']
        msg['To'] = user_email
        
        msg.attach(MIMEText(html_content, 'html'))
        
        with smtplib.SMTP(self.config['smtp_host'], self.config['smtp_port']) as server:
            server.starttls()
            server.login(self.config['username'], self.config['password'])
            server.send_message(msg)
```

**Dashboard Toast Notifications:**

```javascript
// Frontend Integration (existing UI)
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY)

// Subscribe to notifications
supabase
  .channel('notifications')
  .on('postgres_changes', 
      { event: 'INSERT', schema: 'public', table: 'notifications' },
      (payload) => {
          const notification = payload.new
          
          // Show toast based on priority
          if (notification.priority === 'critical') {
              showCriticalAlert(notification.title, notification.message)
          } else {
              showToast(notification.title, notification.message)
          }
      }
  )
  .subscribe()
```

**Notification Filtering:**

```python
class NotificationManager:
    def __init__(self, supabase_client, user_preferences):
        self.db = supabase_client
        self.preferences = user_preferences
    
    async def send(self, notification: dict):
        """Smart notification routing"""
        # Check user preferences
        if not self._should_notify(notification):
            return
        
        # Route to appropriate channels
        channels = self._determine_channels(notification)
        
        tasks = []
        if 'telegram' in channels:
            tasks.append(self._send_telegram(notification))
        if 'email' in channels:
            tasks.append(self._send_email(notification))
        if 'dashboard' in channels:
            tasks.append(self._send_dashboard(notification))
        
        await asyncio.gather(*tasks)
        
        # Log to database
        await self.db.table('notifications').insert({
            'user_id': notification['user_id'],
            'notification_type': notification['type'],
            'priority': notification['priority'],
            'title': notification['title'],
            'message': notification['message'],
            'channels': channels
        }).execute()
    
    def _determine_channels(self, notification: dict) -> List[str]:
        """Route based on priority and user preferences"""
        priority = notification['priority']
        
        if priority == 'critical':
            return ['telegram', 'email', 'dashboard', 'sms']
        elif priority == 'high':
            return ['telegram', 'dashboard']
        elif priority == 'medium':
            return ['dashboard', 'email']
        else:
            return ['dashboard']
```

---

## Technology Stack

### Core Technologies

```yaml
# Language & Runtime
primary_language: Python 3.11+
async_framework: AsyncIO
state_management: LangGraph

# Browser Automation
browser_automation: Playwright
browser_target: Chrome (with AVO Tabs extension)
headless_mode: False (GUI required for extension)

# Vision & Intelligence
vlm_model: Qwen-VL / GPT-4V (fallback)
llm_orchestration: DeepAgent native tools
image_processing: PIL, OpenCV

# Data & Storage
primary_database: Supabase (PostgreSQL)
alternative_database: Airtable
caching: Redis (optional)
file_storage: Supabase Storage / S3

# Authentication
auth_provider: Supabase Auth
auth_methods: [email, oauth_google, oauth_github]

# Notifications
telegram: python-telegram-bot
email: smtplib / SendGrid
webhooks: FastAPI endpoints

# API Integrations
betfair_api: betfairlightweight
odds_aggregation: custom_scrapers + VLM
p2p_networks: web3.py (for Solana/Ethereum)

# Monitoring & Logging
logging: structlog
monitoring: Sentry (error tracking)
metrics: Prometheus + Grafana (optional)

# Deployment
platform: DeepAgent (Abacus.AI)
environment: Linux (Ubuntu)
display: X11 (for GUI automation)
```

### Python Dependencies

```txt
# Core
python>=3.11
langgraph>=0.2.0
langchain>=0.1.0
asyncio-mqtt>=0.16.0

# Browser & GUI
playwright>=1.40.0
pyautogui>=0.9.54
opencv-python>=4.8.0
pillow>=10.0.0

# Vision Models
transformers>=4.35.0
torch>=2.1.0
qwen-vl-utils>=0.1.0

# Data & Storage
supabase>=2.0.0
pyairtable>=2.1.0
redis>=5.0.0
sqlalchemy>=2.0.0

# API Clients
betfairlightweight>=2.18.0
requests>=2.31.0
httpx>=0.25.0
web3>=6.11.0

# Notifications
python-telegram-bot>=20.6
sendgrid>=6.10.0

# Utilities
pydantic>=2.4.0
python-dotenv>=1.0.0
structlog>=23.2.0
sentry-sdk>=1.38.0

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-playwright>=0.4.3
```

### DeepAgent-Specific Tools Usage

```python
# Tool utilization mapping
DEEPAGENT_TOOLS = {
    "gui": {
        "usage": "Primary interface for browser automation",
        "actions": ["screenshot", "left_click", "type", "scroll", "wait"],
        "frequency": "Every interaction with AVO Tabs"
    },
    "analyze_image": {
        "usage": "VLM processing of scanner screenshots",
        "actions": ["OCR", "element_detection", "odds_parsing"],
        "frequency": "Per scan cycle (every 10-30 seconds)"
    },
    "bash": {
        "usage": "System commands, process management",
        "actions": ["install_dependencies", "manage_chrome_profiles", "log_rotation"],
        "frequency": "Setup and maintenance"
    },
    "file_read/write": {
        "usage": "Configuration, logs, data persistence",
        "actions": ["load_config", "save_logs", "cache_data"],
        "frequency": "Initialization and continuous"
    },
    "web_search": {
        "usage": "Research bookmaker APIs, verify odds",
        "actions": ["api_documentation", "odds_verification"],
        "frequency": "As needed"
    }
}
```

---

## Operational Modes

### Mode Overview

```
┌──────────────────────────────────────────────────────────────┐
│                   OPERATIONAL MODE STATES                     │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│   [IDLE] ──user_arms──> [ARMED] ──scan_start──> [SCANNING]  │
│                            │                          │       │
│                            │                          ▼       │
│                            │                   [OPPORTUNITY]  │
│                            │                          │       │
│                            │         ┌────────────────┴───┐  │
│                            │         ▼                    ▼  │
│                            │    [HITL_MODE]        [AUTO_MODE]│
│                            │         │                    │  │
│                            │         ▼                    ▼  │
│                            │   [AWAIT_APPROVAL]  [AUTO_EXECUTE]│
│                            │         │                    │  │
│                            │         └────────┬───────────┘  │
│                            │                  ▼              │
│                            └───────────> [EXECUTING]         │
│                                              │               │
│                                              ▼               │
│                           ┌──────────── [COMPLETE] ─────┐   │
│                           │                              │   │
│                           ▼                              ▼   │
│                      [LOG_RESULT]                  [NOTIFY]  │
│                           │                              │   │
│                           └──────────┬───────────────────┘   │
│                                      ▼                       │
│                             [RETURN_TO_SCANNING]             │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 1. HITL Mode (Human-In-The-Loop)

**Purpose:** Manual execution with agent assistance

**Workflow:**
1. Agent scans and detects opportunities
2. Presents opportunities to user via dashboard + notification
3. User reviews and approves/rejects
4. Agent executes approved trades
5. Logs results and awaits next scan

**UI Interaction:**

```javascript
// Dashboard Component (React/Vue)
function OpportunityCard({ opportunity, onApprove, onReject }) {
    return (
        <div className="opportunity-card">
            <h3>{opportunity.sport} - {opportunity.event_name}</h3>
            <div className="odds-grid">
                {opportunity.legs.map(leg => (
                    <div className="leg">
                        <span>{leg.bookmaker}</span>
                        <span className="odds">{leg.odds}</span>
                        <span className="stake">${leg.recommended_stake}</span>
                    </div>
                ))}
            </div>
            <div className="metrics">
                <span>Profit: ${opportunity.expected_profit}</span>
                <span>Margin: {opportunity.profit_margin}%</span>
                <span className={`risk-tier-${opportunity.risk_tier}`}>
                    Tier {opportunity.risk_tier}
                </span>
            </div>
            <div className="actions">
                <button onClick={() => onApprove(opportunity.id)}>
                    ✅ Approve & Execute
                </button>
                <button onClick={() => onReject(opportunity.id)}>
                    ❌ Reject
                </button>
            </div>
        </div>
    )
}
```

**Agent Behavior:**
- Pauses after presenting opportunity
- Sets timeout (e.g., 60 seconds) for user response
- If timeout expires, marks opportunity as "expired"
- Continues scanning while awaiting approval

### 2. Armed Mode

**Purpose:** Ready state between idle and autonomous

**Characteristics:**
- System initialized and connected
- Chrome with AVO Tabs loaded
- Risk configuration validated
- Scanning inactive, awaiting trigger

**Activation:**
```python
def arm_system(user_id: str, config_id: str):
    """Arm the agent for operation"""
    # Load risk configuration
    risk_config = load_risk_config(user_id, config_id)
    
    # Initialize browser with AVO Tabs
    browser = launch_chrome_with_avo()
    
    # Validate tab presets
    validate_avo_tabs(browser)
    
    # Initialize VLM
    vlm = initialize_vision_model()
    
    # Set state
    set_agent_state({
        'mode': 'ARMED',
        'user_id': user_id,
        'risk_config': risk_config,
        'browser': browser,
        'vlm': vlm,
        'armed_at': datetime.utcnow()
    })
    
    notify_user(user_id, "System armed and ready. Click 'Start Scan' to begin.")
```

**UI Indicator:**

```
┌─────────────────────────────────────┐
│  ARBitech Status: 🟢 ARMED          │
│  Risk Config: Tier_A_Conservative   │
│  Available Balance: $5,000          │
│  [Start Scanning] [Disarm]          │
└─────────────────────────────────────┘
```

### 3. Autonomous Mode

**Purpose:** Fully automated operation with Tier A trades only

**Safety Guardrails:**
- **ONLY** executes Tier A (risk-free) opportunities
- Requires explicit user opt-in
- Can be paused at any time
- Daily stake limits enforced
- Circuit breaker on consecutive failures

**Entry Criteria:**
```python
def can_enter_autonomous_mode(user_id: str) -> Tuple[bool, str]:
    """Validate autonomous mode eligibility"""
    
    # Check subscription tier
    user = get_user(user_id)
    if user.subscription_tier not in ['pro', 'enterprise']:
        return False, "Autonomous mode requires Pro or Enterprise subscription"
    
    # Verify risk config allows autonomous
    risk_config = get_active_risk_config(user_id)
    if not risk_config.autonomous_enabled:
        return False, "Autonomous mode disabled in risk configuration"
    
    # Check daily limits not exceeded
    today_stake = get_daily_stake_total(user_id)
    if today_stake >= risk_config.max_daily_stake:
        return False, "Daily stake limit reached"
    
    # Verify sufficient balance
    total_balance = get_total_bookmaker_balance(user_id)
    if total_balance < risk_config.min_balance_for_auto:
        return False, "Insufficient balance for autonomous operation"
    
    # Check no recent failures
    recent_failures = count_recent_failures(user_id, hours=1)
    if recent_failures >= 3:
        return False, "Too many recent failures, manual review required"
    
    return True, "Eligible for autonomous mode"
```

**Autonomous Execution Loop:**

```python
async def autonomous_mode_loop(user_id: str):
    """Main autonomous execution loop"""
    
    while get_agent_state()['mode'] == 'AUTONOMOUS':
        try:
            # Scan for opportunities
            opportunities = await scan_for_arbitrage()
            
            # Filter to Tier A only
            tier_a_opportunities = [
                opp for opp in opportunities 
                if opp.risk_tier == 'A'
            ]
            
            if not tier_a_opportunities:
                await asyncio.sleep(15)  # Wait before next scan
                continue
            
            # Process each opportunity
            for opportunity in tier_a_opportunities:
                # Validate still viable (odds may have changed)
                if not await validate_opportunity_live(opportunity):
                    continue
                
                # Check limits not exceeded
                if not check_execution_limits(user_id):
                    notify_user(user_id, "Daily limits reached, pausing autonomous mode")
                    set_agent_mode('ARMED')
                    break
                
                # Execute trade
                result = await execute_trade_autonomous(opportunity)
                
                # Log and notify
                await log_trade_result(result)
                await notify_trade_executed(user_id, result)
                
                # Brief pause between trades
                await asyncio.sleep(5)
            
            # Scan interval
            await asyncio.sleep(30)
            
        except Exception as e:
            log_error(e)
            
            # Check if critical error
            if is_critical_error(e):
                set_agent_mode('IDLE')
                notify_user(user_id, f"Critical error in autonomous mode: {e}")
                break
            
            await asyncio.sleep(60)  # Longer pause after error
```

**Emergency Stop:**

```python
def emergency_stop(user_id: str, reason: str):
    """Immediate system halt"""
    
    # Set mode to IDLE
    set_agent_mode('IDLE')
    
    # Cancel pending orders (if possible)
    cancel_all_pending_orders(user_id)
    
    # Close risky positions (if applicable)
    # Note: For arbitrage, positions are typically locked in
    
    # Log incident
    log_audit_event(user_id, 'EMERGENCY_STOP', {
        'reason': reason,
        'stopped_at': datetime.utcnow(),
        'active_trades': get_active_trades(user_id)
    })
    
    # Notify all channels
    notify_critical(user_id, f"EMERGENCY STOP: {reason}")
```

**User Controls:**

```
┌──────────────────────────────────────────────┐
│  Autonomous Mode: 🟢 ACTIVE                  │
│  ┌─────────────────────────────────────────┐ │
│  │ Trades Today: 12                        │ │
│  │ Profit: $345.60                         │ │
│  │ Win Rate: 100%                          │ │
│  │ Next Scan: 28 seconds                   │ │
│  └─────────────────────────────────────────┘ │
│  [⏸ Pause] [⏹ Stop & Disarm] [⚠ E-STOP]    │
└──────────────────────────────────────────────┘
```

### Mode Transitions

```python
class ModeController:
    """Manages agent operational mode transitions"""
    
    ALLOWED_TRANSITIONS = {
        'IDLE': ['ARMED'],
        'ARMED': ['IDLE', 'HITL', 'AUTONOMOUS'],
        'HITL': ['IDLE', 'ARMED'],
        'AUTONOMOUS': ['IDLE', 'ARMED', 'HITL']
    }
    
    def transition_to(self, new_mode: str, user_id: str):
        """Safe mode transition with validation"""
        current_mode = get_current_mode()
        
        # Validate transition
        if new_mode not in self.ALLOWED_TRANSITIONS[current_mode]:
            raise ValueError(f"Cannot transition from {current_mode} to {new_mode}")
        
        # Pre-transition checks
        if new_mode == 'AUTONOMOUS':
            eligible, reason = can_enter_autonomous_mode(user_id)
            if not eligible:
                raise ValueError(f"Cannot enter autonomous mode: {reason}")
        
        # Perform transition
        old_state = get_agent_state()
        set_agent_mode(new_mode)
        
        # Post-transition actions
        if new_mode == 'AUTONOMOUS':
            asyncio.create_task(autonomous_mode_loop(user_id))
        
        if new_mode == 'IDLE':
            cleanup_resources()
        
        # Log transition
        log_audit_event(user_id, 'MODE_TRANSITION', {
            'from': current_mode,
            'to': new_mode,
            'timestamp': datetime.utcnow()
        })
        
        # Notify user
        notify_mode_change(user_id, current_mode, new_mode)
```

---

## Configuration Management System

### Configuration Hierarchy

```
┌─────────────────────────────────────────────────────┐
│              Configuration Layers                    │
├─────────────────────────────────────────────────────┤
│  1. Global Defaults (System-wide)                   │
│     - Base risk parameters                          │
│     - System limits                                 │
│     - Default timeouts                              │
├─────────────────────────────────────────────────────┤
│  2. User Configurations (User-specific)             │
│     - Risk profiles                                 │
│     - Bookmaker accounts                            │
│     - Notification preferences                      │
├─────────────────────────────────────────────────────┤
│  3. Session Configurations (Runtime)                │
│     - Active scan parameters                        │
│     - Dynamic adjustments                           │
│     - Temporary overrides                           │
└─────────────────────────────────────────────────────┘
```

### Configuration Schema

```yaml
# config.yaml - Master Configuration Template

# System Configuration
system:
  version: "2.0.0"
  environment: "production"  # production, staging, development
  log_level: "INFO"
  
  # Browser Settings
  browser:
    headless: false  # Must be false for Chrome extensions
    display: ":1"    # X11 display
    user_data_dir: "/home/ubuntu/.chrome_profiles/arbitech"
    extensions:
      - path: "/home/ubuntu/extensions/avo_tabs.crx"
        enabled: true
    viewport:
      width: 1920
      height: 1080
    
  # VLM Configuration
  vlm:
    model: "Qwen-VL"  # Options: Qwen-VL, GPT-4V, LLaVA
    confidence_threshold: 0.85
    cache_ttl_seconds: 10
    max_retries: 3
  
  # Performance
  performance:
    max_concurrent_scans: 2
    scan_interval_seconds: 30
    screenshot_quality: 85
    image_preprocessing: true

# User Configuration Template
user:
  user_id: "{{USER_ID}}"
  
  # Risk Management
  risk:
    # Active Profile
    active_profile: "conservative"
    
    # Tier A Configuration
    tier_a:
      enabled: true
      min_profit_percentage: 0.5
      max_stake_per_trade: 500
      max_stake_percentage: 5  # % of total bankroll
      min_liquidity: 1000
      
    # Tier B Configuration
    tier_b:
      enabled: true
      min_profit_percentage: 1.5
      max_stake_per_trade: 200
      require_manual_approval: true
      
    # Global Limits
    limits:
      max_daily_stake: 5000
      max_weekly_stake: 20000
      max_concurrent_trades: 3
      max_open_positions: 5
      
    # Sport Filters
    sports:
      whitelist: ["soccer", "basketball", "tennis", "american_football"]
      blacklist: []
      
    # Bookmaker Filters
    bookmakers:
      whitelist: []  # Empty = all allowed
      blacklist: ["suspicious_bookie_1"]
      min_reliability_score: 0.9
    
    # Failsafes
    failsafe:
      max_consecutive_losses: 2
      cooldown_period_minutes: 30
      emergency_stop_loss: 1000
      pause_on_api_error: true
  
  # Autonomous Mode Settings
  autonomous:
    enabled: false  # Requires explicit opt-in
    tier_a_only: true
    require_minimum_balance: 1000
    max_trades_per_hour: 10
    pause_on_low_balance: true
    
  # Notification Preferences
  notifications:
    telegram:
      enabled: true
      bot_token: "{{TELEGRAM_BOT_TOKEN}}"
      chat_id: "{{TELEGRAM_CHAT_ID}}"
      notify_on:
        - opportunity_detected
        - trade_placed
        - trade_settled
        - error_occurred
        - daily_summary
    
    email:
      enabled: true
      address: "user@example.com"
      notify_on:
        - daily_summary
        - weekly_summary
        - critical_error
    
    dashboard:
      enabled: true
      notify_on: all
    
    sms:
      enabled: false
      number: "+1234567890"
      notify_on:
        - critical_error
        - emergency_stop
  
  # Bookmaker Accounts
  bookmaker_accounts:
    - name: "Betfair"
      username: "{{BETFAIR_USERNAME}}"
      encrypted_password: "{{ENCRYPTED}}"
      currency: "USD"
      balance_sync_interval_minutes: 15
      
    - name: "Pinnacle"
      username: "{{PINNACLE_USERNAME}}"
      encrypted_password: "{{ENCRYPTED}}"
      currency: "USD"
      
  # AVO Tabs Settings
  avo_tabs:
    tab_presets:
      - name: "Soccer_Major_Leagues"
        bookmakers: ["Betfair", "Pinnacle", "Bet365"]
        auto_open: true
        
      - name: "Tennis_Live"
        bookmakers: ["Betfair", "Pinnacle"]
        auto_open: false
    
    multi_link_mode: "sequential"  # sequential, parallel
    tab_refresh_interval_minutes: 30

# Supabase Configuration
supabase:
  url: "{{SUPABASE_URL}}"
  anon_key: "{{SUPABASE_ANON_KEY}}"
  service_role_key: "{{SUPABASE_SERVICE_ROLE_KEY}}"
  
  tables:
    users: "users"
    trades: "trades"
    risk_configs: "risk_configs"
    scan_sessions: "scan_sessions"
    notifications: "notifications"
    audit_logs: "audit_logs"

# API Keys & Credentials
api_keys:
  betfair:
    app_key: "{{BETFAIR_APP_KEY}}"
    session_token: "{{BETFAIR_SESSION_TOKEN}}"
  
  openai:
    api_key: "{{OPENAI_API_KEY}}"  # For GPT-4V fallback
  
  telegram:
    bot_token: "{{TELEGRAM_BOT_TOKEN}}"
  
  sendgrid:
    api_key: "{{SENDGRID_API_KEY}}"

# Monitoring & Logging
monitoring:
  sentry:
    dsn: "{{SENTRY_DSN}}"
    environment: "production"
    traces_sample_rate: 0.1
  
  logging:
    format: "json"
    level: "INFO"
    file: "/home/ubuntu/logs/arbitech.log"
    rotation: "daily"
    retention_days: 30
```

### Dynamic Configuration Updates

```python
class ConfigManager:
    """Runtime configuration management"""
    
    def __init__(self, supabase_client):
        self.db = supabase_client
        self._config_cache = {}
        self._last_sync = None
    
    async def load_user_config(self, user_id: str) -> dict:
        """Load and cache user configuration"""
        
        # Check cache (5 minute TTL)
        if user_id in self._config_cache:
            cached, timestamp = self._config_cache[user_id]
            if (datetime.utcnow() - timestamp).seconds < 300:
                return cached
        
        # Fetch from Supabase
        risk_config = await self.db.table('risk_configs').select('*').eq(
            'user_id', user_id
        ).eq('is_active', True).single().execute()
        
        bookmaker_accounts = await self.db.table('bookmaker_accounts').select('*').eq(
            'user_id', user_id
        ).eq('is_active', True).execute()
        
        # Combine with system defaults
        config = {
            'system': load_system_defaults(),
            'risk': risk_config.data,
            'accounts': bookmaker_accounts.data
        }
        
        # Cache
        self._config_cache[user_id] = (config, datetime.utcnow())
        
        return config
    
    async def update_risk_parameter(self, user_id: str, parameter: str, value: any):
        """Hot-update risk parameter without restart"""
        
        # Validate parameter
        if parameter not in ALLOWED_RUNTIME_UPDATES:
            raise ValueError(f"Parameter {parameter} cannot be updated at runtime")
        
        # Update database
        await self.db.table('risk_configs').update({
            parameter: value,
            'updated_at': datetime.utcnow()
        }).eq('user_id', user_id).eq('is_active', True).execute()
        
        # Invalidate cache
        if user_id in self._config_cache:
            del self._config_cache[user_id]
        
        # Emit event for live agents
        emit_config_update_event(user_id, parameter, value)
        
        # Log change
        await self.db.table('audit_logs').insert({
            'user_id': user_id,
            'action': 'CONFIG_UPDATE',
            'entity_type': 'risk_config',
            'new_values': {parameter: value}
        }).execute()
```

### Configuration Validation

```python
from pydantic import BaseModel, Field, validator

class TierAConfig(BaseModel):
    """Tier A risk configuration with validation"""
    
    enabled: bool = True
    min_profit_percentage: float = Field(ge=0.1, le=10.0)
    max_stake_per_trade: float = Field(ge=10, le=10000)
    max_stake_percentage: float = Field(ge=1, le=20)
    min_liquidity: float = Field(ge=100)
    
    @validator('max_stake_per_trade')
    def stake_reasonable(cls, v, values):
        if v > 5000:
            logger.warning(f"Large max stake: ${v}")
        return v

class RiskConfig(BaseModel):
    """Complete risk configuration"""
    
    tier_a: TierAConfig
    tier_b: dict
    limits: dict
    failsafe: dict
    
    @validator('limits')
    def validate_limits(cls, v):
        if v['max_daily_stake'] < v['tier_a']['max_stake_per_trade']:
            raise ValueError("Daily stake must exceed single trade maximum")
        return v

def validate_config(config_dict: dict) -> RiskConfig:
    """Validate configuration before saving"""
    try:
        return RiskConfig(**config_dict)
    except ValidationError as e:
        raise ValueError(f"Invalid configuration: {e}")
```

### Configuration UI Integration

```javascript
// React Component for Risk Configuration
function RiskConfigEditor({ userId, currentConfig, onSave }) {
    const [config, setConfig] = useState(currentConfig)
    const [errors, setErrors] = useState({})
    
    const handleSave = async () => {
        // Validate on frontend
        const validationErrors = validateRiskConfig(config)
        if (Object.keys(validationErrors).length > 0) {
            setErrors(validationErrors)
            return
        }
        
        // Save to Supabase
        const { error } = await supabase
            .from('risk_configs')
            .update(config)
            .eq('user_id', userId)
            .eq('is_active', true)
        
        if (error) {
            alert(`Error saving configuration: ${error.message}`)
        } else {
            onSave(config)
            alert('Configuration saved successfully!')
        }
    }
    
    return (
        <div className="risk-config-editor">
            <h3>Tier A Configuration (Autonomous Trades)</h3>
            
            <div className="config-group">
                <label>Minimum Profit %</label>
                <input 
                    type="number" 
                    step="0.1"
                    value={config.tier_a.min_profit_percentage}
                    onChange={(e) => setConfig({
                        ...config,
                        tier_a: { ...config.tier_a, min_profit_percentage: parseFloat(e.target.value) }
                    })}
                />
                {errors.min_profit_percentage && <span className="error">{errors.min_profit_percentage}</span>}
            </div>
            
            <div className="config-group">
                <label>Max Stake Per Trade ($)</label>
                <input 
                    type="number"
                    value={config.tier_a.max_stake_per_trade}
                    onChange={(e) => setConfig({
                        ...config,
                        tier_a: { ...config.tier_a, max_stake_per_trade: parseFloat(e.target.value) }
                    })}
                />
            </div>
            
            {/* More fields... */}
            
            <div className="config-actions">
                <button onClick={handleSave}>Save Configuration</button>
                <button onClick={() => setConfig(currentConfig)}>Reset</button>
            </div>
        </div>
    )
}
```

---

## Data Flow & Interaction Patterns

### Primary Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    ARBITRAGE DETECTION FLOW                      │
└─────────────────────────────────────────────────────────────────┘

1. SCAN INITIATION
   ┌──────────────┐
   │ User/Cron    │
   │ Trigger      │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │ Load Config  │
   │ & State      │
   └──────┬───────┘
          │
          ▼
2. DATA COLLECTION
   ┌─────────────────────────────────────┐
   │ Parallel Data Gathering             │
   │                                     │
   │  ┌──────────┐  ┌──────────────┐    │
   │  │ API      │  │ VLM Scraping │    │
   │  │ Calls    │  │ (AVO Tabs)   │    │
   │  └────┬─────┘  └─────┬────────┘    │
   │       │              │              │
   │       └──────┬───────┘              │
   │              ▼                      │
   │      ┌──────────────┐               │
   │      │ Normalize    │               │
   │      │ Odds Data    │               │
   │      └──────┬───────┘               │
   └─────────────┼───────────────────────┘
                 │
                 ▼
3. ARBITRAGE DETECTION
   ┌──────────────────────┐
   │ Calculate Implied    │
   │ Probabilities        │
   └──────┬───────────────┘
          │
          ▼
   ┌──────────────────────┐
   │ Identify Arbitrage   │
   │ (Sum < 1.0)          │
   └──────┬───────────────┘
          │
          ▼
   ┌──────────────────────┐
   │ Calculate Stakes     │
   │ (Kelly Criterion)    │
   └──────┬───────────────┘
          │
          ▼
4. RISK VALIDATION
   ┌──────────────────────┐
   │ Risk Engine          │
   │ Validation           │
   └──────┬───────────────┘
          │
          ▼
   ┌──────────────────────┐
   │ Assign Risk Tier     │
   │ (A, B, C, D)         │
   └──────┬───────────────┘
          │
          ▼
5. DECISION ROUTING
          │
          ├─[Tier A + AUTO MODE]─────┐
          │                           │
          ├─[Tier B/C + HITL]─────┐  │
          │                        │  │
          └─[Tier D]──────────────┼──┼──> REJECT
                                  │  │
                                  ▼  ▼
6. EXECUTION              ┌──────────────┐  ┌──────────────┐
                          │ User Approval│  │ Auto Execute │
                          │ Queue        │  │              │
                          └──────┬───────┘  └──────┬───────┘
                                 │                 │
                                 └────────┬────────┘
                                          ▼
                                  ┌──────────────┐
                                  │ Playwright   │
                                  │ Execution    │
                                  └──────┬───────┘
                                         │
                                         ▼
7. LOGGING & NOTIFICATION
   ┌──────────────────────┐
   │ Write to Supabase    │
   └──────┬───────────────┘
          │
          ▼
   ┌──────────────────────┐
   │ Send Notifications   │
   └──────┬───────────────┘
          │
          ▼
   ┌──────────────────────┐
   │ Update Dashboard     │
   └──────────────────────┘
```

### VLM Interaction Pattern

```python
async def vlm_scan_avo_scanner():
    """VLM-based scanning of AVO.bets scanner UI"""
    
    # 1. Take screenshot
    screenshot_path = await capture_avo_scanner_screenshot()
    
    # 2. Prepare VLM prompt
    prompt = """
    Analyze this betting scanner interface and extract all visible arbitrage opportunities.
    
    For each opportunity, identify:
    1. Sport type
    2. Event name and participants
    3. All displayed odds (format: bookmaker:selection:odds)
    4. Any profit margin indicators
    5. Coordinate positions of odds values for clicking
    
    Return as JSON array:
    [
        {
            "sport": "soccer",
            "event": "Team A vs Team B",
            "legs": [
                {"bookmaker": "Betfair", "selection": "Team A", "odds": 2.1, "coordinates": [x, y]},
                {"bookmaker": "Pinnacle", "selection": "Draw", "odds": 3.5, "coordinates": [x, y]}
            ],
            "profit_margin": "1.2%"
        }
    ]
    
    Only include opportunities with clearly visible odds. If odds are partially obscured, mark as "unclear".
    """
    
    # 3. Call VLM (using DeepAgent's analyze_image)
    vlm_response = await analyze_image(screenshot_path, prompt)
    
    # 4. Parse and validate response
    try:
        opportunities = json.loads(vlm_response)
        validated_opportunities = []
        
        for opp in opportunities:
            # Validate structure
            if not all(key in opp for key in ['sport', 'event', 'legs']):
                continue
            
            # Validate odds format
            for leg in opp['legs']:
                if not isinstance(leg['odds'], (int, float)) or leg['odds'] < 1.01:
                    continue
            
            # Calculate actual profit margin (verify VLM)
            calculated_margin = calculate_profit_margin([leg['odds'] for leg in opp['legs']])
            
            opp['calculated_profit_margin'] = calculated_margin
            validated_opportunities.append(opp)
        
        return validated_opportunities
    
    except json.JSONDecodeError:
        logger.error(f"VLM returned invalid JSON: {vlm_response}")
        return []
```

### Browser Automation Pattern (Playwright)

```python
from playwright.async_api import async_playwright

async def execute_trade_via_playwright(opportunity: dict):
    """Execute multi-leg arbitrage trade"""
    
    async with async_playwright() as p:
        # Connect to existing Chrome instance with AVO Tabs
        browser = await p.chromium.connect_over_cdp('http://localhost:9222')
        
        results = []
        
        for leg in opportunity['legs']:
            try:
                # Find or create tab for bookmaker
                tab = await find_bookmaker_tab(browser, leg['bookmaker'])
                
                if not tab:
                    # Open via AVO Tabs multi-link mode
                    tab = await open_via_avo_tabs(leg['bookmaker'], leg['event'])
                
                # Navigate to bet placement
                if 'coordinates' in leg and leg['coordinates']:
                    # VLM provided coordinates
                    await tab.mouse.click(leg['coordinates'][0], leg['coordinates'][1])
                else:
                    # Fallback: Text-based search
                    await tab.click(f'text="{leg['selection']}"')
                
                # Enter stake
                stake_input = await tab.wait_for_selector('input[name="stake"], input[id="stake"]')
                await stake_input.fill(str(leg['recommended_stake']))
                
                # Verify odds haven't changed
                displayed_odds = await extract_displayed_odds(tab)
                if abs(displayed_odds - leg['odds']) > 0.05:
                    results.append({
                        'leg': leg,
                        'status': 'failed',
                        'reason': 'odds_changed',
                        'new_odds': displayed_odds
                    })
                    continue
                
                # Place bet
                place_button = await tab.wait_for_selector('button:has-text("Place Bet"), button:has-text("Confirm")')
                await place_button.click()
                
                # Wait for confirmation
                await tab.wait_for_selector('text=/bet placed|confirmed/i', timeout=5000)
                
                # Take confirmation screenshot
                screenshot = await tab.screenshot()
                screenshot_url = await upload_to_supabase_storage(screenshot, f"trade_{opportunity['id']}_leg_{leg['bookmaker']}.png")
                
                results.append({
                    'leg': leg,
                    'status': 'success',
                    'screenshot_url': screenshot_url
                })
            
            except Exception as e:
                logger.error(f"Failed to place leg {leg}: {e}")
                results.append({
                    'leg': leg,
                    'status': 'failed',
                    'reason': str(e)
                })
        
        # Check if all legs successful
        all_success = all(r['status'] == 'success' for r in results)
        
        return {
            'opportunity_id': opportunity['id'],
            'all_legs_placed': all_success,
            'legs_results': results
        }
```

### Real-Time Dashboard Updates

```javascript
// Frontend: Real-time trade monitoring
import { createClient } from '@supabase/supabase-js'
import { useEffect, useState } from 'react'

function LiveTradesMonitor({ userId }) {
    const [trades, setTrades] = useState([])
    const [liveOpportunities, setLiveOpportunities] = useState([])
    
    useEffect(() => {
        const supabase = createClient(SUPABASE_URL, SUPABASE_KEY)
        
        // Subscribe to new trades
        const tradesSubscription = supabase
            .channel('trades_changes')
            .on('postgres_changes',
                { 
                    event: 'INSERT', 
                    schema: 'public', 
                    table: 'trades',
                    filter: `user_id=eq.${userId}`
                },
                (payload) => {
                    setTrades(prev => [payload.new, ...prev])
                    
                    // Show toast notification
                    showNotification({
                        title: 'Trade Placed',
                        message: `${payload.new.event_name} - $${payload.new.expected_profit} profit`,
                        type: 'success'
                    })
                }
            )
            .on('postgres_changes',
                {
                    event: 'UPDATE',
                    schema: 'public',
                    table: 'trades',
                    filter: `user_id=eq.${userId}`
                },
                (payload) => {
                    setTrades(prev => prev.map(t => 
                        t.id === payload.new.id ? payload.new : t
                    ))
                    
                    // If trade settled, show result
                    if (payload.new.status === 'won' || payload.new.status === 'lost') {
                        const emoji = payload.new.status === 'won' ? '✅' : '❌'
                        showNotification({
                            title: `Trade ${payload.new.status.toUpperCase()}`,
                            message: `${emoji} ${payload.new.event_name} - Profit: $${payload.new.actual_profit}`,
                            type: payload.new.status === 'won' ? 'success' : 'error'
                        })
                    }
                }
            )
            .subscribe()
        
        // Initial fetch
        supabase
            .from('trades')
            .select('*')
            .eq('user_id', userId)
            .order('created_at', { ascending: false })
            .limit(20)
            .then(({ data }) => setTrades(data || []))
        
        return () => {
            tradesSubscription.unsubscribe()
        }
    }, [userId])
    
    return (
        <div className="live-trades-monitor">
            <h3>Live Trades</h3>
            <div className="trades-list">
                {trades.map(trade => (
                    <TradeCard key={trade.id} trade={trade} />
                ))}
            </div>
        </div>
    )
}
```

---

## Integration Strategy with Existing UI

### UI Architecture

```
┌─────────────────────────────────────────────────────────┐
│    Existing UI (apps.abacus.ai/chatllm/?appId=...)     │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  Header                                        │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────┐ │    │
│  │  │ Logo     │  │ User     │  │ Status: 🟢   │ │    │
│  │  └──────────┘  └──────────┘  └──────────────┘ │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌─────────────┬──────────────────────────────────────┐ │
│  │ Sidebar     │  Main Content Area                   │ │
│  │             │                                      │ │
│  │ - Dashboard │  ┌─────────────────────────────────┐│ │
│  │ - Scanner   │  │ [INJECT: ARBitech Components]   ││ │
│  │ - Trades    │  │                                 ││ │
│  │ - Config    │  │ • Control Panel                 ││ │
│  │ - Reports   │  │ • Live Opportunities            ││ │
│  │             │  │ • Active Trades                 ││ │
│  │             │  │ • Performance Metrics           ││ │
│  │             │  │                                 ││ │
│  │             │  └─────────────────────────────────┘│ │
│  └─────────────┴──────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Integration Methods

#### Option 1: Iframe Embedding (Recommended)

```html
<!-- Embed ARBitech components as iframe -->
<div id="arbitech-container">
    <iframe 
        src="https://arbitech-components.abacus.ai/dashboard"
        width="100%"
        height="800px"
        frameborder="0"
        allow="clipboard-write"
    ></iframe>
</div>

<script>
// Post-message communication
window.addEventListener('message', (event) => {
    if (event.origin !== 'https://arbitech-components.abacus.ai') return;
    
    // Handle messages from ARBitech iframe
    switch(event.data.type) {
        case 'TRADE_EXECUTED':
            updateMainDashboard(event.data.trade);
            break;
        case 'MODE_CHANGED':
            updateStatusIndicator(event.data.mode);
            break;
    }
});

// Send config to iframe
iframe.contentWindow.postMessage({
    type: 'INIT',
    userId: currentUser.id,
    config: userConfig
}, 'https://arbitech-components.abacus.ai');
</script>
```

#### Option 2: Direct Component Integration

```javascript
// Import ARBitech React components
import { 
    ARBitechControlPanel, 
    LiveOpportunitiesGrid, 
    TradesTable,
    RiskConfigEditor 
} from '@arbitech/ui-components'

function ExistingDashboard() {
    const { user } = useAuth()
    const [config, setConfig] = useState(null)
    
    useEffect(() => {
        // Fetch user config on mount
        fetchUserConfig(user.id).then(setConfig)
    }, [user.id])
    
    return (
        <div className="dashboard">
            <Sidebar />
            <MainContent>
                {/* Inject ARBitech components */}
                <ARBitechControlPanel 
                    userId={user.id}
                    config={config}
                    onConfigChange={setConfig}
                />
                
                <LiveOpportunitiesGrid userId={user.id} />
                
                <TradesTable 
                    userId={user.id}
                    realtime={true}
                />
            </MainContent>
        </div>
    )
}
```

### Database Connection Strategy

**No UI Rebuild Required** - Connect existing UI to Supabase or Airtable

#### Supabase Connection

```javascript
// In existing UI codebase
import { createClient } from '@supabase/supabase-js'

// Initialize Supabase client
const supabase = createClient(
    process.env.SUPABASE_URL,
    process.env.SUPABASE_ANON_KEY
)

// Fetch trades for display
async function fetchUserTrades(userId) {
    const { data, error } = await supabase
        .from('trades')
        .select('*')
        .eq('user_id', userId)
        .order('created_at', { ascending: false })
    
    if (error) throw error
    return data
}

// Update existing dashboard component
function DashboardStats({ userId }) {
    const [trades, setTrades] = useState([])
    
    useEffect(() => {
        fetchUserTrades(userId).then(setTrades)
        
        // Subscribe to updates
        const subscription = supabase
            .channel('trades')
            .on('postgres_changes', { 
                event: '*', 
                schema: 'public', 
                table: 'trades',
                filter: `user_id=eq.${userId}`
            }, (payload) => {
                setTrades(prev => [payload.new, ...prev.filter(t => t.id !== payload.new.id)])
            })
            .subscribe()
        
        return () => subscription.unsubscribe()
    }, [userId])
    
    // Calculate stats
    const totalProfit = trades.reduce((sum, t) => sum + (t.actual_profit || 0), 0)
    const winRate = trades.filter(t => t.status === 'won').length / trades.length * 100
    
    return (
        <div className="stats-grid">
            <StatCard title="Total Profit" value={`$${totalProfit.toFixed(2)}`} />
            <StatCard title="Win Rate" value={`${winRate.toFixed(1)}%`} />
            <StatCard title="Active Trades" value={trades.filter(t => t.status === 'pending').length} />
        </div>
    )
}
```

#### Airtable Connection

```javascript
// Alternative: Airtable connection
import Airtable from 'airtable'

const base = new Airtable({ apiKey: process.env.AIRTABLE_API_KEY }).base(process.env.AIRTABLE_BASE_ID)

async function fetchTradesFromAirtable(userId) {
    const records = await base('Trades')
        .select({
            filterByFormula: `{user_id} = '${userId}'`,
            sort: [{ field: 'created_at', direction: 'desc' }]
        })
        .all()
    
    return records.map(r => ({
        id: r.id,
        ...r.fields
    }))
}

// Polling-based updates (Airtable doesn't have native realtime)
function useAirtablePolling(userId, intervalMs = 5000) {
    const [data, setData] = useState([])
    
    useEffect(() => {
        const fetchData = async () => {
            const trades = await fetchTradesFromAirtable(userId)
            setData(trades)
        }
        
        fetchData() // Initial fetch
        const interval = setInterval(fetchData, intervalMs)
        
        return () => clearInterval(interval)
    }, [userId, intervalMs])
    
    return data
}
```

### UI Enhancement: Add ARBitech Section

```javascript
// Minimal changes to existing UI
// File: src/pages/Dashboard.jsx (existing)

import ARBitechSection from './components/ARBitechSection'

function Dashboard() {
    return (
        <div className="dashboard-layout">
            <Sidebar />
            <MainContent>
                {/* EXISTING CONTENT */}
                <Overview />
                <Analytics />
                
                {/* NEW: ARBitech Section */}
                <ARBitechSection />
                
                {/* EXISTING CONTENT */}
                <RecentActivity />
            </MainContent>
        </div>
    )
}

// New file: src/components/ARBitechSection.jsx
function ARBitechSection() {
    return (
        <section className="arbitech-section">
            <h2>ARBitech Automation</h2>
            
            <div className="arbitech-grid">
                {/* Control Panel */}
                <div className="control-panel card">
                    <ControlPanel />
                </div>
                
                {/* Live Opportunities */}
                <div className="opportunities card">
                    <LiveOpportunities />
                </div>
                
                {/* Recent Trades */}
                <div className="recent-trades card">
                    <RecentTrades />
                </div>
            </div>
        </section>
    )
}
```

### Authentication Integration

```javascript
// Leverage existing auth system
function ARBitechWrapper() {
    const { user, isAuthenticated } = useExistingAuth() // Your current auth hook
    
    if (!isAuthenticated) {
        return <LoginPrompt />
    }
    
    // Initialize Supabase with existing user session
    const supabase = useMemo(() => {
        const client = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)
        
        // Sync existing auth token to Supabase
        client.auth.setSession({
            access_token: user.accessToken,
            refresh_token: user.refreshToken
        })
        
        return client
    }, [user])
    
    return (
        <SupabaseContext.Provider value={supabase}>
            <ARBitechComponents userId={user.id} />
        </SupabaseContext.Provider>
    )
}
```

---

## Deployment Strategy for DeepAgent

### DeepAgent Environment Setup

```bash
#!/bin/bash
# setup_arbitech.sh - DeepAgent initialization script

set -e

echo "🚀 Setting up ARBitech on DeepAgent..."

# 1. Update system
sudo apt-get update && sudo apt-get upgrade -y

# 2. Install dependencies
echo "📦 Installing dependencies..."
sudo apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    chromium-browser \
    chromium-chromedriver \
    xvfb \
    redis-server \
    git

# 3. Setup Python environment
echo "🐍 Setting up Python environment..."
python3.11 -m venv /home/ubuntu/arbitech_env
source /home/ubuntu/arbitech_env/bin/activate

pip install --upgrade pip
pip install -r /home/ubuntu/arbitech/requirements.txt

# 4. Install Playwright browsers
echo "🎭 Installing Playwright..."
playwright install chromium
playwright install-deps

# 5. Setup Chrome profile for AVO Tabs
echo "🔧 Configuring Chrome..."
mkdir -p /home/ubuntu/.chrome_profiles/arbitech

# 6. Download and install AVO Tabs extension
echo "📥 Installing AVO Tabs extension..."
# Note: Manual step required - user must provide .crx file
# Download from Chrome Web Store or provided source
mkdir -p /home/ubuntu/extensions

# 7. Configure X11 display
echo "🖥️ Configuring display..."
export DISPLAY=:1
Xvfb :1 -screen 0 1920x1080x24 &

# 8. Setup Supabase configuration
echo "💾 Configuring database..."
cat > /home/ubuntu/arbitech/.env << EOF
SUPABASE_URL=${SUPABASE_URL}
SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY}

TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
OPENAI_API_KEY=${OPENAI_API_KEY}

ENVIRONMENT=production
LOG_LEVEL=INFO
EOF

# 9. Initialize database schema
echo "📊 Initializing database..."
python /home/ubuntu/arbitech/scripts/init_database.py

# 10. Setup systemd service (optional for background operation)
echo "⚙️ Configuring service..."
sudo tee /etc/systemd/system/arbitech.service > /dev/null << EOF
[Unit]
Description=ARBitech Automation Agent
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/arbitech
Environment="DISPLAY=:1"
ExecStart=/home/ubuntu/arbitech_env/bin/python /home/ubuntu/arbitech/main.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 11. Start Redis
echo "🔴 Starting Redis..."
sudo systemctl start redis-server
sudo systemctl enable redis-server

echo "✅ Setup complete! Run 'python /home/ubuntu/arbitech/main.py' to start."
```

### Main Application Entry Point

```python
# main.py - DeepAgent application entry point

import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

from arbitech.orchestrator import ARBitechOrchestrator
from arbitech.config import load_config
from arbitech.database import SupabaseManager
from arbitech.notifications import NotificationManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/ubuntu/logs/arbitech.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def main():
    """Main application entry point"""
    
    logger.info("🚀 Starting ARBitech Automation System")
    
    # Load environment variables
    load_dotenv()
    
    # Load configuration
    config = load_config('/home/ubuntu/arbitech/config.yaml')
    
    # Initialize database
    db = SupabaseManager(
        url=config['supabase']['url'],
        key=config['supabase']['service_role_key']
    )
    
    # Initialize notification manager
    notifier = NotificationManager(db, config)
    
    # Initialize orchestrator
    orchestrator = ARBitechOrchestrator(
        config=config,
        database=db,
        notifier=notifier
    )
    
    try:
        # Start orchestrator
        await orchestrator.start()
        
        logger.info("✅ ARBitech is running. Press Ctrl+C to stop.")
        
        # Keep running
        await asyncio.Event().wait()
    
    except KeyboardInterrupt:
        logger.info("🛑 Shutdown signal received")
    
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
    
    finally:
        # Cleanup
        await orchestrator.shutdown()
        logger.info("👋 ARBitech stopped")

if __name__ == "__main__":
    asyncio.run(main())
```

### Directory Structure

```
/home/ubuntu/arbitech/
├── main.py                      # Entry point
├── requirements.txt             # Python dependencies
├── config.yaml                  # Configuration file
├── .env                         # Secrets (git-ignored)
├── README.md                    # Documentation
│
├── arbitech/                    # Main package
│   ├── __init__.py
│   ├── orchestrator.py          # LangGraph orchestrator
│   ├── config.py                # Configuration management
│   ├── database.py              # Supabase/Airtable clients
│   ├── notifications.py         # Notification system
│   │
│   ├── agents/                  # Agent modules
│   │   ├── __init__.py
│   │   ├── vlm_agent.py         # Vision Language Model agent
│   │   ├── scanner_agent.py     # AVO scanner interaction
│   │   ├── risk_agent.py        # Risk validation
│   │   └── execution_agent.py   # Trade execution
│   │
│   ├── automation/              # Browser automation
│   │   ├── __init__.py
│   │   ├── playwright_manager.py
│   │   ├── avo_tabs_interface.py
│   │   └── bookmaker_handlers.py
│   │
│   ├── models/                  # Data models
│   │   ├── __init__.py
│   │   ├── opportunity.py
│   │   ├── trade.py
│   │   └── config.py
│   │
│   └── utils/                   # Utilities
│       ├── __init__.py
│       ├── calculations.py      # Math functions
│       ├── validation.py        # Input validation
│       └── logger.py            # Logging setup
│
├── scripts/                     # Utility scripts
│   ├── init_database.py         # Database initialization
│   ├── migrate_config.py        # Config migration
│   └── test_connection.py       # Connection testing
│
├── tests/                       # Test suite
│   ├── test_arbitrage.py
│   ├── test_risk.py
│   └── test_execution.py
│
├── logs/                        # Log files
│   └── arbitech.log
│
└── extensions/                  # Browser extensions
    └── avo_tabs.crx
```

### DeepAgent Conversation Initialization

```python
# Initialize ARBitech in DeepAgent conversation

from deepagent import DeepAgent

agent = DeepAgent()

# Step 1: Install dependencies
agent.bash("""
cd /home/ubuntu
git clone https://github.com/yourusername/arbitech.git
cd arbitech
bash setup_arbitech.sh
""")

# Step 2: Configure environment
agent.file_write(
    path="/home/ubuntu/arbitech/.env",
    content=f"""
SUPABASE_URL={user_provided_url}
SUPABASE_ANON_KEY={user_provided_key}
TELEGRAM_BOT_TOKEN={user_provided_token}
""",
    append=False
)

# Step 3: Initialize database
agent.bash("cd /home/ubuntu/arbitech && python scripts/init_database.py")

# Step 4: Start application
agent.bash("cd /home/ubuntu/arbitech && python main.py &", background=True)

# Step 5: Open dashboard in browser
agent.browser_open(
    type="url",
    address="https://apps.abacus.ai/chatllm/?appId=3cb1afd5a&convoId=11d1c6aaed"
)
```

### Monitoring & Maintenance

```python
# monitoring.py - Health checks and metrics

import psutil
import asyncio
from datetime import datetime

class SystemMonitor:
    """Monitor system health and performance"""
    
    async def check_health(self) -> dict:
        """Comprehensive health check"""
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'system': {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent
            },
            'arbitech': {
                'mode': self.get_current_mode(),
                'active_trades': self.count_active_trades(),
                'scan_status': self.get_scan_status(),
                'browser_connected': self.check_browser_connection(),
                'database_connected': await self.check_database_connection()
            },
            'performance': {
                'scans_per_hour': self.calculate_scan_rate(),
                'avg_execution_time_ms': self.get_avg_execution_time(),
                'error_rate': self.calculate_error_rate()
            }
        }
    
    async def send_daily_report(self, user_id: str):
        """Generate and send daily performance report"""
        
        stats = await self.db.get_daily_stats(user_id)
        
        report = f"""
📊 **ARBitech Daily Report**
Date: {datetime.utcnow().strftime('%Y-%m-%d')}

**Trading Activity:**
- Total Scans: {stats['total_scans']}
- Opportunities Detected: {stats['opportunities_detected']}
- Trades Executed: {stats['trades_executed']}
- Win Rate: {stats['win_rate']:.1f}%

**Financial Performance:**
- Total Profit: ${stats['total_profit']:.2f}
- Average Profit per Trade: ${stats['avg_profit']:.2f}
- ROI: {stats['roi']:.2f}%
- Largest Win: ${stats['largest_win']:.2f}

**System Health:**
- Uptime: {stats['uptime_hours']:.1f} hours
- Error Rate: {stats['error_rate']:.2f}%
- Avg Execution Time: {stats['avg_execution_ms']:.0f}ms

[View Full Dashboard →](https://apps.abacus.ai/chatllm/?appId=3cb1afd5a)
        """
        
        await self.notifier.send(user_id, 'daily_summary', report)
```

---

## Security Considerations

### Security Architecture

```
┌──────────────────────────────────────────────────┐
│            SECURITY LAYERS                        │
├──────────────────────────────────────────────────┤
│  1. Authentication & Authorization               │
│     • Supabase Auth (JWT tokens)                 │
│     • Row Level Security (RLS)                   │
│     • API key rotation                           │
├──────────────────────────────────────────────────┤
│  2. Data Encryption                              │
│     • Credentials at rest (AES-256)              │
│     • TLS for data in transit                    │
│     • Secure environment variables               │
├──────────────────────────────────────────────────┤
│  3. Browser Security                             │
│     • Isolated Chrome profiles                   │
│     • Extension validation                       │
│     • Click coordinate bounds checking           │
├──────────────────────────────────────────────────┤
│  4. Financial Safeguards                         │
│     • Multi-tier risk validation                 │
│     • Stake limits (per trade, daily, weekly)    │
│     • Emergency stop mechanisms                  │
├──────────────────────────────────────────────────┤
│  5. Audit & Compliance                           │
│     • Comprehensive logging                      │
│     • Trade audit trail                          │
│     • User action tracking                       │
└──────────────────────────────────────────────────┘
```

### Credential Management

```python
# credentials.py - Secure credential handling

from cryptography.fernet import Fernet
import os
from typing import Dict

class CredentialVault:
    """Secure storage and retrieval of sensitive credentials"""
    
    def __init__(self):
        # Load encryption key from environment
        key = os.getenv('ENCRYPTION_KEY')
        if not key:
            # Generate and save new key (one-time setup)
            key = Fernet.generate_key()
            print(f"⚠️  SAVE THIS KEY SECURELY: {key.decode()}")
        else:
            key = key.encode()
        
        self.cipher = Fernet(key)
    
    def encrypt_credentials(self, credentials: Dict[str, str]) -> str:
        """Encrypt bookmaker credentials"""
        import json
        
        json_str = json.dumps(credentials)
        encrypted = self.cipher.encrypt(json_str.encode())
        return encrypted.decode()
    
    def decrypt_credentials(self, encrypted_str: str) -> Dict[str, str]:
        """Decrypt bookmaker credentials"""
        import json
        
        decrypted = self.cipher.decrypt(encrypted_str.encode())
        return json.loads(decrypted.decode())
    
    async def store_bookmaker_credentials(
        self, 
        user_id: str, 
        bookmaker: str, 
        username: str, 
        password: str
    ):
        """Securely store bookmaker login credentials"""
        
        encrypted = self.encrypt_credentials({
            'username': username,
            'password': password
        })
        
        await self.db.table('bookmaker_accounts').insert({
            'user_id': user_id,
            'bookmaker_name': bookmaker,
            'username': username,  # Plain for reference
            'credentials_encrypted': encrypted
        }).execute()
    
    async def retrieve_bookmaker_credentials(
        self, 
        user_id: str, 
        bookmaker: str
    ) -> Dict[str, str]:
        """Retrieve and decrypt bookmaker credentials"""
        
        result = await self.db.table('bookmaker_accounts').select(
            'credentials_encrypted'
        ).eq('user_id', user_id).eq('bookmaker_name', bookmaker).single().execute()
        
        if not result.data:
            raise ValueError(f"No credentials found for {bookmaker}")
        
        return self.decrypt_credentials(result.data['credentials_encrypted'])
```

### Browser Security

```python
# browser_security.py

class BrowserSecurityManager:
    """Enforce browser security policies"""
    
    ALLOWED_DOMAINS = [
        'betfair.com',
        'pinnacle.com',
        'bet365.com',
        # ... other legitimate bookmakers
    ]
    
    def validate_url(self, url: str) -> bool:
        """Ensure URL is from allowed domain"""
        from urllib.parse import urlparse
        
        domain = urlparse(url).netloc
        return any(allowed in domain for allowed in self.ALLOWED_DOMAINS)
    
    def validate_click_coordinates(
        self, 
        x: int, 
        y: int, 
        viewport_size: tuple
    ) -> bool:
        """Ensure click is within safe bounds"""
        width, height = viewport_size
        
        # Reject clicks outside viewport
        if x < 0 or y < 0 or x > width or y > height:
            return False
        
        # Reject clicks in dangerous zones (e.g., browser chrome)
        if y < 100:  # Top 100px (address bar, etc.)
            logger.warning(f"Rejected click in dangerous zone: ({x}, {y})")
            return False
        
        return True
    
    async def validate_avo_extension(self, browser_context) -> bool:
        """Verify AVO Tabs extension is legitimate"""
        
        # Check extension is loaded
        extensions = await browser_context.evaluate('''
            () => {
                return Object.keys(window).filter(k => k.startsWith('AVO'));
            }
        ''')
        
        if 'AVO' not in extensions:
            logger.error("AVO Tabs extension not detected")
            return False
        
        # Verify extension signature/version
        avo_version = await browser_context.evaluate('() => window.AVO?.version')
        
        if not avo_version or avo_version < "1.0.0":
            logger.error(f"Invalid AVO version: {avo_version}")
            return False
        
        return True
```

### Rate Limiting & Abuse Prevention

```python
# rate_limiting.py

from datetime import datetime, timedelta
from collections import defaultdict

class RateLimiter:
    """Prevent abuse and excessive usage"""
    
    def __init__(self):
        self.user_requests = defaultdict(list)
    
    def check_rate_limit(self, user_id: str, action: str, limit: int, window_seconds: int) -> bool:
        """Check if user has exceeded rate limit"""
        
        now = datetime.utcnow()
        key = f"{user_id}:{action}"
        
        # Remove old requests outside window
        self.user_requests[key] = [
            ts for ts in self.user_requests[key]
            if now - ts < timedelta(seconds=window_seconds)
        ]
        
        # Check limit
        if len(self.user_requests[key]) >= limit:
            logger.warning(f"Rate limit exceeded for {user_id} on {action}")
            return False
        
        # Add current request
        self.user_requests[key].append(now)
        return True

# Usage
rate_limiter = RateLimiter()

async def execute_trade(user_id: str, opportunity: dict):
    """Execute trade with rate limiting"""
    
    # Max 20 trades per hour
    if not rate_limiter.check_rate_limit(user_id, 'execute_trade', 20, 3600):
        raise ValueError("Trade rate limit exceeded. Wait before next trade.")
    
    # Proceed with execution
    ...
```

### Audit Logging

```python
# audit.py

async def log_sensitive_action(
    user_id: str,
    action: str,
    entity_type: str,
    entity_id: str,
    details: dict,
    ip_address: str = None
):
    """Comprehensive audit logging"""
    
    await db.table('audit_logs').insert({
        'user_id': user_id,
        'action': action,
        'entity_type': entity_type,
        'entity_id': entity_id,
        'new_values': details,
        'ip_address': ip_address,
        'user_agent': get_user_agent(),
        'created_at': datetime.utcnow()
    }).execute()
    
    # Also log to file for redundancy
    logger.info(f"AUDIT: {user_id} performed {action} on {entity_type}:{entity_id}")

# Audit all sensitive operations
@audit_action('CONFIG_UPDATE')
async def update_risk_config(user_id: str, new_config: dict):
    ...

@audit_action('TRADE_EXECUTION')
async def execute_trade(user_id: str, trade: dict):
    ...

@audit_action('MODE_CHANGE')
async def change_mode(user_id: str, new_mode: str):
    ...
```

---

## Implementation Phases/Roadmap

### Phase 1: Foundation (Weeks 1-2)

**Goals:** Core infrastructure and basic functionality

**Tasks:**
1. ✅ Environment Setup
   - Install dependencies on DeepAgent
   - Configure Chrome with AVO Tabs extension
   - Setup Supabase project and schema
   
2. ✅ Database Implementation
   - Create all tables with RLS
   - Implement Supabase client wrapper
   - Setup authentication flow
   
3. ✅ Basic Browser Automation
   - Playwright integration
   - Chrome profile management
   - AVO Tabs extension detection
   
4. ✅ VLM Integration
   - Qwen-VL setup
   - Screenshot → VLM → JSON pipeline
   - OCR accuracy testing

**Deliverables:**
- Working DeepAgent environment
- Database with sample data
- Basic browser automation (open tabs, take screenshots)
- VLM parsing simple odds displays

**Success Criteria:**
- Can launch Chrome with AVO Tabs
- Can take screenshot and extract odds with >90% accuracy
- Database reads/writes working

---

### Phase 2: Core Detection Engine (Weeks 3-4)

**Goals:** Arbitrage detection and risk validation

**Tasks:**
1. ✅ Scanning Module
   - AVO scanner UI interaction
   - Odds data extraction
   - Multi-bookmaker support
   
2. ✅ Arbitrage Detector
   - Implied probability calculations
   - Kelly criterion stake calculations
   - Opportunity ranking
   
3. ✅ Risk Engine
   - Tier classification (A, B, C, D)
   - Rule-based validation
   - Limit checking (stake, bankroll, etc.)
   
4. ✅ Configuration System
   - YAML config loading
   - User preference management
   - Runtime config updates

**Deliverables:**
- Functional scanning system
- Arbitrage opportunities correctly identified
- Risk tiers accurately assigned
- Configuration system working

**Success Criteria:**
- Detects real arbitrage opportunities from AVO scanner
- Risk tiers align with configured rules
- No false positives in Tier A classification

---

### Phase 3: Execution & Automation (Weeks 5-6)

**Goals:** Automated trade execution

**Tasks:**
1. ✅ Trade Execution Module
   - Playwright-based bet placement
   - Multi-leg coordination
   - Error handling and retries
   
2. ✅ HITL Mode Implementation
   - User approval workflow
   - Dashboard integration
   - Timeout handling
   
3. ✅ State Management
   - LangGraph orchestration
   - State persistence
   - Recovery from failures
   
4. ✅ Logging & Monitoring
   - Trade result logging
   - Performance metrics
   - Error tracking

**Deliverables:**
- End-to-end trade execution (HITL mode)
- Robust error handling
- Comprehensive logging
- State machine functioning

**Success Criteria:**
- Can place bets on 3+ bookmakers
- HITL approval workflow smooth
- System recovers from errors gracefully

---

### Phase 4: Autonomous Mode & Safety (Weeks 7-8)

**Goals:** Full autonomous operation with safeguards

**Tasks:**
1. ✅ Autonomous Execution
   - Tier A auto-execution
   - Real-time decision making
   - Concurrent trade handling
   
2. ✅ Safety Mechanisms
   - Circuit breakers
   - Emergency stop
   - Balance reconciliation
   - Velocity checks
   
3. ✅ Notification System
   - Telegram integration
   - Email summaries
   - Dashboard real-time updates
   
4. ✅ Testing & Validation
   - Simulated trades
   - Paper trading mode
   - Stress testing

**Deliverables:**
- Fully autonomous mode (Tier A only)
- All safety mechanisms active
- Multi-channel notifications
- Extensive testing completed

**Success Criteria:**
- Autonomous mode runs 24/7 without intervention
- No unauthorized trades (Tier B/C/D)
- Emergency stop works instantly
- Notifications deliver within 5 seconds

---

### Phase 5: UI Integration & Polish (Weeks 9-10)

**Goals:** Seamless user experience

**Tasks:**
1. ✅ Dashboard Integration
   - Connect existing UI to Supabase
   - Real-time trade display
   - Control panel implementation
   
2. ✅ Configuration UI
   - Risk parameter editor
   - Bookmaker account management
   - Notification preferences
   
3. ✅ Analytics & Reporting
   - Performance dashboards
   - Trade history visualization
   - Profit/loss charts
   
4. ✅ User Experience
   - Onboarding flow
   - Help documentation
   - Error messages user-friendly

**Deliverables:**
- Polished dashboard with real-time updates
- Intuitive configuration interface
- Rich analytics and reports
- Complete user documentation

**Success Criteria:**
- Non-technical users can configure and run system
- Dashboard updates within 1 second of events
- Analytics provide actionable insights

---

### Phase 6: Optimization & Scale (Weeks 11-12)

**Goals:** Performance optimization and scale testing

**Tasks:**
1. ✅ Performance Tuning
   - VLM response caching
   - Database query optimization
   - Concurrent scan optimization
   
2. ✅ Advanced Features
   - Multi-sport support
   - P2P exchange integration
   - Custom bookmaker handlers
   
3. ✅ Scale Testing
   - High-frequency scanning
   - Multiple concurrent users
   - Load testing
   
4. ✅ Production Hardening
   - Security audit
   - Error recovery testing
   - Backup systems

**Deliverables:**
- Optimized performance (sub-second scans)
- Support for 10+ sports
- Handles 5+ concurrent users
- Production-ready deployment

**Success Criteria:**
- Scan-to-execution under 3 seconds
- 99.5% uptime
- Zero data loss
- Sub-100ms database queries

---

### Post-Launch: Continuous Improvement

**Ongoing Tasks:**
- Monitor performance metrics
- Add new bookmaker integrations
- Improve VLM accuracy
- Expand sport coverage
- User feedback implementation
- Security updates

**Monthly Reviews:**
- Profitability analysis
- System reliability review
- User satisfaction survey
- Feature prioritization

---

## Conclusion

This comprehensive framework provides a complete blueprint for implementing the ARBitech automation system on DeepAgent. The architecture is:

✅ **Modular:** Each component can be developed and tested independently  
✅ **Scalable:** Supports growth from single user to multi-tenant platform  
✅ **Secure:** Multiple layers of security and financial safeguards  
✅ **Actionable:** Detailed enough for immediate implementation  
✅ **DeepAgent-Native:** Leverages platform capabilities optimally  

### Next Steps

1. **Immediate Actions:**
   - Setup Supabase project
   - Clone repository structure
   - Run Phase 1 setup script
   
2. **First Week Goals:**
   - Complete environment setup
   - Database schema deployed
   - First VLM test successful
   
3. **Key Decision Points:**
   - Supabase vs Airtable (recommend Supabase)
   - Qwen-VL vs GPT-4V (recommend Qwen-VL for cost)
   - Deployment: DeepAgent conversation vs standalone service

### Support & Resources

- **Documentation:** Inline comments and README files
- **Testing:** Comprehensive test suite included
- **Monitoring:** Sentry integration for error tracking
- **Community:** (Optional) Discord/Slack for support

---

**Document Version:** 1.0  
**Created:** October 8, 2025  
**Platform:** DeepAgent (Abacus.AI)  
**Status:** Ready for Implementation ✅
