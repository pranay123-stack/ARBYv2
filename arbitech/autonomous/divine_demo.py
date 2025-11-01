#!/usr/bin/env python3
"""
Heavenly Circuit Breakers - Comprehensive Demo
=============================================

This demo showcases the complete heavenly circuit breaker system with:
- Multi-layered protection
- Guardian angel monitoring
- Predictive failure detection
- Phoenix-like recovery
- Divine intervention protocols

Usage:
    python divine_demo.py
"""

import asyncio
import logging
import random
import sys
import os
from datetime import datetime

# Add the parent directory to the path to import the module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from autonomous.circuit_breakers import (
    CelestialProtectionSystem,
    GuardianAngel,
    SacredThreshold,
    DivineTestSuite,
    CelestialEvent,
    DivineState
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'divine_demo_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)

logger = logging.getLogger(__name__)


class DivineDemoScenario:
    """Divine demonstration scenarios"""
    
    def __init__(self, system: CelestialProtectionSystem):
        self.system = system
        self.scenario_results = []
    
    async def run_all_scenarios(self):
        """Run all demonstration scenarios"""
        print("🌟 Starting Comprehensive Divine Circuit Breaker Demonstration")
        print("=" * 70)
        
        scenarios = [
            ("Basic Protection", self.basic_protection_scenario),
            ("Guardian Angel Monitoring", self.guardian_angel_scenario),
            ("Failure Cascade Protection", self.failure_cascade_scenario),
            ("Phoenix Recovery", self.phoenix_recovery_scenario),
            ("Divine Intervention", self.divine_intervention_scenario),
            ("Anomaly Detection", self.anomaly_detection_scenario),
            ("Emergency Protocols", self.emergency_protocols_scenario),
            ("System Integration", self.system_integration_scenario)
        ]
        
        for scenario_name, scenario_func in scenarios:
            print(f"\n🎭 {scenario_name} Scenario")
            print("-" * 50)
            
            try:
                result = await scenario_func()
                self.scenario_results.append({
                    "scenario": scenario_name,
                    "status": "SUCCESS",
                    "result": result
                })
                print(f"✅ {scenario_name}: SUCCESS")
            except Exception as e:
                logger.error(f"Scenario {scenario_name} failed: {e}")
                self.scenario_results.append({
                    "scenario": scenario_name,
                    "status": "FAILED",
                    "error": str(e)
                })
                print(f"❌ {scenario_name}: FAILED - {e}")
        
        return self.generate_summary_report()
    
    async def basic_protection_scenario(self) -> dict:
        """Basic circuit breaker protection scenario"""
        # Register a service
        service = self.system.register_service("basic_service")
        
        # Test function that might fail
        async def potentially_failing_function():
            if random.random() < 0.3:  # 30% failure rate
                raise Exception("Simulated failure")
            return "Success"
        
        # Make protected calls
        results = []
        for i in range(10):
            try:
                result = await service.call(potentially_failing_function)
                results.append(("SUCCESS", result))
            except Exception as e:
                results.append(("FAILURE", str(e)))
        
        # Check circuit breaker state
        status = await service.get_divine_status()
        
        return {
            "calls_made": len(results),
            "successes": sum(1 for r in results if r[0] == "SUCCESS"),
            "failures": sum(1 for r in results if r[0] == "FAILURE"),
            "circuit_state": status["divine_state"]
        }
    
    async def guardian_angel_scenario(self) -> dict:
        """Guardian angel monitoring scenario"""
        service = self.system.register_service("guarded_service")
        
        # Add multiple guardian angels
        angels = [
            GuardianAngel("Archangel Michael", SacredThreshold.ARCHANGEL),
            GuardianAngel("Guardian Angel Gabriel", SacredThreshold.GUARDIAN),
            GuardianAngel("Seraph Raphael", SacredThreshold.SERAPHIC)
        ]
        
        for angel in angels:
            service.add_guardian_angel(angel)
        
        status = await service.get_divine_status()
        guardian_count = len(service.guardian_angels)
        
        # Simulate some service activity
        async def service_function():
            await asyncio.sleep(0.01)
            return "Guarded service response"
        
        try:
            result = await service.call(service_function)
            return {
                "guardian_angels_assigned": guardian_count,
                "test_call_successful": True,
                "service_response": result
            }
        except Exception as e:
            return {
                "guardian_angels_assigned": guardian_count,
                "test_call_successful": False,
                "error": str(e)
            }
    
    async def failure_cascade_scenario(self) -> dict:
        """Failure cascade protection scenario"""
        service = self.system.register_service("cascade_service", failure_threshold=0.2)
        
        # Service function that fails frequently
        async def failing_function():
            if random.random() < 0.7:  # 70% failure rate
                raise Exception("Frequent failure")
            return "Occasional success"
        
        # Make many calls to trigger circuit breaker
        results = []
        for i in range(20):
            try:
                result = await service.call(failing_function)
                results.append(result)
            except Exception as e:
                results.append(f"Failed: {str(e)[:30]}")
        
        # Check final state
        final_status = await service.get_divine_status()
        
        return {
            "total_calls": len(results),
            "successes": sum(1 for r in results if not str(r).startswith("Failed")),
            "final_circuit_state": final_status["divine_state"],
            "failure_count": final_status["circuit_breaker_status"]["failure_count"]
        }
    
    async def phoenix_recovery_scenario(self) -> dict:
        """Phoenix-like recovery scenario"""
        service = self.system.register_service("recovery_service")
        
        # Force the service into standby state
        async def consistently_failing_function():
            raise Exception("Consistent failure")
        
        # Make many calls to force circuit opening
        for i in range(30):
            try:
                await service.call(consistently_failing_function)
            except:
                pass  # Expected failures
        
        # Check if circuit opened
        status_before = await service.get_divine_status()
        initial_state = status_before["divine_state"]
        
        # Wait for recovery timeout (simulated)
        if initial_state == "STANDBY":
            # Trigger phoenix recovery manually
            failure_context = {
                "error_rate": 0.9,
                "response_time": 5.0,
                "resource_usage": 0.95
            }
            recovery_success = await service.phoenix_recovery.phoenix_resurrection(
                "recovery_service", failure_context
            )
            
            # Check recovery result
            status_after = await service.get_divine_status()
            
            return {
                "initial_state": initial_state,
                "recovery_attempted": True,
                "recovery_successful": recovery_success,
                "final_state": status_after["divine_state"]
            }
        
        return {
            "initial_state": initial_state,
            "recovery_attempted": False,
            "reason": "Circuit did not open"
        }
    
    async def divine_intervention_scenario(self) -> dict:
        """Divine intervention protocol scenario"""
        service = self.system.register_service("intervention_service")
        
        # Trigger a divine intervention event
        trigger_event = CelestialEvent(
            timestamp=datetime.now(),
            event_type="CRITICAL_FAILURE",
            severity=0.9,
            source="intervention_service",
            data={"failure_count": 25, "error_rate": 0.95}
        )
        
        # Invoke divine intervention
        success = await service.divine_intervention.invoke_divine_intervention(
            trigger_event, "EMERGENCY_SHUTDOWN"
        )
        
        # Check intervention history
        intervention_count = len(service.divine_intervention.intervention_history)
        
        return {
            "intervention_invoked": True,
            "intervention_successful": success,
            "total_interventions": intervention_count,
            "intervention_type": "EMERGENCY_SHUTDOWN"
        }
    
    async def anomaly_detection_scenario(self) -> dict:
        """Anomaly detection scenario"""
        service = self.system.register_service("anomaly_service")
        
        # Feed normal data first
        for i in range(15):
            is_anomaly, anomaly_type = service.anomaly_detector.divine_perception(
                f"{service.service_name}_metric", 1.0 + random.uniform(-0.1, 0.1)
            )
        
        # Now feed anomalous data
        anomaly_detected = False
        for i in range(10):
            is_anomaly, anomaly_type = service.anomaly_detector.divine_perception(
                f"{service.service_name}_metric", 5.0 + random.uniform(-1.0, 1.0)
            )
            if is_anomaly:
                anomaly_detected = True
                break
        
        return {
            "baseline_established": service.anomaly_detector.baseline_established,
            "anomaly_detected": anomaly_detected,
            "sensitivity": service.anomaly_detector.divine_sensitivity
        }
    
    async def emergency_protocols_scenario(self) -> dict:
        """Emergency protocol scenario"""
        service = self.system.register_service("emergency_service")
        
        # Simulate multiple types of emergencies
        emergency_types = ["EMERGENCY_SHUTDOWN", "DIVINE_ISOLATION", "GUARDIAN_REINFORCEMENT"]
        results = []
        
        for emergency_type in emergency_types:
            trigger_event = CelestialEvent(
                timestamp=datetime.now(),
                event_type=emergency_type,
                severity=0.8,
                source="emergency_service"
            )
            
            success = await service.divine_intervention.invoke_divine_intervention(
                trigger_event, emergency_type
            )
            results.append({
                "type": emergency_type,
                "successful": success
            })
        
        return {
            "emergency_protocols_tested": len(emergency_types),
            "successful_interventions": sum(1 for r in results if r["successful"]),
            "results": results
        }
    
    async def system_integration_scenario(self) -> dict:
        """Full system integration scenario"""
        # Start system monitoring
        await self.system.start_monitoring()
        
        # Register multiple services
        services = [
            ("integration_service_1", 0.3),
            ("integration_service_2", 0.2),
            ("integration_service_3", 0.4)
        ]
        
        registered_services = []
        for service_name, threshold in services:
            service = self.system.register_service(service_name, threshold)
            registered_services.append(service)
            
            # Add random guardian angels
            if random.random() > 0.5:
                angel = GuardianAngel(f"Guardian of {service_name}", SacredThreshold.GUARDIAN)
                service.add_guardian_angel(angel)
        
        # Let monitoring run for a bit
        await asyncio.sleep(2)
        
        # Get comprehensive system status
        system_status = await self.system.get_system_divine_status()
        
        await self.system.stop_monitoring()
        
        return {
            "services_registered": len(registered_services),
            "monitoring_active": self.system._monitoring_task is not None,
            "system_status": system_status["system_status"],
            "total_guardian_angels": system_status["guardian_angels"]
        }
    
    def generate_summary_report(self) -> dict:
        """Generate comprehensive demo summary"""
        successful_scenarios = sum(1 for r in self.scenario_results if r["status"] == "SUCCESS")
        total_scenarios = len(self.scenario_results)
        
        return {
            "demo_summary": {
                "total_scenarios": total_scenarios,
                "successful_scenarios": successful_scenarios,
                "success_rate": successful_scenarios / total_scenarios if total_scenarios > 0 else 0.0
            },
            "scenario_results": self.scenario_results,
            "timestamp": datetime.now().isoformat()
        }


