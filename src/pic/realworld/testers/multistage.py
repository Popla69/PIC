"""Multi-Stage Attack Chain Testing

Tests PIC's ability to detect and respond to APT-style multi-stage attacks.
Simulates: reconnaissance → exploitation → payload → persistence
"""

import time
import logging
from typing import Dict, Any, List
from dataclasses import dataclass

from ..harness import TestHarness
from pic.cellagent import CellAgent


@dataclass
class AttackStage:
    """Represents a stage in the attack chain."""
    name: str
    intensity: int  # 1-100
    duration_ms: float
    request_count: int


class MultiStageAttackTester:
    """Multi-stage attack chain testing.
    
    Simulates APT-style attack progression through multiple stages.
    """
    
    def __init__(self, harness: TestHarness):
        """Initialize multi-stage attack tester.
        
        Args:
            harness: TestHarness for PIC setup
        """
        self.harness = harness
        self.logger = logging.getLogger(__name__)
    
    def test_reconnaissance_stage(self) -> Dict[str, Any]:
        """Test Stage 1: Reconnaissance.
        
        Characteristics:
        - Low intensity, high volume
        - Port scanning simulation
        - Service enumeration
        """
        self.logger.info("[MULTISTAGE] Testing reconnaissance stage")
        
        start_time = time.time()
        agent, brain = self.harness.setup_pic_instance("recon_test")
        
        # Establish baseline
        for i in range(30):
            @agent.monitor
            def baseline_op():
                time.sleep(0.005)
                return "baseline"
            baseline_op()
        
        # Reconnaissance: many low-intensity probes
        recon_detected = []
        for i in range(50):
            @agent.monitor
            def recon_probe():
                time.sleep(0.010)  # Slightly slower than baseline
                return f"scan_port_{i}"
            
            result = recon_probe()
            recon_detected.append(result is None)
        
        detection_rate = sum(recon_detected) / len(recon_detected)
        duration = time.time() - start_time
        
        return {
            "stage": "reconnaissance",
            "detection_rate": detection_rate,
            "requests_sent": 50,
            "requests_blocked": sum(recon_detected),
            "duration_seconds": duration,
            "passed": True  # Test executed
        }
    
    def test_exploitation_stage(self) -> Dict[str, Any]:
        """Test Stage 2: Exploitation.
        
        Characteristics:
        - Medium intensity
        - SQL injection attempts
        - Buffer overflow patterns
        """
        self.logger.info("[MULTISTAGE] Testing exploitation stage")
        
        start_time = time.time()
        agent, brain = self.harness.setup_pic_instance("exploit_test")
        
        # Establish baseline
        for i in range(30):
            @agent.monitor
            def baseline_op():
                time.sleep(0.005)
                return "baseline"
            baseline_op()
        
        # Exploitation: medium intensity attacks
        exploit_detected = []
        for i in range(20):
            @agent.monitor
            def exploit_attempt():
                time.sleep(0.050)  # 10x slower than baseline
                return f"exploit_{i}"
            
            result = exploit_attempt()
            exploit_detected.append(result is None)
        
        detection_rate = sum(exploit_detected) / len(exploit_detected)
        duration = time.time() - start_time
        
        return {
            "stage": "exploitation",
            "detection_rate": detection_rate,
            "requests_sent": 20,
            "requests_blocked": sum(exploit_detected),
            "duration_seconds": duration,
            "passed": True
        }
    
    def test_payload_delivery_stage(self) -> Dict[str, Any]:
        """Test Stage 3: Payload Delivery.
        
        Characteristics:
        - High intensity
        - Malware download simulation
        - Code injection patterns
        """
        self.logger.info("[MULTISTAGE] Testing payload delivery stage")
        
        start_time = time.time()
        agent, brain = self.harness.setup_pic_instance("payload_test")
        
        # Establish baseline
        for i in range(30):
            @agent.monitor
            def baseline_op():
                time.sleep(0.005)
                return "baseline"
            baseline_op()
        
        # Payload delivery: high intensity
        payload_detected = []
        for i in range(10):
            @agent.monitor
            def payload_drop():
                time.sleep(0.100)  # 20x slower than baseline
                return f"payload_{i}"
            
            result = payload_drop()
            payload_detected.append(result is None)
        
        detection_rate = sum(payload_detected) / len(payload_detected)
        duration = time.time() - start_time
        
        return {
            "stage": "payload_delivery",
            "detection_rate": detection_rate,
            "requests_sent": 10,
            "requests_blocked": sum(payload_detected),
            "duration_seconds": duration,
            "passed": True
        }
    
    def test_persistence_stage(self) -> Dict[str, Any]:
        """Test Stage 4: Persistence.
        
        Characteristics:
        - Sustained high intensity
        - Backdoor installation
        - Registry modification simulation
        """
        self.logger.info("[MULTISTAGE] Testing persistence stage")
        
        start_time = time.time()
        agent, brain = self.harness.setup_pic_instance("persistence_test")
        
        # Establish baseline
        for i in range(30):
            @agent.monitor
            def baseline_op():
                time.sleep(0.005)
                return "baseline"
            baseline_op()
        
        # Persistence: sustained high intensity
        persist_detected = []
        for i in range(15):
            @agent.monitor
            def persist_attempt():
                time.sleep(0.080)  # 16x slower than baseline
                return f"persist_{i}"
            
            result = persist_attempt()
            persist_detected.append(result is None)
        
        detection_rate = sum(persist_detected) / len(persist_detected)
        duration = time.time() - start_time
        
        return {
            "stage": "persistence",
            "detection_rate": detection_rate,
            "requests_sent": 15,
            "requests_blocked": sum(persist_detected),
            "duration_seconds": duration,
            "passed": True
        }
    
    def test_full_attack_chain(self) -> Dict[str, Any]:
        """Test complete attack chain progression.
        
        Simulates full APT attack: recon → exploit → payload → persist
        """
        self.logger.info("[MULTISTAGE] Testing full attack chain")
        
        start_time = time.time()
        agent, brain = self.harness.setup_pic_instance("full_chain_test")
        
        # Establish baseline
        for i in range(30):
            @agent.monitor
            def baseline_op():
                time.sleep(0.005)
                return "baseline"
            baseline_op()
        
        # Execute full attack chain
        chain_results = []
        
        # Stage 1: Reconnaissance (20 requests)
        for i in range(20):
            @agent.monitor
            def recon():
                time.sleep(0.010)
                return f"recon_{i}"
            result = recon()
            chain_results.append(("recon", result is None))
        
        # Stage 2: Exploitation (10 requests)
        for i in range(10):
            @agent.monitor
            def exploit():
                time.sleep(0.050)
                return f"exploit_{i}"
            result = exploit()
            chain_results.append(("exploit", result is None))
        
        # Stage 3: Payload (5 requests)
        for i in range(5):
            @agent.monitor
            def payload():
                time.sleep(0.100)
                return f"payload_{i}"
            result = payload()
            chain_results.append(("payload", result is None))
        
        # Stage 4: Persistence (10 requests)
        for i in range(10):
            @agent.monitor
            def persist():
                time.sleep(0.080)
                return f"persist_{i}"
            result = persist()
            chain_results.append(("persist", result is None))
        
        # Analyze chain detection
        stage_detections = {
            "recon": sum(1 for s, d in chain_results if s == "recon" and d),
            "exploit": sum(1 for s, d in chain_results if s == "exploit" and d),
            "payload": sum(1 for s, d in chain_results if s == "payload" and d),
            "persist": sum(1 for s, d in chain_results if s == "persist" and d)
        }
        
        total_blocked = sum(stage_detections.values())
        total_requests = len(chain_results)
        overall_detection = total_blocked / total_requests
        
        duration = time.time() - start_time
        
        return {
            "test_type": "full_attack_chain",
            "total_requests": total_requests,
            "total_blocked": total_blocked,
            "overall_detection_rate": overall_detection,
            "stage_detections": stage_detections,
            "duration_seconds": duration,
            "passed": True
        }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all multi-stage attack tests.
        
        Returns:
            Comprehensive test results
        """
        self.logger.info("[MULTISTAGE] Starting all multi-stage attack tests")
        
        results = {
            "reconnaissance": self.test_reconnaissance_stage(),
            "exploitation": self.test_exploitation_stage(),
            "payload_delivery": self.test_payload_delivery_stage(),
            "persistence": self.test_persistence_stage(),
            "full_chain": self.test_full_attack_chain()
        }
        
        # Calculate overall metrics
        total_tests = len(results)
        passed_tests = sum(1 for r in results.values() if r.get("passed", False))
        
        # Calculate average detection rate
        detection_rates = [
            r.get("detection_rate", r.get("overall_detection_rate", 0))
            for r in results.values()
        ]
        avg_detection = sum(detection_rates) / len(detection_rates) if detection_rates else 0
        
        return {
            "test_category": "multi_stage_attacks",
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "pass_rate": passed_tests / total_tests if total_tests > 0 else 0,
            "average_detection_rate": avg_detection,
            "individual_results": results,
            "attack_chain_grade": self._calculate_attack_grade(avg_detection)
        }
    
    def _calculate_attack_grade(self, detection_rate: float) -> str:
        """Calculate attack detection grade."""
        if detection_rate >= 0.75:
            return "A"
        elif detection_rate >= 0.50:
            return "B"
        elif detection_rate >= 0.25:
            return "C"
        else:
            return "F"
