"""
HITL Opportunity Presenter

Component responsible for presenting arbitrage opportunities to users in various formats
with rich context, formatting, and interactive elements. Integrates with multiple 
presentation backends (console, web, GUI, etc.) and provides customizable templates.
"""

import asyncio
import logging
import json
import textwrap
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum

from ..storage.models import ArbitrageOpportunity, ArbitrageLeg, RiskTier, Sport
from ..storage.audit_logger import get_audit_logger
from ..utils.logger import get_logger


class PresentationFormat(str, Enum):
    """Supported presentation formats."""
    CONSOLE = "console"
    HTML = "html"
    JSON = "json"
    TABLE = "table"
    WEB_DASHBOARD = "web_dashboard"
    EMAIL = "email"
    SLACK = "slack"
    DISCORD = "discord"


class PresentationPriority(str, Enum):
    """Presentation priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PresentationStyle(str, Enum):
    """Presentation style options."""
    COMPACT = "compact"
    DETAILED = "detailed"
    SUMMARY = "summary"
    FULL = "full"
    COMPARISON = "comparison"


@dataclass
class PresentationContext:
    """Context for opportunity presentation."""
    # Basic information
    opportunity: ArbitrageOpportunity
    format: PresentationFormat = PresentationFormat.CONSOLE
    style: PresentationStyle = PresentationStyle.DETAILED
    priority: PresentationPriority = PresentationPriority.MEDIUM
    
    # Presentation options
    show_risk_analysis: bool = True
    show_stake_breakdown: bool = True
    show_bookmaker_info: bool = True
    show_comparison_data: bool = False
    show_historical_context: bool = False
    
    # User preferences
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    preferences: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    presentation_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None


@dataclass
class PresentationResult:
    """Result of opportunity presentation."""
    # Success status
    success: bool = True
    presentation_id: str = ""
    
    # Presentation output
    formatted_content: str = ""
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    # Delivery information
    delivered_to: List[str] = field(default_factory=list)
    delivery_status: Dict[str, str] = field(default_factory=dict)
    
    # Metadata
    presentation_time: float = 0.0
    format_used: str = ""
    errors: List[str] = field(default_factory=list)
    
    # Analytics
    view_count: int = 0
    interaction_data: Dict[str, Any] = field(default_factory=dict)


class HITLPresenter:
    """
    HITL Opportunity Presenter - handles presenting opportunities to users
    in various formats and interfaces.
    """
    
    def __init__(self, audit_logger=None, logger: Optional[logging.Logger] = None):
        """Initialize the HITL presenter."""
        self.audit_logger = audit_logger or get_audit_logger()
        self.logger = logger or get_logger('hitl_presenter')
        
        # Presentation templates and formatters
        self._templates = self._initialize_templates()
        self._formatters = self._initialize_formatters()
        
        # Active presentations tracking
        self._active_presentations: Dict[str, PresentationContext] = {}
        self._presentation_history: List[PresentationResult] = []
        
        # Statistics
        self._stats = {
            'presentations_created': 0,
            'presentations_delivered': 0,
            'formats_used': {},
            'avg_presentation_time': 0.0,
            'total_presentation_time': 0.0
        }
    
    def _initialize_templates(self) -> Dict[str, Dict[str, str]]:
        """Initialize presentation templates for different formats."""
        return {
            PresentationFormat.CONSOLE.value: {
                PresentationStyle.COMPACT.value: """
📊 ARBITRAGE OPPORTUNITY {priority_indicator}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{header_line}
Risk Tier: {risk_tier} | Profit: {profit_margin:.2%} | Stake: {total_stake}
Bookmakers: {bookmakers}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                """.strip(),
                
                PresentationStyle.DETAILED.value: """
🎯 ARBITRAGE OPPORTUNITY DETECTED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 Event Information:
   Sport: {sport}
   Event: {event_name}
   Date: {event_date}
   Market: {market_type}

💰 Financial Details:
   Total Stake: {total_stake} {currency}
   Expected Profit: {profit_amount} {currency}
   Profit Margin: {profit_margin:.2%}
   Guaranteed Profit: {guaranteed_profit}

