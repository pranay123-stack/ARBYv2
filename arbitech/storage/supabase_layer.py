"""
Supabase Data Persistence Layer for ARBitech Trading Platform

This module provides a comprehensive interface between ARBitech's Python infrastructure
and the Supabase backend, enabling:
- Opportunity storage and retrieval
- Trade execution tracking
- Risk management persistence
- HITL decision logging
- Autonomous decision recording
- Real-time monitoring and alerts
- Performance metrics tracking
"""

import os
import json
import asyncio
from typing import List, Dict, Optional, Any, Union
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4
import logging

from supabase import create_client, Client
from storage.models import (
    ArbitrageOpportunity, ArbitrageLeg, Trade, RiskConfig,
    ScannerSession, BookmakerAccount, Notification,
    TradeStatus, ExecutionMode, RiskTier, Sport
)

logger = logging.getLogger(__name__)


class SupabaseDataLayer:
    """
    Comprehensive data persistence layer for ARBitech platform.
    Handles all database operations and real-time subscriptions.
    """
    
    def __init__(self, url: Optional[str] = None, key: Optional[str] = None):
        """
        Initialize Supabase client.
        
        Args:
            url: Supabase project URL (defaults to SUPABASE_URL env var)
            key: Supabase anon key (defaults to SUPABASE_ANON_KEY env var)
        """
        self.url = url or os.getenv('SUPABASE_URL')
        self.key = key or os.getenv('SUPABASE_ANON_KEY')
        
        if not self.url or not self.key:
            raise ValueError("Supabase URL and key must be provided or set as environment variables")
        
        self.client: Client = create_client(self.url, self.key)
        self.subscriptions = []
        
        logger.info("SupabaseDataLayer initialized successfully")
    
    # ============================================
    # ARBITRAGE OPPORTUNITIES
    # ============================================
    
    async def save_opportunity(self, opportunity: ArbitrageOpportunity) -> Dict[str, Any]:
        """
        Save an arbitrage opportunity and its legs to the database.
        
        Args:
            opportunity: ArbitrageOpportunity instance
            
        Returns:
            Saved opportunity data with ID
        """
        try:
            # Prepare opportunity data
            opp_data = {
                'id': str(opportunity.id),
                'sport': opportunity.sport.value,
                'event_name': opportunity.event_name,
                'event_date': opportunity.event_date.isoformat(),
                'market_type': opportunity.market_type,
                'total_stake': float(opportunity.total_stake),
                'profit_margin': float(opportunity.profit_margin),
                'profit_amount': float(opportunity.profit_amount),
                'guaranteed_profit': opportunity.guaranteed_profit,
                'risk_tier': opportunity.risk_tier.value,
                'liquidity_checked': opportunity.liquidity_checked,
                'odds_freshness': opportunity.odds_freshness.isoformat(),
                'validation_errors': opportunity.validation_errors,
                'source_scanner': opportunity.source_scanner,
                'discovered_at': opportunity.discovered_at.isoformat(),
                'expires_at': opportunity.expires_at.isoformat() if opportunity.expires_at else None
            }
            
            # Insert opportunity
            result = self.client.table('arbitrage_opportunities').insert(opp_data).execute()
            
            if not result.data:
                raise Exception("Failed to insert opportunity")
            
            opp_id = result.data[0]['id']
            
            # Insert legs
            legs_data = []
            for leg in opportunity.legs:
                leg_data = {
                    'id': str(uuid4()),
                    'opportunity_id': opp_id,
                    'bookmaker': leg.bookmaker,
                    'event_outcome': leg.event_outcome,
                    'odds': float(leg.odds),
                    'implied_probability': float(leg.implied_probability),
                    'stake_percentage': float(leg.stake_percentage),
                    'actual_stake': float(leg.actual_stake),
                    'potential_payout': float(leg.potential_payout)
                }
                legs_data.append(leg_data)
            
            if legs_data:
                self.client.table('arbitrage_legs').insert(legs_data).execute()
            
            logger.info(f"Saved opportunity {opp_id} with {len(legs_data)} legs")
            return result.data[0]
            
        except Exception as e:
            logger.error(f"Error saving opportunity: {str(e)}")
            raise
    
    def get_opportunities(
        self,
        sport: Optional[Sport] = None,
        risk_tier: Optional[RiskTier] = None,
        min_profit_margin: Optional[float] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Retrieve arbitrage opportunities with optional filters.
        
        Args:
            sport: Filter by sport type
            risk_tier: Filter by risk tier
            min_profit_margin: Minimum profit margin threshold
            limit: Maximum number of results
            
        Returns:
            List of opportunity records
        """
        try:
            query = self.client.table('arbitrage_opportunities').select('*')
            
            if sport:
                query = query.eq('sport', sport.value)
            
            if risk_tier:
                query = query.eq('risk_tier', risk_tier.value)
            
            if min_profit_margin:
                query = query.gte('profit_margin', min_profit_margin)
            
            query = query.order('discovered_at', desc=True).limit(limit)
            
            result = query.execute()
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error retrieving opportunities: {str(e)}")
            raise
    
    def get_opportunity_legs(self, opportunity_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all legs for a specific opportunity.
        
        Args:
            opportunity_id: UUID of the opportunity
            
        Returns:
            List of leg records
        """
        try:
            result = self.client.table('arbitrage_legs').select('*').eq(
                'opportunity_id', opportunity_id
            ).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error retrieving opportunity legs: {str(e)}")
            raise
    
    # ============================================
    # TRADES
    # ============================================
    
    async def create_trade(self, trade: Trade) -> Dict[str, Any]:
        """
        Create a new trade record.
        
        Args:
            trade: Trade instance
            
        Returns:
            Created trade data
        """
        try:
            trade_data = {
                'id': str(trade.id),
                'user_id': str(trade.user_id),
                'opportunity_id': str(trade.opportunity.id),
                'status': trade.status.value,
                'execution_mode': trade.execution_mode.value,
                'total_stake': float(trade.stake_data.total_stake),
                'currency': trade.stake_data.currency,
                'expected_profit': float(trade.expected_profit),
                'actual_profit': float(trade.actual_profit) if trade.actual_profit else None,
                'fees_total': float(trade.stake_data.fees_included),
                'placed_bets': trade.placed_bets,
                'failed_bets': trade.failed_bets,
                'hedge_trades': trade.hedge_trades,
                'error_messages': trade.error_messages,
                'retry_count': trade.retry_count,
                'execution_time_ms': trade.execution_time_ms,
                'slippage': float(trade.slippage) if trade.slippage else None
            }
            
            result = self.client.table('trades').insert(trade_data).execute()
            
            if not result.data:
                raise Exception("Failed to create trade")
            
            logger.info(f"Created trade {result.data[0]['id']}")
            return result.data[0]
            
        except Exception as e:
            logger.error(f"Error creating trade: {str(e)}")
            raise
    
    async def update_trade_status(
        self,
        trade_id: str,
        status: TradeStatus,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update trade status and related fields.
        
        Args:
            trade_id: UUID of the trade
            status: New trade status
            additional_data: Additional fields to update
            
        Returns:
            Updated trade data
        """
        try:
            update_data = {'status': status.value}
            
            # Add timestamps based on status
            if status == TradeStatus.PLACING_BETS and not additional_data:
                update_data['started_at'] = datetime.utcnow().isoformat()
            elif status == TradeStatus.FILLED:
                update_data['completed_at'] = datetime.utcnow().isoformat()
            elif status == TradeStatus.SETTLED:
                update_data['settled_at'] = datetime.utcnow().isoformat()
            
            if additional_data:
                update_data.update(additional_data)
            
            result = self.client.table('trades').update(update_data).eq('id', trade_id).execute()
            
            logger.info(f"Updated trade {trade_id} status to {status.value}")
            return result.data[0] if result.data else {}
            
        except Exception as e:
            logger.error(f"Error updating trade status: {str(e)}")
            raise
    
    def get_user_trades(
        self,
        user_id: str,
        status: Optional[TradeStatus] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Retrieve trades for a specific user.
        
        Args:
            user_id: UUID of the user
            status: Filter by trade status
            limit: Maximum number of results
            
        Returns:
            List of trade records
        """
        try:
            query = self.client.table('trades').select('*').eq('user_id', user_id)
            
            if status:
                query = query.eq('status', status.value)
            
            query = query.order('created_at', desc=True).limit(limit)
            
            result = query.execute()
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error retrieving user trades: {str(e)}")
            raise
    
    # ============================================
    # HITL DECISIONS
    # ============================================
    
    async def log_hitl_decision(
        self,
        opportunity_id: str,
        user_id: str,
        decision: str,
        decision_reason: Optional[str] = None,
        modified_stake: Optional[Decimal] = None,
        risk_summary: Optional[Dict] = None,
        opportunity_snapshot: Optional[Dict] = None,
        presented_at: Optional[datetime] = None,
        decided_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Log a human-in-the-loop decision.
        
        Args:
            opportunity_id: UUID of the opportunity
            user_id: UUID of the user making the decision
            decision: Decision made ('approved', 'rejected', 'modified')
            decision_reason: Reason for the decision
            modified_stake: Modified stake amount if applicable
            risk_summary: Summary of risk factors
            opportunity_snapshot: Snapshot of opportunity data
            presented_at: When opportunity was presented
            decided_at: When decision was made
            
        Returns:
            Created decision record
        """
        try:
            now = datetime.utcnow()
            presented_at = presented_at or now
            decided_at = decided_at or now
            
            decision_data = {
                'id': str(uuid4()),
                'opportunity_id': opportunity_id,
                'user_id': user_id,
                'decision': decision,
                'decision_reason': decision_reason,
                'modified_stake': float(modified_stake) if modified_stake else None,
                'presented_at': presented_at.isoformat(),
                'decided_at': decided_at.isoformat(),
                'response_time_ms': int((decided_at - presented_at).total_seconds() * 1000),
                'risk_summary': risk_summary or {},
                'opportunity_snapshot': opportunity_snapshot or {}
            }
            
            result = self.client.table('hitl_decisions').insert(decision_data).execute()
            
            logger.info(f"Logged HITL decision: {decision} for opportunity {opportunity_id}")
            return result.data[0] if result.data else {}
            
        except Exception as e:
            logger.error(f"Error logging HITL decision: {str(e)}")
            raise
    
    # ============================================
    # AUTONOMOUS DECISIONS
    # ============================================
    
    async def log_autonomous_decision(
        self,
        opportunity_id: str,
        decision: str,
        confidence_score: float,
        reasoning: Dict[str, Any],
        risk_score: float,
        risk_factors: List[str]
    ) -> Dict[str, Any]:
        """
        Log an autonomous system decision.
        
        Args:
            opportunity_id: UUID of the opportunity
            decision: Decision made ('execute', 'skip', 'queue')
            confidence_score: Confidence in the decision
            reasoning: Detailed reasoning for the decision
            risk_score: Calculated risk score
            risk_factors: List of identified risk factors
            
        Returns:
            Created decision record
        """
        try:
            decision_data = {
                'id': str(uuid4()),
                'opportunity_id': opportunity_id,
                'decision': decision,
                'confidence_score': confidence_score,
                'reasoning': reasoning,
                'risk_score': risk_score,
                'risk_factors': risk_factors,
                'executed': False
            }
            
            result = self.client.table('autonomous_decisions').insert(decision_data).execute()
            
            logger.info(f"Logged autonomous decision: {decision} for opportunity {opportunity_id}")
            return result.data[0] if result.data else {}
            
        except Exception as e:
            logger.error(f"Error logging autonomous decision: {str(e)}")
            raise
    
    # ============================================
    # RISK ALERTS
    # ============================================
    
    async def create_risk_alert(
        self,
        alert_type: str,
        severity: str,
        title: str,
        description: str,
        user_id: Optional[str] = None,
        opportunity_id: Optional[str] = None,
        trade_id: Optional[str] = None,
        risk_metrics: Optional[Dict] = None,
        recommended_action: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a risk alert.
        
        Args:
            alert_type: Type of alert
            severity: Severity level ('low', 'medium', 'high', 'critical')
            title: Alert title
            description: Alert description
            user_id: Optional user ID
            opportunity_id: Optional opportunity ID
            trade_id: Optional trade ID
            risk_metrics: Optional risk metrics data
            recommended_action: Recommended action
            
        Returns:
            Created alert record
        """
        try:
            alert_data = {
                'id': str(uuid4()),
                'alert_type': alert_type,
                'severity': severity,
                'title': title,
                'description': description,
                'user_id': user_id,
                'opportunity_id': opportunity_id,
                'trade_id': trade_id,
                'risk_metrics': risk_metrics or {},
                'recommended_action': recommended_action,
                'resolved': False
            }
            
            result = self.client.table('risk_alerts').insert(alert_data).execute()
            
            logger.info(f"Created {severity} risk alert: {title}")
            return result.data[0] if result.data else {}
            
        except Exception as e:
            logger.error(f"Error creating risk alert: {str(e)}")
            raise
    
    def get_unresolved_alerts(
        self,
        user_id: Optional[str] = None,
        min_severity: str = 'low'
    ) -> List[Dict[str, Any]]:
        """
        Retrieve unresolved risk alerts.
        
        Args:
            user_id: Filter by user ID
            min_severity: Minimum severity level
            
        Returns:
            List of alert records
        """
        try:
            query = self.client.table('risk_alerts').select('*').eq('resolved', False)
            
            if user_id:
                query = query.eq('user_id', user_id)
            
            result = query.order('created_at', desc=True).execute()
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error retrieving unresolved alerts: {str(e)}")
            raise
    
    # ============================================
    # CIRCUIT BREAKER EVENTS
    # ============================================
    
    async def log_circuit_breaker_event(
        self,
        breaker_type: str,
        trigger_value: float,
        threshold_value: float,
        description: str,
        affected_operations: List[str]
    ) -> Dict[str, Any]:
        """
        Log a circuit breaker activation event.
        
        Args:
            breaker_type: Type of circuit breaker
            trigger_value: Value that triggered the breaker
            threshold_value: Threshold value
            description: Event description
            affected_operations: List of affected operations
            
        Returns:
            Created event record
        """
        try:
            event_data = {
                'id': str(uuid4()),
                'breaker_type': breaker_type,
                'trigger_value': trigger_value,
                'threshold_value': threshold_value,
                'description': description,
                'affected_operations': affected_operations,
                'resolved': False,
                'triggered_at': datetime.utcnow().isoformat()
            }
            
            result = self.client.table('circuit_breaker_events').insert(event_data).execute()
            
            logger.warning(f"Circuit breaker activated: {breaker_type}")
            return result.data[0] if result.data else {}
            
        except Exception as e:
            logger.error(f"Error logging circuit breaker event: {str(e)}")
            raise
    
    # ============================================
    # EXECUTION LOGS
    # ============================================
    
    async def add_execution_log(
        self,
        trade_id: str,
        log_level: str,
        message: str,
        details: Optional[Dict] = None,
        screenshot_url: Optional[str] = None,
        bookmaker: Optional[str] = None,
        step_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add an execution log entry.
        
        Args:
            trade_id: UUID of the trade
            log_level: Log level ('info', 'warning', 'error')
            message: Log message
            details: Additional details
            screenshot_url: URL to screenshot if applicable
            bookmaker: Bookmaker name
            step_name: Execution step name
            
        Returns:
            Created log record
        """
        try:
            log_data = {
                'id': str(uuid4()),
                'trade_id': trade_id,
                'log_level': log_level,
                'message': message,
                'details': details or {},
                'screenshot_url': screenshot_url,
                'bookmaker': bookmaker,
                'step_name': step_name
            }
            
            result = self.client.table('execution_logs').insert(log_data).execute()
            return result.data[0] if result.data else {}
            
        except Exception as e:
            logger.error(f"Error adding execution log: {str(e)}")
            raise
    
    # ============================================
    # PERFORMANCE METRICS
    # ============================================
    
    async def save_performance_metrics(
        self,
        user_id: Optional[str],
        period_start: datetime,
        period_end: datetime,
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Save performance metrics for a time period.
        
        Args:
            user_id: UUID of the user (None for system-wide)
            period_start: Start of the period
            period_end: End of the period
            metrics: Performance metrics data
            
        Returns:
            Created metrics record
        """
        try:
            metrics_data = {
                'id': str(uuid4()),
                'user_id': user_id,
                'period_start': period_start.isoformat(),
                'period_end': period_end.isoformat(),
                **metrics
            }
            
            result = self.client.table('performance_metrics').insert(metrics_data).execute()
            
            logger.info(f"Saved performance metrics for period {period_start} to {period_end}")
            return result.data[0] if result.data else {}
            
        except Exception as e:
            logger.error(f"Error saving performance metrics: {str(e)}")
            raise
    
    # ============================================
    # STORAGE OPERATIONS
    # ============================================
    
    async def upload_screenshot(
        self,
        file_path: str,
        screenshot_name: str,
        bucket: str = 'arbitech-screenshots'
    ) -> str:
        """
        Upload a screenshot to storage.
        
        Args:
            file_path: Local path to the screenshot file
            screenshot_name: Name for the screenshot in storage
            bucket: Storage bucket name
            
        Returns:
            Public URL of the uploaded screenshot
        """
        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Upload to Supabase Storage
            result = self.client.storage.from_(bucket).upload(
                screenshot_name,
                file_data,
                {'content-type': 'image/png'}
            )
            
            # Get public URL
            public_url = self.client.storage.from_(bucket).get_public_url(screenshot_name)
            
            logger.info(f"Uploaded screenshot: {screenshot_name}")
            return public_url
            
        except Exception as e:
            logger.error(f"Error uploading screenshot: {str(e)}")
            raise
    
    async def upload_log_file(
        self,
        file_path: str,
        log_name: str,
        bucket: str = 'arbitech-logs'
    ) -> str:
        """
        Upload a log file to storage.
        
        Args:
            file_path: Local path to the log file
            log_name: Name for the log in storage
            bucket: Storage bucket name
            
        Returns:
            Public URL of the uploaded log
        """
        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Determine content type
            content_type = 'application/json' if log_name.endswith('.json') else 'text/plain'
            
            # Upload to Supabase Storage
            result = self.client.storage.from_(bucket).upload(
                log_name,
                file_data,
                {'content-type': content_type}
            )
            
            # Get public URL
            public_url = self.client.storage.from_(bucket).get_public_url(log_name)
            
            logger.info(f"Uploaded log file: {log_name}")
            return public_url
            
        except Exception as e:
            logger.error(f"Error uploading log file: {str(e)}")
            raise
    
    # ============================================
    # REAL-TIME SUBSCRIPTIONS
    # ============================================
    
    def subscribe_to_opportunities(self, callback):
        """
        Subscribe to real-time opportunity updates.
        
        Args:
            callback: Function to call when opportunities are updated
        """
        try:
            subscription = self.client.table('arbitrage_opportunities').on(
                'INSERT', callback
            ).subscribe()
            
            self.subscriptions.append(subscription)
            logger.info("Subscribed to opportunity updates")
            
        except Exception as e:
            logger.error(f"Error subscribing to opportunities: {str(e)}")
            raise
    
    def subscribe_to_trade_status(self, user_id: str, callback):
        """
        Subscribe to real-time trade status updates for a user.
        
        Args:
            user_id: UUID of the user
            callback: Function to call when trade status is updated
        """
        try:
            subscription = self.client.table('trades').on(
                'UPDATE', callback
            ).eq('user_id', user_id).subscribe()
            
            self.subscriptions.append(subscription)
            logger.info(f"Subscribed to trade updates for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error subscribing to trade updates: {str(e)}")
            raise
    
    def unsubscribe_all(self):
        """Unsubscribe from all active subscriptions."""
        for subscription in self.subscriptions:
            try:
                subscription.unsubscribe()
            except Exception as e:
                logger.error(f"Error unsubscribing: {str(e)}")
        
        self.subscriptions = []
        logger.info("Unsubscribed from all real-time updates")


# Convenience singleton instance
_data_layer = None


def get_data_layer() -> SupabaseDataLayer:
    """Get or create the global SupabaseDataLayer instance."""
    global _data_layer
    if _data_layer is None:
        _data_layer = SupabaseDataLayer()
    return _data_layer
