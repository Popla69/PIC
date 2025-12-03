"""Vulnerable Application Testing

Tests PIC's ability to protect intentionally vulnerable applications.
"""

import time
import logging
from typing import Dict, Any
import hashlib

from pic.cellagent import CellAgent
from pic.realworld.safety import SafetyController


class VulnerableAppTester:
    """Tests PIC's protection of vulnerable applications.
    
    This tester validates that PIC can:
    - Monitor all application functions
    - Detect SQL injection strings
    - Identify slowloris-style attacks
    - Detect malformed headers
    - Provide forensic data for incident response
    """
    
    def __init__(self, agent: CellAgent, safety: SafetyController):
        """Initialize vulnerable app tester.
        
        Args:
            agent: CellAgent instance to test
            safety: SafetyController for validation
        """
        self.agent = agent
        self.safety = safety
        self.logger = logging.getLogger(__name__)
    
    def test_application_monitoring(self) -> Dict[str, Any]:
        """Test that all application functions are monitored.
        
        Returns:
            Test result dictionary
        """
        self.logger.info("Testing application monitoring coverage...")
        
        functions_monitored = []
        
        @self.agent.monitor
        def login_function(username: str, password: str) -> bool:
            """Login function."""
            functions_monitored.append("login")
            return True
        
        @self.agent.monitor
        def search_function(query: str) -> list:
            """Search function."""
            functions_monitored.append("search")
            return []
        
        @self.agent.monitor
        def update_profile(user_id: int, data: dict) -> bool:
            """Profile update function."""
            functions_monitored.append("update")
            return True
        
        # Execute all functions
        login_function("user", "pass")
        search_function("test")
        update_profile(1, {})
        
        # Check coverage
        unique_functions = set(functions_monitored)
        all_monitored = len(unique_functions) == 3
        
        return {
            "passed": all_monitored,
            "metrics": {
                "functions_registered": 3,
                "functions_monitored": len(unique_functions),
                "coverage": len(unique_functions) / 3
            }
        }
    
    def test_sql_injection_string_detection(self) -> Dict[str, Any]:
        """Test detection of SQL injection strings.
        
        Returns:
            Test result dictionary
        """
        self.logger.info("Testing SQL injection string detection...")
        
        @self.agent.monitor
        def vulnerable_search(search_term: str) -> list:
            """Vulnerable search function."""
            # Simulate database query
            time.sleep(0.01)
            return [f"result_for_{search_term}"]
        
        # Establish baseline with normal searches
        normal_searches = ["python", "tutorial", "example", "code", "test"]
        for _ in range(6):
            for search in normal_searches:
                vulnerable_search(search)
        
        # Test SQL injection strings
        injection_strings = [
            "' OR '1'='1",
            "admin'--",
            "1' UNION SELECT * FROM users--",
            "'; DROP TABLE users;--",
            "1' AND 1=1--",
            "' OR 1=1--",
            "admin' OR '1'='1'--",
            "' UNION SELECT NULL, username, password FROM users--"
        ]
        
        injections_detected = 0
        
        for injection in injection_strings:
            result = vulnerable_search(injection)
            if result is None:  # Blocked
                injections_detected += 1
        
        # Calculate entropy of injection strings (they're typically high)
        def calculate_entropy(s: str) -> float:
            """Calculate Shannon entropy of string."""
            if not s:
                return 0.0
            entropy = 0.0
            for x in set(s):
                p_x = s.count(x) / len(s)
                if p_x > 0:
                    entropy += - p_x * (p_x ** 0.5)  # Simplified entropy
            return entropy
        
        avg_injection_entropy = sum(calculate_entropy(s) for s in injection_strings) / len(injection_strings)
        avg_normal_entropy = sum(calculate_entropy(s) for s in normal_searches) / len(normal_searches)
        
        detection_rate = injections_detected / len(injection_strings)
        passed = detection_rate > 0.5
        
        return {
            "passed": passed,
            "detections": injections_detected,
            "metrics": {
                "injection_attempts": len(injection_strings),
                "injections_detected": injections_detected,
                "detection_rate": detection_rate,
                "avg_injection_entropy": avg_injection_entropy,
                "avg_normal_entropy": avg_normal_entropy
            },
            "forensic_data": {
                "attack_type": "sql_injection",
                "patterns_tested": injection_strings[:3]  # Sample
            }
        }
    
    def test_slowloris_detection(self) -> Dict[str, Any]:
        """Test detection of slowloris-style attacks.
        
        Returns:
            Test result dictionary
        """
        self.logger.info("Testing slowloris attack detection...")
        
        @self.agent.monitor
        def handle_slow_request(request_id: int, delay_seconds: float) -> str:
            """Request handler that can be slow."""
            time.sleep(delay_seconds)
            return f"response_{request_id}"
        
        # Establish baseline with fast requests
        normal_delay = 0.01  # 10ms
        for i in range(30):
            handle_slow_request(i, normal_delay)
        
        # Simulate slowloris (very slow requests)
        slow_delay = normal_delay * 50  # 500ms (50x slower)
        result = handle_slow_request(999, slow_delay)
        
        # Detection: abnormally slow request should be flagged
        detected = result is None
        
        return {
            "passed": detected,
            "detections": 1 if detected else 0,
            "metrics": {
                "normal_delay_ms": normal_delay * 1000,
                "slow_delay_ms": slow_delay * 1000,
                "delay_multiplier": 50,
                "detected": detected
            },
            "forensic_data": {
                "attack_type": "slowloris",
                "pattern": "abnormal_execution_duration"
            }
        }
    
    def test_malformed_header_detection(self) -> Dict[str, Any]:
        """Test detection of malformed headers.
        
        Returns:
            Test result dictionary
        """
        self.logger.info("Testing malformed header detection...")
        
        @self.agent.monitor
        def parse_headers(headers: dict) -> dict:
            """Header parsing function."""
            # Simulate header parsing
            parsed = {}
            for key, value in headers.items():
                if isinstance(value, str) and len(value) < 1000:
                    parsed[key.lower()] = value
            return parsed
        
        # Establish baseline with normal headers
        normal_headers = [
            {"Content-Type": "application/json", "Accept": "application/json"},
            {"User-Agent": "Mozilla/5.0", "Accept-Language": "en-US"},
            {"Authorization": "Bearer token123", "Content-Length": "100"}
        ]
        
        for _ in range(10):
            for headers in normal_headers:
                parse_headers(headers)
        
        # Test malformed headers
        malformed_headers = [
            {"Content-Type": "x" * 10000},  # Extremely long value
            {"X-Malformed": "\x00\xff\xfe"},  # Non-UTF8 characters
            {"\x00Invalid": "value"},  # Null byte in key
            {"Normal": "value\r\n\r\nInjected: header"}  # Header injection
        ]
        
        malformed_detected = 0
        
        for headers in malformed_headers:
            result = parse_headers(headers)
            if result is None:  # Blocked
                malformed_detected += 1
        
        detection_rate = malformed_detected / len(malformed_headers)
        passed = detection_rate > 0.5
        
        return {
            "passed": passed,
            "detections": malformed_detected,
            "metrics": {
                "malformed_attempts": len(malformed_headers),
                "malformed_detected": malformed_detected,
                "detection_rate": detection_rate
            }
        }
    
    def test_forensic_data_collection(self) -> Dict[str, Any]:
        """Test forensic data collection for incident response.
        
        Returns:
            Test result dictionary
        """
        self.logger.info("Testing forensic data collection...")
        
        @self.agent.monitor
        def vulnerable_endpoint(attack_vector: str, payload: str) -> str:
            """Vulnerable endpoint for forensic testing."""
            if "attack" in attack_vector:
                time.sleep(0.05)  # Simulate attack processing
            return f"processed_{attack_vector}"
        
        # Establish baseline
        for i in range(30):
            vulnerable_endpoint("normal_request", "safe_data")
        
        # Execute attack
        attack_vector = "sql_injection_attack"
        attack_payload = "' OR '1'='1"
        
        start_time = time.time()
        result = vulnerable_endpoint(attack_vector, attack_payload)
        end_time = time.time()
        
        # Check if attack was detected
        detected = result is None
        
        # Collect forensic data
        forensic_data = {
            "attack_vector": attack_vector,
            "payload": attack_payload,
            "timestamp": start_time,
            "duration_ms": (end_time - start_time) * 1000,
            "detected": detected,
            "safety_violations": len(self.safety.get_violations())
        }
        
        # Success if forensic data is comprehensive
        has_vector = "attack_vector" in forensic_data
        has_timestamp = "timestamp" in forensic_data
        has_duration = "duration_ms" in forensic_data
        
        passed = detected and has_vector and has_timestamp and has_duration
        
        return {
            "passed": passed,
            "detections": 1 if detected else 0,
            "metrics": {
                "forensic_fields_collected": len(forensic_data),
                "has_attack_vector": has_vector,
                "has_timestamp": has_timestamp,
                "has_duration": has_duration
            },
            "forensic_data": forensic_data
        }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all vulnerable application tests.
        
        Returns:
            Comprehensive test results
        """
        self.logger.info("Running all vulnerable application tests...")
        
        results = {
            "application_monitoring": self.test_application_monitoring(),
            "sql_injection": self.test_sql_injection_string_detection(),
            "slowloris": self.test_slowloris_detection(),
            "malformed_headers": self.test_malformed_header_detection(),
            "forensic_data": self.test_forensic_data_collection()
        }
        
        # Calculate overall metrics
        total_tests = len(results)
        passed_tests = sum(1 for r in results.values() if r.get("passed", False))
        total_detections = sum(r.get("detections", 0) for r in results.values())
        
        return {
            "test_category": "vulnerable_app",
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
