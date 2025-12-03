"""Microservice Attack Simulation Testing

Tests PIC's ability to protect microservices from various attacks.
"""

import time
import logging
from typing import Dict, Any
import psutil
import os

from pic.cellagent import CellAgent
from pic.realworld.safety import SafetyController


class MicroserviceTester:
    """Tests PIC's microservice protection capabilities.
    
    This tester validates that PIC can:
    - Detect authentication failure spikes
    - Identify unusual transaction patterns
    - Correlate CPU usage with function execution
    - Detect payload size anomalies
    - Maintain independent baselines per service
    """
    
    def __init__(self, agent: CellAgent, safety: SafetyController):
        """Initialize microservice tester.
        
        Args:
            agent: CellAgent instance to test
            safety: SafetyController for validation
        """
        self.agent = agent
        self.safety = safety
        self.logger = logging.getLogger(__name__)
        self.process = psutil.Process(os.getpid())
    
    def test_auth_failure_detection(self) -> Dict[str, Any]:
        """Test detection of authentication failure spikes.
        
        Returns:
            Test result dictionary
        """
        self.logger.info("Testing auth failure detection...")
        
        @self.agent.monitor
        def authenticate_user(username: str, password: str, fail: bool = False) -> bool:
            """Authentication function."""
            if fail:
                time.sleep(0.01)  # Failed auth takes slightly longer
                return False
            return True
        
        # Establish baseline with normal auth (mostly successful)
        for i in range(30):
            authenticate_user(f"user{i}", "correct_password", fail=False)
        
        # Simulate auth failure spike (brute force attempt)
        failure_count = 50
        failures_detected = 0
        
        for i in range(failure_count):
            result = authenticate_user("admin", f"wrong_pass_{i}", fail=True)
            if result is None:  # Blocked by PIC
                failures_detected += 1
        
        # Detection: spike in failures should be flagged
        detected = failures_detected > 0
        
        return {
            "passed": detected,
            "detections": failures_detected,
            "metrics": {
                "failure_attempts": failure_count,
                "failures_detected": failures_detected,
                "detection_rate": failures_detected / failure_count
            },
            "forensic_data": {
                "attack_type": "brute_force_auth",
                "pattern": "authentication_failure_spike"
            }
        }
    
    def test_transaction_pattern_detection(self) -> Dict[str, Any]:
        """Test detection of unusual transaction patterns.
        
        Returns:
            Test result dictionary
        """
        self.logger.info("Testing transaction pattern detection...")
        
        @self.agent.monitor
        def process_transaction(amount: float, transaction_type: str) -> str:
            """Transaction processing function."""
            # Simulate processing time
            time.sleep(0.005)
            return f"transaction_{transaction_type}_completed"
        
        # Establish baseline with normal transactions
        normal_amount = 100.0
        for i in range(30):
            process_transaction(normal_amount, "purchase")
        
        # Simulate unusual transaction pattern (very large amount)
        unusual_amount = normal_amount * 1000  # 1000x normal
        result = process_transaction(unusual_amount, "purchase")
        
        # Detection: unusual transaction should be flagged
        detected = result is None
        
        return {
            "passed": detected,
            "detections": 1 if detected else 0,
            "metrics": {
                "normal_amount": normal_amount,
                "unusual_amount": unusual_amount,
                "amount_multiplier": 1000,
                "detected": detected
            }
        }
    
    def test_cpu_correlation(self) -> Dict[str, Any]:
        """Test CPU correlation with function execution.
        
        Returns:
            Test result dictionary
        """
        self.logger.info("Testing CPU correlation...")
        
        @self.agent.monitor
        def cpu_intensive_operation(intensity: int) -> int:
            """CPU-intensive operation."""
            # Simulate CPU work
            result = 0
            for i in range(intensity * 1000):
                result += i ** 2
            return result
        
        # Establish baseline with low intensity
        baseline_intensity = 10
        for i in range(30):
            cpu_intensive_operation(baseline_intensity)
        
        # Execute high-intensity operation
        high_intensity = baseline_intensity * 50
        
        cpu_before = self.process.cpu_percent()
        result = cpu_intensive_operation(high_intensity)
        cpu_after = self.process.cpu_percent()
        
        # Detection: high CPU usage should correlate with execution
        detected = result is None
        cpu_spike = cpu_after > cpu_before
        
        return {
            "passed": detected or cpu_spike,
            "detections": 1 if detected else 0,
            "metrics": {
                "baseline_intensity": baseline_intensity,
                "high_intensity": high_intensity,
                "cpu_before": cpu_before,
                "cpu_after": cpu_after,
                "cpu_spike_detected": cpu_spike,
                "operation_detected": detected
            }
        }
    
    def test_payload_size_detection(self) -> Dict[str, Any]:
        """Test detection of payload size anomalies.
        
        Returns:
            Test result dictionary
        """
        self.logger.info("Testing payload size detection...")
        
        @self.agent.monitor
        def process_payload(data: str) -> int:
            """Payload processing function."""
            return len(data)
        
        # Establish baseline with normal payload sizes
        normal_size = 1000
        for i in range(30):
            process_payload("x" * normal_size)
        
        # Send oversized payload (100x normal)
        oversized_payload = "x" * (normal_size * 100)
        result = process_payload(oversized_payload)
        
        # Detection: oversized payload should be flagged
        detected = result is None
        
        return {
            "passed": detected,
            "detections": 1 if detected else 0,
            "metrics": {
                "normal_size": normal_size,
                "oversized_size": len(oversized_payload),
                "size_multiplier": 100,
                "detected": detected
            }
        }
    
    def test_independent_baselines(self) -> Dict[str, Any]:
        """Test that multiple services maintain independent baselines.
        
        Returns:
            Test result dictionary
        """
        self.logger.info("Testing independent baselines...")
        
        @self.agent.monitor
        def auth_service_operation(delay_ms: float) -> str:
            """Auth service operation."""
            time.sleep(delay_ms / 1000.0)
            return "auth_completed"
        
        @self.agent.monitor
        def billing_service_operation(delay_ms: float) -> str:
            """Billing service operation."""
            time.sleep(delay_ms / 1000.0)
            return "billing_completed"
        
        # Establish different baselines for each service
        auth_baseline = 10  # 10ms
        billing_baseline = 50  # 50ms (slower service)
        
        for i in range(30):
            auth_service_operation(auth_baseline)
            billing_service_operation(billing_baseline)
        
        # Test that each service has independent baseline
        # Auth service with billing-like delay should be anomalous
        auth_result = auth_service_operation(billing_baseline)
        auth_detected = auth_result is None
        
        # Billing service with normal billing delay should be fine
        billing_result = billing_service_operation(billing_baseline)
        billing_normal = billing_result is not None
        
        # Success if baselines are independent
        passed = auth_detected and billing_normal
        
        return {
            "passed": passed,
            "detections": 1 if auth_detected else 0,
            "metrics": {
                "auth_baseline_ms": auth_baseline,
                "billing_baseline_ms": billing_baseline,
                "auth_anomaly_detected": auth_detected,
                "billing_normal_accepted": billing_normal,
                "baselines_independent": passed
            }
        }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all microservice tests.
        
        Returns:
            Comprehensive test results
        """
        self.logger.info("Running all microservice tests...")
        
        results = {
            "auth_failure": self.test_auth_failure_detection(),
            "transaction_pattern": self.test_transaction_pattern_detection(),
            "cpu_correlation": self.test_cpu_correlation(),
            "payload_size": self.test_payload_size_detection(),
            "independent_baselines": self.test_independent_baselines()
        }
        
        # Calculate overall metrics
        total_tests = len(results)
        passed_tests = sum(1 for r in results.values() if r.get("passed", False))
        total_detections = sum(r.get("detections", 0) for r in results.values())
        
        return {
            "test_category": "microservice",
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