async def main():
    """Main demonstration function"""
    print("🌟 Heavenly Circuit Breakers and Divine Failsafes Demo")
    print("✨ Demonstrating Multi-Layered Celestial Protection")
    print("=" * 70)
    
    # Create the celestial protection system
    system = CelestialProtectionSystem()
    
    # Create demo scenarios
    demo = DivineDemoScenario(system)
    
    # Run comprehensive tests first
    print("\n🧪 Running Divine Test Suite")
    print("-" * 40)
    test_suite = DivineTestSuite()
    test_report = await test_suite.run_comprehensive_tests()
    
    print(f"Test Results: {test_report['test_summary']['passed']}/{test_report['test_summary']['total_tests']} passed")
    print(f"Divine Precision: {test_report['divine_metrics']['divine_precision']:.2%}")
    
    # Run demonstration scenarios
    summary = await demo.run_all_scenarios()
    
    # Print final summary
    print("\n" + "=" * 70)
    print("🎭 DIVINE DEMONSTRATION SUMMARY")
    print("=" * 70)
    print(f"Total Scenarios: {summary['demo_summary']['total_scenarios']}")
    print(f"Successful Scenarios: {summary['demo_summary']['successful_scenarios']}")
    print(f"Success Rate: {summary['demo_summary']['success_rate']:.2%}")
    
    print("\n🌟 Scenario Results:")
    for result in summary['scenario_results']:
        status_icon = "✅" if result['status'] == "SUCCESS" else "❌"
        print(f"  {status_icon} {result['scenario']}: {result['status']}")
    
    print("\n🙏 Divine demonstration complete!")
    print("🛡️ Your systems are now protected by celestial circuit breakers!")
    
    return summary


if __name__ == "__main__":
    # Run the comprehensive demo
    try:
        result = asyncio.run(main())
        sys.exit(0 if result['demo_summary']['success_rate'] > 0.8 else 1)
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Demo failed with error: {e}")
        logger.exception("Demo execution failed")
        sys.exit(1)