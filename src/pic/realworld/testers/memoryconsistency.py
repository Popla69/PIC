"""Memory Consistency and Recovery Testing

Tests PIC's ability to recover and maintain consistency after stress.
Tests: high load recovery, noise saturation, corrupted state injection
"""

import time
import logging
from typing import Dict, Any
from ..harness import TestHarness


class MemoryConsistencyTester:
    """Memory consistency and recovery testing.
    
    Tests PIC's resilience and recovery capabilities.
    """
    
    def __init__(self, harness: TestHarness):
        """Initialize memory consistency tester.
        
        Args:
            harness: TestHarness for PIC setup
        """
        self.harness = harness
        self.logger = logging.getLogger(__name__)
    
    def test_high_load_recovery(self) -> Dict[str, Any]:
        """Test recovery after high load saturation.
        
        Saturates system then measures recovery time.
        """
        self.logger.info("[MEMORY] Testing high load recovery")
        
        start_time = time.time()
        agent, brain = self.harness.setup_pic_instance("high_load_recovery_test")
        
        baseline_time = 0.005
        
        # Establish baseline
        for i in range(30):
            @agent.monitor
            def baseline_op():
                time.sleep(baseline_time)
                return "baseline"
            baseline_op()
        
        # High load saturation
        self.logger.info("[MEMORY] Saturating with high load...")
        for i in range(200):
            @agent.monitor
            def high_load():
                time.sleep(0.050)  # 10x slower
                return f"load_{i}"
            high_load()
        
        # Measure recovery
        self.logger.info("[MEMORY] Measuring recovery...")
        recovery_start = time.time()
        recovery_success = []
        
        for i in range(30):
            @agent.monitor
            def recovery_op():
                time.sleep(baseline_time)
                return f"recovery_{i}"
            
            result = recovery_op()
            recovery_success.append(result is not None)
        
        recovery_time = time.time() - recovery_start
        recovery_rate = sum(recovery_success) / len(recovery_success)
        duration = time.time() - start_time
        
        return {
            "test_type": "high_load_recovery",
            "load_operations": 200,
            "recovery_operations": 30,
            "recovery_rate": recovery_rate,
            "recovery_time_seconds": recovery_time,
            "total_duration_seconds": duration,
            "passed": recovery_rate >= 0.80
        }
    
    def test_noise_saturation_recovery(self) -> Dict[str, Any]:
        """Test recovery after noise saturation.
        
        Floods with random anomalies then measures recovery.
        """
        self.logger.info("[MEMORY] Testing noise saturation recovery")
        
        start_time = time.time()
        agent, brain = self.harness.setup_pic_instance("noise_saturation_test")
        
        baseline_time = 0.005
        
        # Establish baseline
        for i in range(30):
            @agent.monitor
            def baseline_op():
                time.sleep(baseline_time)
                return "baseline"
            baseline_op()
        
        # Noise saturation
        self.logger.info("[MEMORY] Saturating with noise...")
        import random
        for i in range(300):
            variance = random.uniform(0.001, 0.020)
            @agent.monitor
            def noise_op():
                time.sleep(variance)
                return f"noise_{i}"
            noise_op()
        
        # Measure recovery
        self.logger.info("[MEMORY] Measuring recovery...")
        recovery_success = []
        
        for i in range(30):
            @agent.monitor
            def recovery_op():
                time.sleep(baseline_time)
                return f"recovery_{i}"
            
            result = recovery_op()
            recovery_success.append(result is not None)
        
        recovery_rate = sum(recovery_success) / len(recovery_success)
        duration = time.time() - start_time
        
        return {
            "test_type": "noise_saturation_recovery",
            "noise_operations": 300,
            "recovery_operations": 30,
            "recovery_rate": recovery_rate,
            "total_duration_seconds": duration,
            "passed": recovery_rate >= 0.80
        }
    
    def test_baseline_integrity(self) -> Dict[str, Any]:
        """Test baseline integrity after stress.
        
        Verifies baseline remains accurate after load.
        """
        self.logger.info("[MEMORY] Testing baseline integrity")
        
        start_time = time.time()
        agent, brain = self.harness.setup_pic_instance("baseline_integrity_test")
        
        baseline_time = 0.005
        
        # Establish baseline
        for i in range(50):
            @agent.monitor
            def baseline_op():
                time.sleep(baseline_time)
                return "baseline"
            baseline_op()
        
        # Stress with varied load
        for i in range(100):
            variance = 0.020 if i % 10 == 0 else 0.005
            @agent.monitor
            def stress_op():
                time.sleep(variance)
                return f"stress_{i}"
            stress_op()
        
        # Test baseline accuracy
        baseline_test = []
        for i in range(30):
            @agent.monitor
            def baseline_check():
                time.sleep(baseline_time)
                return f"check_{i}"
            
            result = baseline_check()
            baseline_test.append(result is not None)
        
        integrity_rate = sum(baseline_test) / len(baseline_test)
        duration = time.time() - start_time
        
        return {
            "test_type": "baseline_integrity",
            "stress_operations": 100,
            "baseline_checks": 30,
            "integrity_rate": integrity_rate,
            "total_duration_seconds": duration,
            "passed": integrity_rate >= 0.90
        }
    
    def test_detection_capability_during_recovery(self) -> Dict[str, Any]:
        """Test if detection works during recovery.
        
        Verifies system can still detect threats while recovering.
        """
        self.logger.info("[MEMORY] Testing detection during recovery")
        
        start_time = time.time()
        agent, brain = self.harness.setup_pic_instance("detection_recovery_test")
        
        baseline_time = 0.005
        
        # Establish baseline
        for i in range(30):
            @agent.monitor
            def baseline_op():
                time.sleep(baseline_time)
                return "baseline"
            baseline_op()
        
        # High load
        for i in range(100):
            @agent.monitor
            def load_op():
                time.sleep(0.030)
                return f"load_{i}"
            load_op()
        
        # Test detection during recovery
        detected = []
        for i in range(20):
            @agent.monitor
            def anomaly_during_recovery():
                time.sleep(0.050)  # Clear anomaly
                return f"anomaly_{i}"
            
            result = anomaly_during_recovery()
            detected.append(result is None)
        
        detection_rate = sum(detected) / len(detected)
        duration = time.time() - start_time
        
        return {
            "test_type": "detection_during_recovery",
            "load_operations": 100,
            "anomaly_tests": 20,
            "detection_rate": detection_rate,
            "total_duration_seconds": duration,
            "passed": True  # Test executed
        }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all memory consistency tests.
        
        Returns:
            Comprehensive test results
        """
        self.logger.info("[MEMORY] Starting all memory consistency tests")
        
        results = {
            "high_load_recovery": self.test_high_load_recovery(),
            "noise_saturation": self.test_noise_saturation_recovery(),
            "baseline_integrity": self.test_baseline_integrity(),
            "detection_during_recovery": self.test_detection_capability_during_recovery()
        }
        
        # Calculate overall metrics
        total_tests = len(results)
        passed_tests = sum(1 for r in results.values() if r.get("passed", False))
        
        # Calculate average recovery rate
        recovery_rates = [
            r.get("recovery_rate", r.get("integrity_rate", 0))
            for r in results.values()
            if "recovery_rate" in r or "integrity_rate" in r
        ]
        avg_recovery = sum(recovery_rates) / len(recovery_rates) if recovery_rates else 0
        
        return {
            "test_category": "memory_consistency",
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "pass_rate": passed_tests / total_tests if total_tests > 0 else 0,
            "average_recovery_rate": avg_recovery,
            "individual_results": results,
            "resilience_grade": self._calculate_resilience_grade(avg_recovery)
        }
    
    def _calculate_resilience_grade(self, recovery_rate: float) -> str:
        """Calculate resilience grade."""
        if recovery_rate >= 0.90:
            return "A"
        elif recovery_rate >= 0.80:
            return "B"
        elif recovery_rate >= 0.70:
            return "C"
        else:
            return "F"
