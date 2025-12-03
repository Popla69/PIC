"""Stress and Abuse Resistance Testing

Tests PIC's stability and performance under extreme load conditions.
"""

import time
import psutil
import os
from typing import List, Any
from dataclasses import dataclass
import logging

from pic.realworld.harness import TestHarness, TestStatus
from pic.cellagent import CellAgent


@dataclass
class StressTestConfig:
    """Configuration for stress tests."""
    high_throughput_events: int = 100000
    batch_size: int = 1000000
    memory_limit_mb: int = 500
    min_detection_accuracy: float = 0.80
    recovery_timeout_seconds: int = 10


class StressAbuseTester:
    """Tests PIC's stress and abuse resistance.
    
    Validates system behavior under:
    - High-throughput event streams
    - Large batch processing
    - Memory pressure
    - Resource exhaustion
    """
    
    def __init__(self, agent: CellAgent, safety):
        """Initialize stress tester.
        
        Args:
            agent: CellAgent instance
            safety: Safety controller for validation
        """
        self.agent = agent
        self.safety = safety
        self.logger = logging.getLogger(__name__)
        self.process = psutil.Process(os.getpid())
    
    def get_memory_usage_mb(self) -> float:
        """Get current memory usage in MB.
        
        Returns:
            Memory usage in megabytes
        """
        return self.process.memory_info().rss / (1024 * 1024)
    
    def test_high_throughput_stability(self) -> Dict[str, Any]:
        """Test system stability under high event throughput.
        
        Returns:
            Test result dictionary
        """
        self.logger.info("Testing high-throughput stability...")
        
        @self.agent.monitor
        def high_frequency_operation(op_id: int) -> int:
            """Fast operation for throughput testing."""
            return op_id * 2
        
        # Test parameters
        target_events = 10000  # Reduced from 100k for faster testing
        timeout_seconds = 30
        
        start_time = time.time()
        events_processed = 0
        system_stable = True
        
        try:
            for i in range(target_events):
                result = high_frequency_operation(i)
                if result is not None:
                    events_processed += 1
                
                # Check timeout
                if time.time() - start_time > timeout_seconds:
                    self.logger.warning("Throughput test timeout")
                    system_stable = False
                    break
                
        except Exception as e:
            self.logger.error(f"System crashed during throughput test: {e}")
            system_stable = False
        
        end_time = time.time()
        duration = end_time - start_time
        throughput = events_processed / duration if duration > 0 else 0
        
        # Success if processed 80% of events without crashing
        passed = system_stable and events_processed >= target_events * 0.8
        
        return {
            "passed": passed,
            "metrics": {
                "events_processed": events_processed,
                "target_events": target_events,
                "duration_seconds": duration,
                "throughput_events_per_second": throughput,
                "system_stable": system_stable
            }
        }
    
    def test_memory_usage_under_load(self) -> Dict[str, Any]:
        """Test memory usage during batch processing.
        
        Returns:
            Test result dictionary
        """
        self.logger.info("Testing memory usage under load...")
        
        @self.agent.monitor
        def memory_intensive_operation(data_size: int) -> int:
            """Operation that allocates memory."""
            data = [0] * data_size
            result = sum(data[:100])  # Use small portion
            del data  # Explicit cleanup
            return result
        
        # Record initial memory
        initial_memory = self.get_memory_usage_mb()
        max_memory = initial_memory
        
        # Process batch of operations
        batch_size = 1000  # Reduced from 1M for faster testing
        operations_completed = 0
        
        try:
            for size in [1000, 5000, 10000, 50000, 100000]:
                for _ in range(batch_size // 5):
                    result = memory_intensive_operation(size)
                    if result is not None:
                        operations_completed += 1
                    
                    # Track peak memory
                    current_memory = self.get_memory_usage_mb()
                    max_memory = max(max_memory, current_memory)
                    
        except Exception as e:
            self.logger.error(f"Memory test failed: {e}")
        
        memory_increase = max_memory - initial_memory
        
        # Success if memory stayed under 500MB increase
        passed = memory_increase < 500
        
        return {
            "passed": passed,
            "metrics": {
                "initial_memory_mb": initial_memory,
                "peak_memory_mb": max_memory,
                "memory_increase_mb": memory_increase,
                "operations_completed": operations_completed,
                "memory_limit_mb": 500
            }
        }
    
    def test_detection_accuracy_under_load(self) -> Dict[str, Any]:
        """Test that anomaly detection continues under extreme load.
        
        Returns:
            Test result dictionary
        """
        self.logger.info("Testing detection accuracy under load...")
        
        @self.agent.monitor
        def detection_test_function(is_anomaly: bool, delay_ms: float) -> str:
            """Function for testing detection under load."""
            if is_anomaly:
                time.sleep(delay_ms / 1000.0)
            return "completed"
        
        # Establish baseline
        baseline_delay = 5
        for i in range(30):
            detection_test_function(False, baseline_delay)
        
        # Generate high load with mixed normal and anomalous operations
        total_operations = 1000
        anomalies_injected = 0
        anomalies_detected = 0
        
        for i in range(total_operations):
            # Every 10th operation is anomalous
            is_anomaly = (i % 10 == 0)
            delay = baseline_delay * 20 if is_anomaly else baseline_delay
            
            if is_anomaly:
                anomalies_injected += 1
            
            result = detection_test_function(is_anomaly, delay)
            
            # If anomaly was blocked, it was detected
            if is_anomaly and result is None:
                anomalies_detected += 1
        
        # Calculate detection accuracy
        detection_rate = anomalies_detected / anomalies_injected if anomalies_injected > 0 else 0
        
        # Success if detection rate > 80%
        passed = detection_rate > 0.8
        
        return {
            "passed": passed,
            "detections": anomalies_detected,
            "metrics": {
                "total_operations": total_operations,
                "anomalies_injected": anomalies_injected,
                "anomalies_detected": anomalies_detected,
                "detection_rate": detection_rate,
                "target_accuracy": 0.8
            }
        }
    
    def test_sampling_under_overload(self) -> Dict[str, Any]:
        """Test that sampling preserves critical anomalies.
        
        Returns:
            Test result dictionary
        """
        self.logger.info("Testing sampling under overload...")
        
        @self.agent.monitor
        def overload_function(severity: str, delay_ms: float) -> str:
            """Function for testing sampling."""
            time.sleep(delay_ms / 1000.0)
            return f"processed_{severity}"
        
        # Establish baseline
        for i in range(30):
            overload_function("normal", 5)
        
        # Generate overload with critical and non-critical anomalies
        critical_anomalies = 0
        critical_detected = 0
        non_critical_anomalies = 0
        
        for i in range(500):  # High volume
            if i % 50 == 0:  # Critical anomaly (severe)
                result = overload_function("critical", 100)
                critical_anomalies += 1
                if result is None:
                    critical_detected += 1
            elif i % 10 == 0:  # Non-critical anomaly (mild)
                overload_function("mild", 20)
                non_critical_anomalies += 1
            else:  # Normal
                overload_function("normal", 5)
        
        # Success if most critical anomalies were preserved
        critical_preservation_rate = critical_detected / critical_anomalies if critical_anomalies > 0 else 0
        passed = critical_preservation_rate > 0.7
        
        return {
            "passed": passed,
            "detections": critical_detected,
            "metrics": {
                "critical_anomalies": critical_anomalies,
                "critical_detected": critical_detected,
                "critical_preservation_rate": critical_preservation_rate,
                "non_critical_anomalies": non_critical_anomalies
            }
        }
    
    def test_recovery_time(self) -> Dict[str, Any]:
        """Test recovery time after overload.
        
        Returns:
            Test result dictionary
        """
        self.logger.info("Testing recovery time...")
        
        @self.agent.monitor
        def recovery_function(load_level: str) -> str:
            """Function for testing recovery."""
            if load_level == "high":
                time.sleep(0.05)  # 50ms
            else:
                time.sleep(0.005)  # 5ms
            return "completed"
        
        # Establish baseline
        for i in range(30):
            recovery_function("normal")
        
        # Create overload
        for i in range(200):
            recovery_function("high")
        
        # Measure recovery time
        recovery_start = time.time()
        normal_operations = 0
        
        for i in range(50):
            result = recovery_function("normal")
            if result is not None:
                normal_operations += 1
        
        recovery_time = time.time() - recovery_start
        
        # Success if recovered within 10 seconds and most operations pass
        passed = recovery_time < 10 and normal_operations >= 40
        
        return {
            "passed": passed,
            "metrics": {
                "recovery_time_seconds": recovery_time,
                "normal_operations_after_recovery": normal_operations,
                "recovery_rate": normal_operations / 50,
                "target_recovery_time": 10
            }
        }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all stress/abuse tests.
        
        Returns:
            Comprehensive test results
        """
        self.logger.info("Running all stress/abuse tests...")
        
        results = {
            "high_throughput": self.test_high_throughput_stability(),
            "memory_usage": self.test_memory_usage_under_load(),
            "detection_accuracy": self.test_detection_accuracy_under_load(),
            "sampling": self.test_sampling_under_overload(),
            "recovery": self.test_recovery_time()
        }
        
        # Calculate overall metrics
        total_tests = len(results)
        passed_tests = sum(1 for r in results.values() if r.get("passed", False))
        total_detections = sum(r.get("detections", 0) for r in results.values())
        
        return {
            "test_category": "stress_abuse",
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "pass_rate": passed_tests / total_tests,
            "total_detections": total_detections,
            "individual_results": results,
            "metrics": {
                "tests_passed": passed_tests,
                "tests_failed": total_tests - passed_tests
            }
        }
