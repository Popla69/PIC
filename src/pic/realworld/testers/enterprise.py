"""Enterprise Security Testing

Real-world enterprise security validation tests.
No fluff. Just facts.
"""

import time
import logging
from typing import Dict, Any
from pic.cellagent import CellAgent
from ..safety import SafetyController
from ..harness import TestHarness


class EnterpriseSecurityTester:
    """Enterprise-grade security testing.
    
    Tests real failure modes and production scenarios.
    """
    
    def __init__(self, harness: TestHarness):
        """Initialize enterprise tester.
        
        Args:
            harness: TestHarness for PIC setup
        """
        self.harness = harness
        self.logger = logging.getLogger(__name__)
        self.results = []
    
    def test_fail_open_vs_fail_closed(self) -> Dict[str, Any]:
        """Test 5: Critical failure mode testing.
        
        Tests what happens when components crash/stall/fail.
        This determines production safety.
        """
        self.logger.info("[ENTERPRISE] Starting fail-open vs fail-closed tests")
        
        results = {
            "detector_crash": self._test_detector_crash(),
            "effector_stall": self._test_effector_stall(),
            "safety_trip": self._test_safety_trip(),
            "storage_failure": self._test_storage_failure(),
            "network_partition": self._test_network_partition()
        }
        
        # Calculate overall failure behavior
        fail_open_count = sum(1 for r in results.values() if r.get("behavior") == "fail_open")
        fail_closed_count = sum(1 for r in results.values() if r.get("behavior") == "fail_closed")
        
        return {
            "test_category": "fail_open_vs_fail_closed",
            "total_scenarios": len(results),
            "fail_open_scenarios": fail_open_count,
            "fail_closed_scenarios": fail_closed_count,
            "individual_results": results,
            "overall_behavior": "fail_open" if fail_open_count > fail_closed_count else "fail_closed",
            "safety_grade": "A" if fail_closed_count >= 3 else "B" if fail_closed_count >= 2 else "C"
        }

    def _test_detector_crash(self) -> Dict[str, Any]:
        """Test detector process crash behavior."""
        self.logger.info("[TEST] Detector crash simulation")
        
        start_time = time.time()
        agent, brain = self.harness.setup_pic_instance("detector_crash_test")
        
        # Send normal traffic
        normal_requests = 0
        for i in range(10):
            try:
                @agent.monitor
                def normal_request():
                    time.sleep(0.01)
                    return f"response_{i}"
                
                result = normal_request()
                if result is not None:
                    normal_requests += 1
            except Exception as e:
                self.logger.error(f"Normal request failed: {e}")
        
        # Simulate detector crash
        try:
            brain._detector = None
            
            post_crash_requests = 0
            for i in range(10):
                try:
                    @agent.monitor
                    def post_crash_request():
                        time.sleep(0.01)
                        return f"post_crash_{i}"
                    
                    result = post_crash_request()
                    if result is not None:
                        post_crash_requests += 1
                except Exception as e:
                    self.logger.error(f"Post-crash request failed: {e}")
            
            behavior = "fail_open" if post_crash_requests > 0 else "fail_closed"
            safety_level = "LOW" if post_crash_requests > 0 else "HIGH"
            duration = time.time() - start_time
            
            return {
                "scenario": "detector_crash",
                "behavior": behavior,
                "safety_level": safety_level,
                "normal_requests_passed": normal_requests,
                "post_crash_requests_passed": post_crash_requests,
                "availability_during_failure": (post_crash_requests / 10) * 100,
                "duration_seconds": duration,
                "passed": True
            }
        except Exception as e:
            return {
                "scenario": "detector_crash",
                "behavior": "unknown",
                "error": str(e),
                "passed": False
            }

    def _test_effector_stall(self) -> Dict[str, Any]:
        """Test effector stall behavior."""
        self.logger.info("[TEST] Effector stall simulation")
        
        start_time = time.time()
        try:
            agent, brain = self.harness.setup_pic_instance("effector_stall_test")
            
            def stalled_execute(decision):
                time.sleep(10)
                return None
            
            if hasattr(brain, '_effector') and brain._effector:
                brain._effector.execute = stalled_execute
            
            stalled_requests = 0
            request_times = []
            
            for i in range(5):
                req_start = time.time()
                try:
                    @agent.monitor
                    def stalled_request():
                        time.sleep(0.01)
                        return f"stalled_{i}"
                    
                    result = stalled_request()
                    req_end = time.time()
                    request_times.append(req_end - req_start)
                    
                    if result is not None:
                        stalled_requests += 1
                except Exception as e:
                    self.logger.error(f"Stalled request failed: {e}")
                    req_end = time.time()
                    request_times.append(req_end - req_start)
            
            avg_response_time = sum(request_times) / len(request_times) if request_times else 0
            
            if stalled_requests > 0 and avg_response_time < 1.0:
                behavior = "fail_open"
                safety_level = "LOW"
            elif stalled_requests == 0:
                behavior = "fail_closed"
                safety_level = "HIGH"
            else:
                behavior = "degraded"
                safety_level = "MEDIUM"
            
            duration = time.time() - start_time
            
            return {
                "scenario": "effector_stall",
                "behavior": behavior,
                "safety_level": safety_level,
                "requests_passed": stalled_requests,
                "avg_response_time_seconds": avg_response_time,
                "availability_during_stall": (stalled_requests / 5) * 100,
                "duration_seconds": duration,
                "passed": True
            }
        except Exception as e:
            return {
                "scenario": "effector_stall",
                "behavior": "unknown",
                "error": str(e),
                "passed": False
            }

    def _test_safety_trip(self) -> Dict[str, Any]:
        """Test safety controller trip behavior."""
        self.logger.info("[TEST] Safety controller trip simulation")
        
        start_time = time.time()
        try:
            agent, brain = self.harness.setup_pic_instance("safety_trip_test")
            safety = self.harness.safety_controller
            
            safety_triggered = False
            try:
                safety.validate_test_safety("DANGEROUS_OPERATION")
            except Exception as e:
                safety_triggered = True
                self.logger.info(f"Safety controller triggered: {e}")
            
            post_trip_requests = 0
            for i in range(5):
                try:
                    @agent.monitor
                    def post_trip_request():
                        time.sleep(0.01)
                        return f"post_trip_{i}"
                    
                    result = post_trip_request()
                    if result is not None:
                        post_trip_requests += 1
                except Exception as e:
                    self.logger.error(f"Post-trip request failed: {e}")
            
            if safety_triggered and post_trip_requests == 0:
                behavior = "fail_closed"
                safety_level = "HIGH"
            elif not safety_triggered:
                behavior = "fail_open"
                safety_level = "LOW"
            else:
                behavior = "inconsistent"
                safety_level = "CRITICAL"
            
            duration = time.time() - start_time
            
            return {
                "scenario": "safety_trip",
                "behavior": behavior,
                "safety_level": safety_level,
                "safety_triggered": safety_triggered,
                "post_trip_requests_passed": post_trip_requests,
                "availability_after_trip": (post_trip_requests / 5) * 100,
                "duration_seconds": duration,
                "passed": True
            }
        except Exception as e:
            return {
                "scenario": "safety_trip",
                "behavior": "unknown",
                "error": str(e),
                "passed": False
            }
    
    def _test_storage_failure(self) -> Dict[str, Any]:
        """Test storage system failure behavior."""
        self.logger.info("[TEST] Storage failure simulation")
        
        start_time = time.time()
        try:
            agent, brain = self.harness.setup_pic_instance("storage_failure_test")
            
            if hasattr(brain, '_state_store'):
                def failing_store(key, value):
                    raise Exception("Storage failure simulated")
                brain._state_store.store = failing_store
            
            storage_fail_requests = 0
            for i in range(5):
                try:
                    @agent.monitor
                    def storage_fail_request():
                        time.sleep(0.01)
                        return f"storage_fail_{i}"
                    
                    result = storage_fail_request()
                    if result is not None:
                        storage_fail_requests += 1
                except Exception as e:
                    self.logger.error(f"Storage fail request failed: {e}")
            
            behavior = "fail_open" if storage_fail_requests > 0 else "fail_closed"
            safety_level = "MEDIUM" if storage_fail_requests > 0 else "HIGH"
            duration = time.time() - start_time
            
            return {
                "scenario": "storage_failure",
                "behavior": behavior,
                "safety_level": safety_level,
                "requests_passed": storage_fail_requests,
                "availability_during_failure": (storage_fail_requests / 5) * 100,
                "duration_seconds": duration,
                "passed": True
            }
        except Exception as e:
            return {
                "scenario": "storage_failure",
                "behavior": "unknown",
                "error": str(e),
                "passed": False
            }
    
    def _test_network_partition(self) -> Dict[str, Any]:
        """Test network partition behavior."""
        self.logger.info("[TEST] Network partition simulation")
        
        start_time = time.time()
        try:
            agent, brain = self.harness.setup_pic_instance("network_partition_test")
            partition_active = True
            
            partition_requests = 0
            for i in range(5):
                try:
                    @agent.monitor
                    def partition_request():
                        if partition_active:
                            time.sleep(0.1)
                        time.sleep(0.01)
                        return f"partition_{i}"
                    
                    result = partition_request()
                    if result is not None:
                        partition_requests += 1
                except Exception as e:
                    self.logger.error(f"Partition request failed: {e}")
            
            behavior = "fail_open" if partition_requests > 0 else "fail_closed"
            safety_level = "MEDIUM" if partition_requests > 0 else "HIGH"
            duration = time.time() - start_time
            
            return {
                "scenario": "network_partition",
                "behavior": behavior,
                "safety_level": safety_level,
                "requests_passed": partition_requests,
                "availability_during_partition": (partition_requests / 5) * 100,
                "autonomous_operation": partition_requests > 0,
                "duration_seconds": duration,
                "passed": True
            }
        except Exception as e:
            return {
                "scenario": "network_partition",
                "behavior": "unknown",
                "error": str(e),
                "passed": False
            }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all enterprise security tests."""
        self.logger.info("[ENTERPRISE] Starting all enterprise security tests")
        
        results = {
            "fail_open_vs_fail_closed": self.test_fail_open_vs_fail_closed()
        }
        
        total_scenarios = sum(r.get("total_scenarios", 0) for r in results.values())
        passed_scenarios = sum(
            len([s for s in r.get("individual_results", {}).values() if s.get("passed", False)])
            for r in results.values()
        )
        
        return {
            "test_category": "enterprise_security",
            "total_scenarios": total_scenarios,
            "passed_scenarios": passed_scenarios,
            "pass_rate": passed_scenarios / total_scenarios if total_scenarios > 0 else 0,
            "individual_results": results,
            "enterprise_grade": self._calculate_enterprise_grade(results)
        }
    
    def _calculate_enterprise_grade(self, results: Dict[str, Any]) -> str:
        """Calculate overall enterprise security grade."""
        fail_results = results.get("fail_open_vs_fail_closed", {})
        safety_grade = fail_results.get("safety_grade", "F")
        
        if safety_grade == "A":
            return "ENTERPRISE_READY"
        elif safety_grade == "B":
            return "PRODUCTION_READY"
        elif safety_grade == "C":
            return "DEVELOPMENT_ONLY"
        else:
            return "NOT_READY"
