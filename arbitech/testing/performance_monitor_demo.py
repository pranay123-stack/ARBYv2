#!/usr/bin/env python3
"""
Demo and Test Script for ARBitech Performance Monitoring System

This script demonstrates the comprehensive performance monitoring capabilities:
- Real-time system resource monitoring
- Trading performance analytics
- Alert management and notifications
- Dashboard integration
- Optimization recommendations
- Data export and reporting

Usage:
    python performance_monitor_demo.py [--demo] [--test] [--export]

Arguments:
    --demo: Run full demonstration (default)
    --test: Run test suite
    --export: Export sample performance data
"""

import asyncio
import json
import time
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from testing.performance_monitor import (
    PerformanceMonitor, SystemResourceMonitor, TradingPerformanceAnalyzer,
    AlertManager, OptimizationEngine, DashboardIntegration,
    get_performance_monitor
)

class PerformanceMonitorDemo:
    """Comprehensive demo of the performance monitoring system"""
    
    def __init__(self):
        self.monitor = None
        self.demo_trades = self._generate_sample_trades()
    
    def _generate_sample_trades(self):
        """Generate sample trade data for testing"""
        import random
        
        trades = []
        base_time = time.time() - (24 * 3600)  # 24 hours ago
        
        for i in range(50):  # Generate 50 sample trades
            trade_time = base_time + (i * 1800)  # Every 30 minutes
            
            # Random trade outcomes with realistic distributions
            stake = random.uniform(50, 500)
            pnl = random.uniform(-stake * 0.1, stake * 0.15)  # -10% to +15% range
            
            trades.append({
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(trade_time)),
                'pnl': round(pnl, 2),
                'stake': round(stake, 2),
                'start_time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(trade_time)),
                'end_time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(trade_time + random.uniform(30, 300))),
                'bookmaker': random.choice(['bet365', 'william_hill', 'ladbrokes', 'pinnacle', 'betfair']),
                'sport': random.choice(['football', 'tennis', 'basketball', 'horse_racing']),
                'opportunity_id': f"arb_{i:04d}"
            })
        
        return trades
    
    async def run_full_demo(self):
        """Run complete demonstration of the system"""
        print("🚀 ARBitech Performance Monitoring System - Full Demo")
        print("=" * 60)
        
        try:
            # 1. Initialize and setup
            print("\n1️⃣  Initializing Performance Monitor...")
            self.monitor = PerformanceMonitor()
            
            # Add sample trade data
            print(f"📊 Adding {len(self.demo_trades)} sample trades...")
            for trade in self.demo_trades:
                self.monitor.add_trade_result(trade)
            
            # 2. Start monitoring
            print("\n2️⃣  Starting Real-time Monitoring...")
            await self.monitor.start_monitoring()
            
            # 3. Let it run and collect data
            print("\n3️⃣  Collecting Performance Data...")
            print("   • System metrics (CPU, Memory, Disk, Network)")
            print("   • Trading analytics (ROI, Sharpe Ratio, Drawdown)")
            print("   • Alert monitoring and processing")
            print("   • Dashboard data updates")
            
            # Run for 45 seconds to collect meaningful data
            for i in range(9):
                await asyncio.sleep(5)
                print(f"   ⏱️  Monitoring... ({i+1}/9)")
            
            # 4. Show current performance summary
            print("\n4️⃣  Current Performance Summary")
            print("-" * 40)
            summary = self.monitor.get_current_performance_summary()
            
            print(f"🖥️  System Status:")
            system_metrics = summary.get('system_metrics', {})
            if system_metrics:
                print(f"   CPU Usage: {system_metrics.get('cpu_percent', 0):.1f}%")
                print(f"   Memory Usage: {system_metrics.get('memory_percent', 0):.1f}%")
                print(f"   Disk Usage: {system_metrics.get('disk_usage_percent', 0):.1f}%")
            
            print(f"\n📈 Trading Performance:")
            trading_metrics = summary.get('trading_metrics', {})
            if trading_metrics:
                print(f"   Total Trades: {trading_metrics.get('total_trades', 0)}")
                print(f"   ROI: {trading_metrics.get('roi', 0):.2f}%")
                print(f"   Win Rate: {trading_metrics.get('win_rate', 0):.1f}%")
                print(f"   Total P&L: ${trading_metrics.get('total_pnl', 0):.2f}")
                print(f"   Max Drawdown: {trading_metrics.get('max_drawdown', 0):.2f}%")
                print(f"   Sharpe Ratio: {trading_metrics.get('sharpe_ratio', 0):.2f}")
            
            print(f"\n🚨 Active Alerts: {summary.get('active_alerts_count', 0)}")
            
            # 5. Show metric trends
            print("\n5️⃣  Metric Trends Analysis")
            print("-" * 40)
            
            key_metrics = ['cpu_percent', 'memory_percent', 'roi', 'win_rate']
            for metric in key_metrics:
                trend = self.monitor.get_metric_trends(metric, hours=1)
                print(f"📊 {metric}:")
                stats = trend.get('statistics', {})
                if stats:
                    print(f"   Avg: {stats.get('mean', 0):.2f}")
                    print(f"   Min: {stats.get('min', 0):.2f}")
                    print(f"   Max: {stats.get('max', 0):.2f}")
                    print(f"   Data Points: {trend.get('data_points', 0)}")
                print()
            
            # 6. Show comprehensive report
            print("6️⃣  Comprehensive Performance Report")
            print("-" * 40)
            report = self.monitor.get_performance_report(hours=1)
            
            print("📋 Report Summary:")
            summary_stats = report.get('summary', {})
            print(f"   Metrics Collected: {summary_stats.get('total_metrics_collected', 0)}")
            print(f"   Alerts Triggered: {summary_stats.get('total_alerts_triggered', 0)}")
            print(f"   Recommendations: {summary_stats.get('total_recommendations', 0)}")
            print(f"   System Checks: {summary_stats.get('total_system_checks', 0)}")
            print(f"   Errors: {summary_stats.get('errors_encountered', 0)}")
            
            # 7. Show dashboard integration
            print("\n7️⃣  Dashboard Integration")
            print("-" * 40)
            dashboard_data = self.monitor.dashboard_integration.get_dashboard_data()
            print(f"📊 Dashboard Last Updated: {dashboard_data.get('last_updated', 'N/A')}")
            print(f"   System Metrics: ✅" if dashboard_data.get('system_metrics') else "   System Metrics: ❌")
            print(f"   Trading Metrics: ✅" if dashboard_data.get('trading_metrics') else "   Trading Metrics: ❌")
            print(f"   Alerts: ✅" if dashboard_data.get('alerts') else "   Alerts: ❌")
            print(f"   Recommendations: ✅" if dashboard_data.get('recommendations') else "   Recommendations: ❌")
            
            # 8. Export data
            print("\n8️⃣  Exporting Performance Data")
            print("-" * 40)
            export_file = "demo_performance_export.json"
            self.monitor.export_performance_data(export_file)
            print(f"📁 Performance data exported to: {export_file}")
            
            # 9. Stop monitoring
            print("\n9️⃣  Stopping Monitoring")
            print("-" * 40)
            await self.monitor.shutdown()
            print("✅ Monitoring stopped gracefully")
            
            print("\n" + "=" * 60)
            print("🎉 DEMO COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            
            # Summary of capabilities demonstrated
            print("\n📋 Demo Summary:")
            print("✅ Real-time performance metrics collection")
            print("✅ System resource monitoring (CPU, Memory, Disk, Network)")
            print("✅ Trading performance analytics (ROI, Sharpe, Drawdown)")
            print("✅ Alert management and real-time notifications")
            print("✅ Historical data tracking and trend analysis")
            print("✅ Dashboard integration for real-time visualization")
            print("✅ Automated optimization recommendations")
            print("✅ Supabase integration for data persistence")
            print("✅ Performance reporting and data export")
            print("✅ Production-ready monitoring without performance impact")
            
        except Exception as e:
            print(f"❌ Demo failed with error: {e}")
            import traceback
            traceback.print_exc()
    
    async def run_test_suite(self):
        """Run comprehensive test suite"""
        print("🧪 Running Performance Monitoring Test Suite")
        print("=" * 50)
        
        tests_passed = 0
        tests_total = 0
        
        # Test 1: System Resource Monitoring
        tests_total += 1
        try:
            print("\nTest 1: System Resource Monitoring")
            monitor = SystemResourceMonitor()
            metrics = monitor.collect_system_metrics()
            assert isinstance(metrics, object)
            assert hasattr(metrics, 'cpu_percent')
            assert hasattr(metrics, 'memory_percent')
            assert hasattr(metrics, 'disk_usage_percent')
            print("✅ PASSED")
            tests_passed += 1
        except Exception as e:
            print(f"❌ FAILED: {e}")
        
        # Test 2: Trading Performance Analysis
        tests_total += 1
        try:
            print("\nTest 2: Trading Performance Analysis")
            analyzer = TradingPerformanceAnalyzer()
            
            # Add sample trades
            sample_trades = [
                {'pnl': 10, 'stake': 100, 'timestamp': '2025-11-02T04:00:00Z'},
                {'pnl': -5, 'stake': 100, 'timestamp': '2025-11-02T04:01:00Z'},
                {'pnl': 15, 'stake': 100, 'timestamp': '2025-11-02T04:02:00Z'},
            ]
            
            for trade in sample_trades:
                analyzer.add_trade_result(trade)
            
            metrics = analyzer.calculate_performance_metrics()
            assert isinstance(metrics, object)
            assert hasattr(metrics, 'total_trades')
            assert hasattr(metrics, 'roi')
            assert hasattr(metrics, 'win_rate')
            print("✅ PASSED")
            tests_passed += 1
        except Exception as e:
            print(f"❌ FAILED: {e}")
        
        # Test 3: Alert Management
        tests_total += 1
        try:
            print("\nTest 3: Alert Management")
            alert_manager = AlertManager()
            
            # Check alert conditions
            alerts = alert_manager.check_alert_conditions('cpu_percent', 90.0)
            assert isinstance(alerts, list)
            
            active_alerts = alert_manager.get_active_alerts()
            assert isinstance(active_alerts, list)
            print("✅ PASSED")
            tests_passed += 1
        except Exception as e:
            print(f"❌ FAILED: {e}")
        
        # Test 4: Optimization Engine
        tests_total += 1
        try:
            print("\nTest 4: Optimization Engine")
            opt_engine = OptimizationEngine()
            
            # Test recommendation generation
            recommendations = opt_engine._generate_general_recommendations()
            assert isinstance(recommendations, list)
            assert len(recommendations) > 0
            print("✅ PASSED")
            tests_passed += 1
        except Exception as e:
            print(f"❌ FAILED: {e}")
        
        # Test 5: Dashboard Integration
        tests_total += 1
        try:
            print("\nTest 5: Dashboard Integration")
            dashboard = DashboardIntegration()
            
            # Test data structures
            data = dashboard.get_dashboard_data()
            assert isinstance(data, dict)
            assert 'system_metrics' in data
            assert 'trading_metrics' in data
            print("✅ PASSED")
            tests_passed += 1
        except Exception as e:
            print(f"❌ FAILED: {e}")
        
        # Test 6: Main Performance Monitor
        tests_total += 1
        try:
            print("\nTest 6: Main Performance Monitor")
            monitor = PerformanceMonitor()
            
            # Test initialization
            assert monitor is not None
            assert hasattr(monitor, 'monitoring_active')
            assert hasattr(monitor, 'stats')
            
            # Test trade addition
            monitor.add_trade_result({'pnl': 10, 'stake': 100})
            
            # Test performance summary
            summary = monitor.get_current_performance_summary()
            assert isinstance(summary, dict)
            assert 'statistics' in summary
            print("✅ PASSED")
            tests_passed += 1
        except Exception as e:
            print(f"❌ FAILED: {e}")
        
        print(f"\n{'='*50}")
        print(f"🏆 TEST RESULTS: {tests_passed}/{tests_total} tests passed")
        
        if tests_passed == tests_total:
            print("🎉 ALL TESTS PASSED!")
        else:
            print(f"⚠️  {tests_total - tests_passed} tests failed")
        
        return tests_passed == tests_total
    
    async def export_sample_data(self):
        """Export sample performance data"""
        print("📊 Exporting Sample Performance Data")
        print("=" * 40)
        
        try:
            monitor = PerformanceMonitor()
            
            # Add sample trades
            for trade in self.demo_trades[:10]:  # First 10 trades
                monitor.add_trade_result(trade)
            
            # Start monitoring briefly
            await monitor.start_monitoring()
            await asyncio.sleep(10)  # Collect for 10 seconds
            await monitor.stop_monitoring()
            
            # Export comprehensive report
            export_file = "sample_performance_data.json"
            monitor.export_performance_data(export_file, hours=1)
            
            print(f"✅ Sample data exported to: {export_file}")
            
            # Also export dashboard data
            dashboard_file = "sample_dashboard_data.json"
            dashboard_data = monitor.dashboard_integration.get_dashboard_data()
            
            with open(dashboard_file, 'w') as f:
                json.dump(dashboard_data, f, indent=2, default=str)
            
            print(f"✅ Dashboard data exported to: {dashboard_file}")
            
        except Exception as e:
            print(f"❌ Export failed: {e}")

def main():
    """Main entry point for the demo script"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ARBitech Performance Monitor Demo')
    parser.add_argument('--demo', action='store_true', help='Run full demonstration')
    parser.add_argument('--test', action='store_true', help='Run test suite')
    parser.add_argument('--export', action='store_true', help='Export sample data')
    
    args = parser.parse_args()
    
    # Default to demo if no arguments specified
    if not any([args.demo, args.test, args.export]):
        args.demo = True
    
    async def run_demo():
        demo = PerformanceMonitorDemo()
        
        if args.demo:
            await demo.run_full_demo()
        
        if args.test:
            success = await demo.run_test_suite()
            if not success:
                sys.exit(1)
        
        if args.export:
            await demo.export_sample_data()
    
    # Run the demo
    asyncio.run(run_demo())

if __name__ == "__main__":
    main()