🏆 Betting Legs:
{legs_table}

⚠️  Risk Analysis:
   Risk Tier: {risk_tier}
   Liquidity Checked: {liquidity_checked}
   Odds Freshness: {odds_freshness}
   
⏰ Timing:
   Discovered: {discovered_at}
   Expires: {expires_at}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                """.strip(),
                
                PresentationStyle.SUMMARY.value: """
🔍 OPPORTUNITY SUMMARY
Sport: {sport} | {event_name}
Profit: {profit_amount} {currency} ({profit_margin:.2%})
Risk: {risk_tier} | Stake: {total_stake} {currency}
Bookmakers: {bookmakers}
                """.strip()
            },
            
            PresentationFormat.HTML.value: {
                PresentationStyle.DETAILED.value: """
<!DOCTYPE html>
<html>
<head>
    <title>Arbitrage Opportunity</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f8ff; padding: 20px; border-radius: 8px; }}
        .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .profit {{ color: green; font-weight: bold; }}
        .risk-tier {{ font-weight: bold; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 Arbitrage Opportunity</h1>
        <p><strong>Event:</strong> {event_name}</p>
        <p><strong>Sport:</strong> {sport}</p>
        <p><strong>Date:</strong> {event_date}</p>
    </div>
    
    <div class="section">
        <h2>💰 Financial Details</h2>
        <p>Total Stake: <strong>{total_stake} {currency}</strong></p>
        <p>Expected Profit: <span class="profit">{profit_amount} {currency}</span></p>
        <p>Profit Margin: <span class="profit">{profit_margin:.2%}</span></p>
        <p>Guaranteed Profit: {guaranteed_profit}</p>
    </div>
    
    <div class="section">
        <h2>🏆 Betting Legs</h2>
        <table>
            <tr>
                <th>Bookmaker</th>
                <th>Outcome</th>
                <th>Odds</th>
                <th>Stake</th>
                <th>Payout</th>
            </tr>
            {legs_table_rows}
        </table>
    </div>
    
    <div class="section">
        <h2>⚠️ Risk Analysis</h2>
        <p>Risk Tier: <span class="risk-tier">{risk_tier}</span></p>
        <p>Liquidity Checked: {liquidity_checked}</p>
        <p>Odds Freshness: {odds_freshness}</p>
    </div>
    
    <div class="section">
        <h2>⏰ Timing</h2>
        <p>Discovered: {discovered_at}</p>
        <p>Expires: {expires_at}</p>
    </div>
</body>
</html>
                """.strip()
            },
            
            PresentationFormat.JSON.value: {
                PresentationStyle.FULL.value: """
{
  "opportunity": {
    "id": "{opportunity_id}",
    "sport": "{sport}",
    "event_name": "{event_name}",
    "event_date": "{event_date}",
    "market_type": "{market_type}",
    "legs": [{legs_json}],
    "total_stake": "{total_stake}",
    "profit_margin": {profit_margin},
    "profit_amount": "{profit_amount}",
    "guaranteed_profit": {guaranteed_profit},
    "risk_tier": "{risk_tier}",
    "liquidity_checked": {liquidity_checked},
    "odds_freshness": "{odds_freshness}",
    "discovered_at": "{discovered_at}",
    "expires_at": "{expires_at}"
  },
  "presentation": {
    "format": "{format}",
    "style": "{style}",
    "priority": "{priority}",
    "created_at": "{created_at}"
  }
}
                """.strip()
            }
        }
    
    def _initialize_formatters(self) -> Dict[str, Callable]:
        """Initialize custom formatters for different data types."""
        return {
            'currency': self._format_currency,
            'percentage': self._format_percentage,
            'datetime': self._format_datetime,
            'table': self._format_table,
            'risk_indicator': self._format_risk_indicator
        }
    
    def _format_currency(self, amount: Union[Decimal, float], currency: str = "USD") -> str:
        """Format currency amount."""
        if isinstance(amount, Decimal):
            amount = float(amount)
        return f"{amount:.2f} {currency}"
    
    def _format_percentage(self, value: Union[Decimal, float]) -> str:
        """Format percentage value."""
        if isinstance(value, Decimal):
            value = float(value)
        return f"{value:.2%}"
    
    def _format_datetime(self, dt: datetime) -> str:
        """Format datetime for display."""
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    
    def _format_table(self, legs: List[ArbitrageLeg], currency: str = "USD") -> str:
        """Format legs as a table."""
        if not legs:
            return "No betting legs available"
        
        # Calculate column widths
        bookmaker_width = max(len("Bookmaker"), max(len(leg.bookmaker) for leg in legs))
        outcome_width = max(len("Outcome"), max(len(leg.event_outcome) for leg in legs))
        odds_width = max(len("Odds"), max(len(str(leg.odds)) for leg in legs))
        stake_width = max(len("Stake"), max(len(self._format_currency(leg.actual_stake, currency)) for leg in legs))
        
        # Header
        table = f"{'Bookmaker':<{bookmaker_width}} {'Outcome':<{outcome_width}} {'Odds':<{odds_width}} {'Stake':<{stake_width}} {'Payout':<{stake_width}}\n"
        table += "-" * (bookmaker_width + outcome_width + odds_width + stake_width + stake_width + 4) + "\n"
        
        # Rows
        for leg in legs:
            payout = self._format_currency(leg.potential_payout, currency)
            stake = self._format_currency(leg.actual_stake, currency)
            table += f"{leg.bookmaker:<{bookmaker_width}} {leg.event_outcome:<{outcome_width}} {str(leg.odds):<{odds_width}} {stake:<{stake_width}} {payout:<{stake_width}}\n"
        
        return table
    
    def _format_risk_indicator(self, risk_tier: RiskTier) -> str:
        """Format risk tier with indicator."""
        indicators = {
            RiskTier.TIER_A: "🟢 LOW RISK",
            RiskTier.TIER_B: "🟡 MEDIUM RISK",
            RiskTier.TIER_C: "🟠 HIGH RISK",
            RiskTier.TIER_D: "🔴 VERY HIGH RISK"
        }
        return indicators.get(risk_tier, f"UNKNOWN ({risk_tier})")
    
    async def present_opportunity(
        self,
        opportunity: ArbitrageOpportunity,
        format: PresentationFormat = PresentationFormat.CONSOLE,
        style: PresentationStyle = PresentationStyle.DETAILED,
        **kwargs
    ) -> PresentationResult:
        """
        Present an arbitrage opportunity to the user.
        
        Args:
            opportunity: The arbitrage opportunity to present
            format: Output format (console, html, json, etc.)
            style: Presentation style (compact, detailed, summary, etc.)
            **kwargs: Additional presentation options
        
        Returns:
            PresentationResult with the formatted presentation
        """
        start_time = datetime.utcnow()
        
        try:
            # Create presentation context
            context = PresentationContext(
                opportunity=opportunity,
                format=format,
                style=style,
                **kwargs
            )
            
            # Generate presentation ID
            context.presentation_id = f"present_{opportunity.id}_{int(start_time.timestamp())}"
            
            # Track active presentation
            self._active_presentations[context.presentation_id] = context
            
            # Format the opportunity
            formatted_content = await self._format_opportunity(context)
            
            # Create result
            result = PresentationResult(
                success=True,
                presentation_id=context.presentation_id,
                formatted_content=formatted_content,
                raw_data=self._extract_opportunity_data(opportunity),
                format_used=format.value,
                presentation_time=(datetime.utcnow() - start_time).total_seconds()
            )
            
            # Update statistics
            self._stats['presentations_created'] += 1
            self._stats['total_presentation_time'] += result.presentation_time
            self._stats['formats_used'][format.value] = self._stats['formats_used'].get(format.value, 0) + 1
            self._stats['avg_presentation_time'] = (
                self._stats['total_presentation_time'] / self._stats['presentations_created']
            )
            
            # Log presentation event
            await self._log_presentation_event(
                context.presentation_id, "opportunity_presented",
                {
                    'format': format.value,
                    'style': style.value,
                    'opportunity_id': str(opportunity.id),
                    'presentation_time': result.presentation_time
                }
            )
            
            self.logger.debug(
                "Opportunity presented successfully",
                presentation_id=context.presentation_id,
                format=format.value,
                style=style.value,
                presentation_time=result.presentation_time
            )
            
            return result
            
        except Exception as e:
            self.logger.error(
                "Failed to present opportunity",
                opportunity_id=str(opportunity.id),
                format=format.value,
                style=style.value,
                error=str(e)
            )
            
            return PresentationResult(
                success=False,
                presentation_id="",
                formatted_content="",
                errors=[str(e)],
                presentation_time=(datetime.utcnow() - start_time).total_seconds()
            )
        
        finally:
            # Cleanup active presentation
            if hasattr(context, 'presentation_id') and context.presentation_id in self._active_presentations:
                del self._active_presentations[context.presentation_id]
    
    async def _format_opportunity(self, context: PresentationContext) -> str:
        """Format the opportunity using the appropriate template."""
        opportunity = context.opportunity
        
        # Get template
        template = self._templates.get(context.format.value, {}).get(context.style.value)
        if not template:
            raise ValueError(f"No template found for format {context.format.value} and style {context.style.value}")
        
        # Prepare template data
        template_data = self._prepare_template_data(opportunity, context)
        
        # Format using template
        if context.format == PresentationFormat.HTML:
            return await self._format_html(template, template_data)
        elif context.format == PresentationFormat.JSON:
            return await self._format_json(template, template_data)
        elif context.format == PresentationFormat.CONSOLE:
            return await self._format_console(template, template_data)
        else:
            # Generic formatting
            return template.format(**template_data)
    
    def _prepare_template_data(self, opportunity: ArbitrageOpportunity, context: PresentationContext) -> Dict[str, Any]:
        """Prepare data for template formatting."""
        # Base data
        data = {
            'opportunity_id': str(opportunity.id),
            'sport': opportunity.sport.value.title(),
            'event_name': opportunity.event_name,
            'event_date': self._format_datetime(opportunity.event_date),
            'market_type': opportunity.market_type.title(),
            'total_stake': str(opportunity.total_stake),
            'profit_amount': str(opportunity.profit_amount),
            'profit_margin': opportunity.profit_margin,
            'guaranteed_profit': "Yes" if opportunity.guaranteed_profit else "No",
            'risk_tier': self._format_risk_indicator(opportunity.risk_tier),
            'liquidity_checked': "Yes" if opportunity.liquidity_checked else "No",
            'odds_freshness': self._format_datetime(opportunity.odds_freshness),
            'discovered_at': self._format_datetime(opportunity.discovered_at),
            'expires_at': self._format_datetime(opportunity.expires_at) if opportunity.expires_at else "No expiry",
            'bookmakers': ', '.join(set(leg.bookmaker for leg in opportunity.legs)),
            'currency': 'USD',  # This should come from configuration
            'format': context.format.value,
            'style': context.style.value,
            'priority': context.priority.value,
            'created_at': self._format_datetime(context.created_at)
        }
        
        # Add legs data
        data['legs_table'] = self._format_table(opportunity.legs, data['currency'])
        data['legs_json'] = self._format_legs_json(opportunity.legs)
        data['legs_table_rows'] = self._format_legs_table_rows(opportunity.legs, data['currency'])
        
        # Add priority indicator
        priority_indicators = {
            PresentationPriority.LOW: "🔵",
            PresentationPriority.MEDIUM: "🟡", 
            PresentationPriority.HIGH: "🟠",
            PresentationPriority.CRITICAL: "🔴"
        }
        data['priority_indicator'] = priority_indicators.get(context.priority, "⚪")
        
        # Add header line for compact format
        data['header_line'] = f"{opportunity.sport.value.title()} | {opportunity.event_name}"
        
        return data
    
    def _format_legs_json(self, legs: List[ArbitrageLeg]) -> str:
        """Format legs as JSON array."""
        leg_data = []
        for leg in legs:
            leg_data.append({
                'bookmaker': leg.bookmaker,
                'outcome': leg.event_outcome,
                'odds': str(leg.odds),
                'stake': str(leg.actual_stake),
                'payout': str(leg.potential_payout)
            })
        return json.dumps(leg_data, indent=2)
    
    def _format_legs_table_rows(self, legs: List[ArbitrageLeg], currency: str) -> str:
        """Format legs as HTML table rows."""
        if not legs:
            return "<tr><td colspan='5'>No betting legs</td></tr>"
        
        rows = []
        for leg in legs:
            row = f"""
            <tr>
                <td>{leg.bookmaker}</td>
                <td>{leg.event_outcome}</td>
                <td>{leg.odds}</td>
                <td>{self._format_currency(leg.actual_stake, currency)}</td>
                <td>{self._format_currency(leg.potential_payout, currency)}</td>
            </tr>
            """.strip()
            rows.append(row)
        
        return '\n'.join(rows)
    
    async def _format_html(self, template: str, data: Dict[str, Any]) -> str:
        """Format as HTML."""
        return template.format(**data)
    
    async def _format_json(self, template: str, data: Dict[str, Any]) -> str:
        """Format as JSON."""
        return template.format(**data)
    
    async def _format_console(self, template: str, data: Dict[str, Any]) -> str:
        """Format for console display."""
        return template.format(**data)
    
    def _extract_opportunity_data(self, opportunity: ArbitrageOpportunity) -> Dict[str, Any]:
        """Extract raw opportunity data for API responses."""
        return {
            'id': str(opportunity.id),
            'sport': opportunity.sport.value,
            'event_name': opportunity.event_name,
            'event_date': opportunity.event_date.isoformat(),
            'market_type': opportunity.market_type,
            'legs': [
                {
                    'bookmaker': leg.bookmaker,
                    'outcome': leg.event_outcome,
                    'odds': float(leg.odds),
                    'stake': float(leg.actual_stake),
                    'payout': float(leg.potential_payout)
                }
                for leg in opportunity.legs
            ],
            'total_stake': float(opportunity.total_stake),
            'profit_margin': float(opportunity.profit_margin),
            'profit_amount': float(opportunity.profit_amount),
            'guaranteed_profit': opportunity.guaranteed_profit,
            'risk_tier': opportunity.risk_tier.value,
            'liquidity_checked': opportunity.liquidity_checked,
            'odds_freshness': opportunity.odds_freshness.isoformat(),
            'discovered_at': opportunity.discovered_at.isoformat(),
            'expires_at': opportunity.expires_at.isoformat() if opportunity.expires_at else None,
            'validation_errors': opportunity.validation_errors
        }
    
    async def _log_presentation_event(self, presentation_id: str, event_type: str, details: Dict[str, Any]) -> None:
        """Log presentation events to audit trail."""
        try:
            await self.audit_logger.log_user_action(
                action=f"hitl_presentation_{event_type}",
                resource=f"presentation:{presentation_id}",
                details={
                    'presentation_id': presentation_id,
                    'event_type': event_type,
                    'timestamp': datetime.utcnow().isoformat(),
                    **details
                }
            )
        except Exception as e:
            self.logger.error("Failed to log presentation event", error=str(e))
    
    def get_presentation_stats(self) -> Dict[str, Any]:
        """Get presentation statistics."""
        return self._stats.copy()
    
    def get_active_presentations(self) -> List[Dict[str, Any]]:
        """Get all active presentations."""
        return [
            {
                'presentation_id': pid,
                'opportunity_id': str(ctx.opportunity.id),
                'format': ctx.format.value,
                'style': ctx.style.value,
                'priority': ctx.priority.value,
                'created_at': ctx.created_at.isoformat(),
                'expires_at': ctx.expires_at.isoformat() if ctx.expires_at else None,
                'user_id': ctx.user_id,
                'preferences': ctx.preferences
            }
            for pid, ctx in self._active_presentations.items()
        ]
    
    async def present_multiple_opportunities(
        self,
        opportunities: List[ArbitrageOpportunity],
        format: PresentationFormat = PresentationFormat.CONSOLE,
        style: PresentationStyle = PresentationStyle.SUMMARY,
        **kwargs
    ) -> List[PresentationResult]:
        """
        Present multiple opportunities in a single batch.
        
        Args:
            opportunities: List of opportunities to present
            format: Output format
            style: Presentation style
            **kwargs: Additional presentation options
        
        Returns:
            List of PresentationResult objects
        """
        results = []
        
        for opportunity in opportunities:
            result = await self.present_opportunity(opportunity, format, style, **kwargs)
            results.append(result)
        
        return results
    
    def create_comparison_presentation(
        self,
        opportunities: List[ArbitrageOpportunity],
        format: PresentationFormat = PresentationFormat.CONSOLE
    ) -> PresentationResult:
        """
        Create a comparison presentation showing multiple opportunities side by side.
        
        Args:
            opportunities: List of opportunities to compare
            format: Output format
        
        Returns:
            PresentationResult with comparison data
        """
        # This would implement comparison logic
        # For now, return a basic summary
        summary_text = f"Comparison of {len(opportunities)} opportunities:\n\n"
        
        for i, opp in enumerate(opportunities, 1):
            summary_text += f"{i}. {opp.event_name} ({opp.sport.value})\n"
            summary_text += f"   Profit: {opp.profit_amount} ({opp.profit_margin:.2%})\n"
            summary_text += f"   Risk: {opp.risk_tier.value}\n\n"
        
        return PresentationResult(
            success=True,
            presentation_id=f"comparison_{int(datetime.utcnow().timestamp())}",
            formatted_content=summary_text,
            raw_data={
                'comparison_count': len(opportunities),
                'opportunities': [self._extract_opportunity_data(opp) for opp in opportunities]
            }
        )
    
    def cleanup_expired_presentations(self) -> int:
        """Clean up expired presentations and return count cleaned."""
        current_time = datetime.utcnow()
        expired_ids = []
        
        for pid, ctx in self._active_presentations.items():
            if ctx.expires_at and current_time > ctx.expires_at:
                expired_ids.append(pid)
        
        # Remove expired presentations
        for pid in expired_ids:
            del self._active_presentations[pid]
        
        return len(expired_ids)


# Example usage
if __name__ == "__main__":
    import asyncio
    from decimal import Decimal
    
    async def main():
        """Example usage of HITL Presenter."""
        
        presenter = HITLPresenter()
        
        # Create sample opportunity
        opportunity = ArbitrageOpportunity(
            sport=Sport.FOOTBALL,
            event_name="Liverpool vs Manchester United",
            event_date=datetime.utcnow() + timedelta(days=1),
            market_type="match_winner",
            legs=[
                ArbitrageLeg(
                    bookmaker="bet365",
                    event_outcome="Liverpool",
                    odds=Decimal("2.10"),
                    implied_probability=Decimal("0.4762"),
                    stake_percentage=Decimal("0.5"),
                    actual_stake=Decimal("100.00"),
                    potential_payout=Decimal("210.00")
                ),
                ArbitrageLeg(
                    bookmaker="william_hill",
                    event_outcome="Manchester United",
                    odds=Decimal("2.05"),
                    implied_probability=Decimal("0.4878"),
                    stake_percentage=Decimal("0.5"),
                    actual_stake=Decimal("100.00"),
                    potential_payout=Decimal("205.00")
                )
            ],
            total_stake=Decimal("200.00"),
            profit_margin=Decimal("0.025"),
            profit_amount=Decimal("5.00"),
            risk_tier=RiskTier.TIER_A,
            source_scanner="test_scanner"
        )
        
        # Present in different formats
        formats = [
            (PresentationFormat.CONSOLE, PresentationStyle.DETAILED),
            (PresentationFormat.HTML, PresentationStyle.DETAILED),
            (PresentationFormat.JSON, PresentationStyle.FULL)
        ]
        
        for format_type, style in formats:
            print(f"\n=== {format_type.value.upper()} ({style.value}) ===\n")
            result = await presenter.present_opportunity(
                opportunity, 
                format=format_type, 
                style=style
            )
            print(result.formatted_content)
            print(f"\nPresentation time: {result.presentation_time:.3f}s")
        
        # Get statistics
        stats = presenter.get_presentation_stats()
        print(f"\nStatistics: {stats}")
    
    asyncio.run(main())
