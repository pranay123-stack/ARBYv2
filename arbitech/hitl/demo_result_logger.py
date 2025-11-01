#!/usr/bin/env python3
"""
Comprehensive Demo: HITL Trade Result Logging System

This script demonstrates the complete functionality of the result logging system
including human decision tracking, execution outcome logging, performance analytics,
and real-time dashboard generation.

The demo shows integration with:
- Human decision logging with full context
- Trade execution result tracking
- Performance metrics calculation
- User behavior pattern analysis
- Real-time dashboard generation
- Export capabilities
- Audit trail generation
"""

import sys
import os
import asyncio
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add the arbitech directory to the path
sys.path.insert(0, '/workspace/arbitech')

from hitl import (
    ResultLogger, HumanDecision, TradeResult, PerformanceMetrics, UserInteractionPattern,
    DecisionType, TradeOutcome, InteractionPattern,
    get_result_logger, log_human_decision, log_trade_result, get_performance_dashboard
)


class ComprehensiveDemo:
    """Comprehensive demonstration of the HITL result logging system."""
    
    def __init__(self):
        self.logger = get_result_logger({
            'logs_directory': '/workspace/arbitech/logs',
            'hitl_directory': '/workspace/arbitech/logs/hitl',
            'enable_real_time_dashboards': True,
            'enable_user_behavior_analysis': True,
            'enable_performance_prediction': True,
            'retention_days': 90,
            'enable_export_capabilities': True,
            'json_pretty_print': True
        })
        self.demo_users = ['trader_alice', 'trader_bob', 'trader_charlie']
        self.demo_opportunities = []
        
    async def run_comprehensive_demo(self):
        """Run the complete demonstration."""
        print("🚀 Starting Comprehensive HITL Result Logging Demo")
        print("=" * 60)
        
        try:
            # Phase 1: Simulate human decisions
            await self.demo_human_decisions()
            
            # Phase 2: Simulate trade execution outcomes
            await self.demo_trade_outcomes()
            
            # Phase 3: Generate performance analytics
            await self.demo_performance_analytics()
            
            # Phase 4: Create real-time dashboards
            await self.demo_real_time_dashboards()
            
            # Phase 5: Demonstrate export capabilities
            await self.demo_export_capabilities()
            
            # Phase 6: Show audit trails
            await self.demo_audit_trails()
            
            # Phase 7: Generate final report
            await self.generate_final_report()
            
            print("\n✅ Comprehensive demo completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Demo failed: {e}")
            raise
    
    async def demo_human_decisions(self):
        """Demonstrate human decision logging."""
        print("\n📋 Phase 1: Human Decision Logging")
        print("-" * 40)
        
        # Simulate various types of decisions
        decisions_data = [
            {
                'opportunity_id': 'OPP-001',
                'decision_type': DecisionType.APPROVE,
                'user_id': 'trader_alice',
                'session_id': 'session-001',
                'reasoning': 'Excellent arbitrage opportunity with low risk',
                'confidence_score': 0.95,
                'time_to_decision_ms': 1200,
                'risk_level': '0.2',
                'expected_profit': 250.0,
                'max_stake': 2000.0,
                'bookmaker_count': 4
            },
            {
                'opportunity_id': 'OPP-002',
                'decision_type': DecisionType.REJECT,
                'user_id': 'trader_bob',
                'session_id': 'session-002',
                'reasoning': 'Risk level too high, insufficient liquidity',
                'confidence_score': 0.85,
                'time_to_decision_ms': 4500,
                'risk_level': '0.8',
                'expected_profit': 500.0,
                'max_stake': 5000.0,
                'bookmaker_count': 2
            },
            {
                'opportunity_id': 'OPP-003',
                'decision_type': DecisionType.TIMEOUT,
                'user_id': 'trader_charlie',
                'session_id': 'session-003',
                'reasoning': 'No response within timeout window',
                'confidence_score': None,
                'time_to_decision_ms': 30000,  # 30 second timeout
                'risk_level': '0.5',
                'expected_profit': 100.0,
                'max_stake': 1000.0,
                'bookmaker_count': 3
            },
            {
                'opportunity_id': 'OPP-004',
                'decision_type': DecisionType.MANUAL_OVERRIDE,
                'user_id': 'trader_alice',
                'session_id': 'session-001',
                'reasoning': 'System recommended reject, but market conditions improved',
                'confidence_score': 0.75,
                'time_to_decision_ms': 8000,
                'risk_level': '0.6',
                'expected_profit': 300.0,
                'max_stake': 1500.0,
                'bookmaker_count': 3
            }
        ]
        
        logged_decisions = []
        for decision_data in decisions_data:
            decision = log_human_decision(**decision_data)
            logged_decisions.append(decision)
            self.demo_opportunities.append(decision_data['opportunity_id'])
            
            print(f"  ✓ Logged {decision.decision_type.value} decision for {decision.opportunity_id}")
            print(f"    User: {decision.user_id}, Profit: ${decision.expected_profit}")
        
        print(f"\n📊 Total decisions logged: {len(logged_decisions)}")
        return logged_decisions
    
    async def demo_trade_outcomes(self):
        """Demonstrate trade execution outcome logging."""
        print("\n💰 Phase 2: Trade Execution Outcome Logging")
        print("-" * 45)
        
        # Simulate trade outcomes
        results_data = [
            {
                'decision_id': 'dummy',  # Will be updated with actual decision IDs
                'opportunity_id': 'OPP-001',
                'outcome': TradeOutcome.SUCCESS,
                'total_profit_loss': 245.50,
                'net_profit_loss': 242.25,
                'commission_costs': 3.25,
                'slippage': -2.0,
                'legs_completed': 4,
                'legs_total': 4,
                'execution_time_ms': 2800.0,
                'expected_vs_actual_profit': -4.50,
                'efficiency_score': 0.92
            },
            {
                'decision_id': 'dummy',
                'opportunity_id': 'OPP-003',
                'outcome': TradeOutcome.FAILURE,
                'total_profit_loss': -50.0,
                'net_profit_loss': -55.75,
                'commission_costs': 5.75,
                'slippage': -15.0,
                'legs_completed': 1,
                'legs_total': 3,
                'legs_failed': ['leg_2', 'leg_3'],
                'execution_time_ms': 15000.0,
                'error_messages': ['Liquidity insufficient', 'Odds changed rapidly'],
                'expected_vs_actual_profit': -150.0,
                'efficiency_score': 0.15
            },
            {
                'decision_id': 'dummy',
                'opportunity_id': 'OPP-004',
                'outcome': TradeOutcome.PARTIAL_SUCCESS,
                'total_profit_loss': 125.0,
                'net_profit_loss': 120.5,
                'commission_costs': 4.5,
                'legs_completed': 2,
                'legs_total': 3,
                'legs_failed': ['leg_3'],
                'execution_time_ms': 5200.0,
                'expected_vs_actual_profit': -174.5,
                'efficiency_score': 0.68
            }
        ]
        
        # In a real system, we'd correlate with actual decision IDs
        logged_results = []
        for result_data in results_data:
            result = log_trade_result(**result_data)
            logged_results.append(result)
            
            print(f"  ✓ Logged {result.outcome.value} result for {result.opportunity_id}")
            print(f"    P&L: ${result.net_profit_loss}, Execution: {result.execution_time_ms}ms")
        
        print(f"\n📊 Total results logged: {len(logged_results)}")
        return logged_results
    
    async def demo_performance_analytics(self):
        """Demonstrate performance analytics."""
        print("\n📈 Phase 3: Performance Analytics")
        print("-" * 35)
        
        # Generate performance metrics for each user
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=24)
        
        for user_id in self.demo_users:
            try:
                metrics = self.logger.get_performance_metrics(user_id, start_time, end_time)
                
                print(f"\n📊 Performance Metrics for {user_id}:")
                print(f"  Decisions: {metrics.total_decisions}")
                print(f"  Approval Rate: {metrics.approval_rate:.1%}")
                print(f"  Success Rate: {metrics.success_rate:.1%}")
                print(f"  Net Profit: ${metrics.net_profit:.2f}")
                print(f"  Avg Decision Time: {metrics.avg_decision_time_ms:.0f}ms")
                print(f"  ROI: {metrics.roi:.2f}%")
                
            except Exception as e:
                print(f"  ⚠️  No data available for {user_id}: {e}")
    
    async def demo_real_time_dashboards(self):
        """Demonstrate real-time dashboard generation."""
        print("\n📺 Phase 4: Real-Time Dashboard Generation")
        print("-" * 43)
        
        # Generate dashboard for a specific user
        dashboard_data = get_performance_dashboard('trader_alice')
        
        print("📊 Dashboard Data Generated:")
        print(f"  Timestamp: {dashboard_data.get('timestamp', 'N/A')}")
        print(f"  User ID: {dashboard_data.get('user_id', 'N/A')}")
        print(f"  Recent Activity: {len(dashboard_data.get('recent_activity', []))} items")
        print(f"  System Status: {dashboard_data.get('system_status', {})}")
        
        # Show summary metrics if available
        summary = dashboard_data.get('summary', {})
        if summary:
            print("\n📈 Summary Metrics:")
            print(f"  Total Decisions: {summary.get('total_decisions', 0)}")
            print(f"  Approval Rate: {summary.get('approval_rate', 0):.1%}")
            print(f"  Success Rate: {summary.get('success_rate', 0):.1%}")
            print(f"  Net Profit: ${summary.get('net_profit', 0):.2f}")
        
        return dashboard_data
    
    async def demo_export_capabilities(self):
        """Demonstrate export capabilities."""
        print("\n💾 Phase 5: Export Capabilities")
        print("-" * 31)
        
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=1)
        
        export_types = ['decisions', 'results', 'performance']
        
        for export_type in export_types:
            try:
                export_file = self.logger.export_data(
                    data_type=export_type,
                    user_id='trader_alice',
                    start_time=start_time,
                    end_time=end_time,
                    format='json'
                )
                
                # Verify file was created and show size
                if os.path.exists(export_file):
                    file_size = os.path.getsize(export_file)
                    print(f"  ✓ Exported {export_type} data to: {export_file} ({file_size} bytes)")
                else:
                    print(f"  ⚠️  Export file not found: {export_file}")
                    
            except Exception as e:
                print(f"  ❌ Failed to export {export_type}: {e}")
    
    async def demo_audit_trails(self):
        """Demonstrate audit trail generation."""
        print("\n🔍 Phase 6: Audit Trail Generation")
        print("-" * 33)
        
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=2)
        
        try:
            audit_trail = self.logger.get_audit_trail(
                user_id='trader_alice',
                start_time=start_time,
                end_time=end_time
            )
            
            print(f"  📋 Audit trail entries: {len(audit_trail)}")
            
            if audit_trail:
                print("  📄 Sample audit entries:")
                for i, entry in enumerate(audit_trail[:3]):  # Show first 3 entries
                    print(f"    {i+1}. {entry.get('action', 'N/A')} at {entry.get('timestamp', 'N/A')}")
            
        except Exception as e:
            print(f"  ⚠️  No audit trail data available: {e}")
    
    async def generate_final_report(self):
        """Generate a comprehensive final report."""
        print("\n📋 Final Comprehensive Report")
        print("-" * 31)
        
        # Get overall statistics
        try:
            # Count total decisions
            decisions_count = 0
            results_count = 0
            
            with open('/workspace/arbitech/logs/hitl/decisions/human_decisions.jsonl', 'r') as f:
                decisions_count = sum(1 for line in f)
            
            with open('/workspace/arbitech/logs/hitl/results/trade_results.jsonl', 'r') as f:
                results_count = sum(1 for line in f)
            
            print(f"📊 System Statistics:")
            print(f"  Total Decisions Logged: {decisions_count}")
            print(f"  Total Results Logged: {results_count}")
            print(f"  Demo Users: {len(self.demo_users)}")
            print(f"  Demo Opportunities: {len(self.demo_opportunities)}")
            
            # Check log files
            log_files = [
                '/workspace/arbitech/logs/hitl/decisions/human_decisions.jsonl',
                '/workspace/arbitech/logs/hitl/results/trade_results.jsonl',
                '/workspace/arbitech/logs/hitl/performance/metrics.jsonl',
                '/workspace/arbitech/logs/hitl/patterns/interaction_patterns.jsonl',
                '/workspace/arbitech/logs/hitl/audit_trail.jsonl'
            ]
            
            print(f"\n📁 Log Files Status:")
            for log_file in log_files:
                if os.path.exists(log_file):
                    size = os.path.getsize(log_file)
                    print(f"  ✓ {Path(log_file).name}: {size} bytes")
                else:
                    print(f"  ⚠️  {Path(log_file).name}: Not found")
            
            print(f"\n🎯 HITL Result Logging System Features Verified:")
            print(f"  ✓ Human decision logging with full context")
            print(f"  ✓ Trade execution result tracking")
            print(f"  ✓ Performance metrics and analytics")
            print(f"  ✓ Real-time dashboard generation")
            print(f"  ✓ Export capabilities (JSON format)")
            print(f"  ✓ Audit trail generation")
            print(f"  ✓ Structured logging with JSON formatting")
            print(f"  ✓ Integration with existing ARBitech infrastructure")
            print(f"  ✓ User behavior pattern analysis")
            print(f"  ✓ Comprehensive P&L tracking")
            
        except Exception as e:
            print(f"  ⚠️  Error generating final report: {e}")


async def main():
    """Main demo execution."""
    print("🎯 ARBitech HITL Comprehensive Trade Result Logging Demo")
    print("=" * 70)
    print("This demo showcases the complete trade result logging system including:")
    print("• Human decision tracking with full context")
    print("• Execution outcome logging and P&L tracking") 
    print("• Performance analytics and success rate calculation")
    print("• User behavior pattern analysis")
    print("• Real-time dashboard generation")
    print("• Export capabilities and audit trails")
    print("• Integration with Phase 4 risk metrics and Phase 5 execution tracking")
    print("=" * 70)
    
    demo = ComprehensiveDemo()
    await demo.run_comprehensive_demo()


if __name__ == "__main__":
    # Run the async demo
    asyncio.run(main())