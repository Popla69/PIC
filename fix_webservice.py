#!/usr/bin/env python3
"""Fix the webservice.py file"""

content = '''"""Web Service Integration Testing

Tests PIC's ability to detect web service attacks in safe mode.
"""

import time
import logging
from pathlib import Path
from typing import Dict, Any

from pic.cellagent import CellAgent
from pic.realworld.safety import SafetyController


class WebServiceTester:
    """Tests PIC's web service attack detection capabilities."""
    
    def __init__(self, agent: CellAgent, safety: SafetyController):
        """Initialize web service tester."""
        self.agent = agent
        self.safety = safety
        self.logger = logging.getLogger(__name__)
    
    def test_ddos_pattern(self) -> Dict[str, Any]:
        """Test detection of DDoS patterns."""
        self.logger.info("Testing DDoS pattern detection...")
        
        @self.agent.monitor
        def handle_request(request_id: str, request_rate: int) -> str:
            """Simulated request handler."""
            time.sleep(0.001 / request_rate if request_rate > 0 else 0.001)
            return f"response_{request_id}"
        
        # Establish baseline
        for i in range(30):
            handle_request(f"normal_{i}", 10)
        
        # Simulate DDoS
        result = handle_request("ddos_001", 1000)
        detected = result is None
        
        return {
            "passed": detected,
            "detections": 1 if detected else 0,
            "metrics": {"baseline_rate": 10, "attack_rate": 1000, "detected": detected},
            "forensic_data": {"attack_type": "ddos", "pattern": "request_flood"}
        }
    
    def test_sql_injection(self) -> Dict[str, Any]:
        """Test detection of SQL injection patterns."""
        self.logger.info("Testing SQL injection detection...")
        
        @self.agent.monitor
        def execute_query(query: str, complexity: int) -> str:
            """Simulated query execution."""
            time.sleep(complexity * 0.001)
            return f"result_{len(query)}"
        
        # Establish baseline
        for i in range(30):
            execute_query(f"SELECT * FROM users WHERE id={i}", 1)
        
        # Simulate SQL injection
        result = execute_query("' OR '1'='1", 50)
        detected = result is None
        
        return {
            "passed": detected,
            "detections": 1 if detected else 0,
            "metrics": {"baseline_complexity": 1, "injection_complexity": 50, "detected": detected},
            "forensic_data": {"attack_type": "sql_injection", "pattern": "malicious_query"}
        }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all web service tests."""
        self.logger.info("Running all web service tests...")
        
        results = {
            "ddos": self.test_ddos_pattern(),
            "sql_injection": self.test_sql_injection()
        }
        
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
            "metrics": {"tests_passed": passed_tests, "tests_failed": total_tests - passed_tests}
        }
'''

with open('src/pic/realworld/testers/webservice.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("File written successfully!")
print(f"File size: {len(content)} bytes")

# Verify
with open('src/pic/realworld/testers/webservice.py', 'r', encoding='utf-8') as f:
    verify = f.read()
    print(f"Verified size: {len(verify)} bytes")
    print(f"Contains WebServiceTester: {'WebServiceTester' in verify}")
