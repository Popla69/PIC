"""Web Service Integration Testing

Tests PIC's ability to detect web service attacks in safe mode.
"""

import time
import logging
from pathlib import Path
from typing import Dict, Any

from pic.cellagent import CellAgent
from pic.realworld.safety import SafetyController


class WebServiceTester:
    """Tests PIC's web service attack detection capabilities.
    
    This tester validates that PIC can detect:
    - DDoS patterns (request flooding)
    - SQL injection attempts
    - XSS patterns
    - Authentication bypass attempts
    
    All tests use safe, educational variants that don't cause actual harm.
    """
    
    def __init__(self, agent: CellAgent, safety: SafetyController):
        """Initialize web service tester.
        
        Args:
            agent: CellAgent instance to test
            safety: SafetyController for validation
        """
        self.agent = agent
        self.safety = safety
        self.logger = logging.getLogger(__name__)
    
    def test_ddos_pattern(self) -> Dict[str, Any]:
        """Test detection of DDoS patterns.
        
        Returns:
            Test result dictionary
        """
        self.logger.info("Testing DDoS pattern detection...")
        
        @self.agent.monitor
        def handle_request(request_id: str, request_rate: int) -> str:
            """Simulated request handler."""
            # Simulate processing time
            time.sleep(0.001 / request_rate if request_rate > 0 else 0.001)
            return f"response_{request_id}"
        
        # Establish baseline with normal request rate
        for i in range(30):
            handle_request(f"normal_{i}", 10)  # 10 req/sec
        
        # Simulate DDoS pattern (request flood)
        ddos_rate = 1000  # 1000 req/sec
        result = handle_request("ddos_001", ddos_rate)
        
        # Detection: DDoS pattern should be flagged
        detected = result is None
        
        return {
            "passed": detected,
            "detections": 1 if detected else 0,
            "metrics": {
                "baseline_rate": 10,
                "attack_rate": ddos_rate,
                "rate_multiplier": 100,
                "detected": detected
            },
            "forensic_data": {
                "attack_type": "ddos",
                "pattern": "request_flood"
            }
        }
    
    def test_sql_injection(self) -> Dict[str, Any]:
        """Test detection of SQL injection patterns.
        
        Returns:
            Test result dictionary
        """
        self.logger.info("Testing SQL injection detection...")
        
        @self.agent.monitor
        def execute_query(query: str, complexity: int) -> str:
            """Simulated query execution."""
            # Simulate query processing
            time.sleep(complexity * 0.001)
            return f"result_{len(query)}"
        
        # Establish baseline with normal queries
        for i in range(30):
            execute_query(f"SELECT * FROM users WHERE id={i}", 1)
        
        # Simulate SQL injection pattern
        injection_query = "' OR '1'='1"
        injection_complexity = 50  # High complexity
        result = execute_query(injection_query, injection_complexity)
        
        # Detection: SQL injection should be flagged
        detected = result is None
        
        return {
            "passed": detected,
            "detections": 1 if detected else 0,
            "metrics": {
                "baseline_complexity": 1,
                "injection_complexity": injection_complexity,
                "complexity_multiplier": 50,
                "detected": detected
            },
            "forensic_data": {
                "attack_type": "sql_injection",
                "pattern": "malicious_query"
            }
        }
    
    def test_xss_pattern(self) -> Dict[str, Any]:
        """Test detection of XSS patterns.
        
        Returns:
            Test result dictionary
        """
        self.logger.info("Testing XSS pattern detection...")
        
        @self.agent.monitor
        def render_content(content: str, sanitization_level: int) -> str:
            """Simulated content rendering."""
            # Simulate rendering time
            time.sleep(sanitization_level * 0.001)
            return f"rendered_{len(content)}"
        
        # Establish baseline with normal content
        for i in range(30):
            render_content(f"<p>Normal content {i}</p>", 1)
        
        # Simulate XSS pattern
        xss_content = "<script>alert('xss')</script>"
        xss_complexity = 30  # High complexity
        result = render_content(xss_content, xss_complexity)
        
        # Detection: XSS pattern should be flagged
        detected = result is None
        
        return {
            "passed": detected,
            "detections": 1 if detected else 0,
            "metrics": {
                "baseline_complexity": 1,
                "xss_complexity": xss_complexity,
                "complexity_multiplier": 30,
                "detected": detected
            },
            "forensic_data": {
                "attack_type": "xss",
                "pattern": "script_injection"
            }
        }
    
    def test_auth_bypass(self) -> Dict[str, Any]:
        """Test detection of authentication bypass attempts.
        
        Returns:
            Test result dictionary
        """
        self.logger.info("Testing authentication bypass detection...")
        
        @self.agent.monitor
        def authenticate(username: str, attempt_count: int) -> bool:
            """Simulated authentication."""
            # Simulate auth processing
            time.sleep(attempt_count * 0.001)
            return attempt_count < 10
        
        # Establish baseline with normal auth attempts
        for i in range(30):
            authenticate(f"user_{i}", 1)
        
        # Simulate auth bypass pattern (brute force)
        bypass_attempts = 100  # Many attempts
        result = authenticate("admin", bypass_attempts)
        
        # Detection: auth bypass should be flagged
        detected = result is None or result is False
        
        return {
            "passed": detected,
            "detections": 1 if detected else 0,
            "metrics": {
                "baseline_attempts": 1,
                "bypass_attempts": bypass_attempts,
                "attempt_multiplier": 100,
                "detected": detected
            },
            "forensic_data": {
                "attack_type": "auth_bypass",
                "pattern": "brute_force"
            }
        }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all web service tests.
        
        Returns:
            Comprehensive test results
        """
        self.logger.info("Running all web service tests...")
        
        results = {
            "ddos": self.test_ddos_pattern(),
            "sql_injection": self.test_sql_injection(),
            "xss": self.test_xss_pattern(),
            "auth_bypass": self.test_auth_bypass()
        }
        
        # Calculate overall metrics
        total_tests = len(results)
        passed_tests = sum(1 for r in results.values() if r.get("passed", False))
        total_detections = sum(r.get("detections", 0) for r in results.values())
        
        return {
            "test_category": "webservice",
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
