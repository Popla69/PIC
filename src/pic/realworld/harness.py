"""Test Harness for Real-World Testing

Central orchestration component for executing real-world test scenarios.
"""

import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging

from pic.realworld.safety import SafetyController
from pic.realworld.sandbox import SandboxManager
from pic.cellagent import CellAgent
from pic.brain.core import BrainCore
from pic.storage.state_store import StateStore
from pic.storage.audit_store import AuditStore
from pic.storage.trace_store import TraceStore
from pic.crypto import CryptoCore


class TestStatus(Enum):
    """Test execution status."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TestResult:
    """Result of a test execution."""
    test_name: str
    status: TestStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    detections: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    anomaly_scores: List[float] = field(default_factory=list)
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def mark_complete(self, status: TestStatus, error: Optional[str] = None):
        """Mark test as complete."""
        self.end_time = datetime.now()
        self.duration_seconds = (self.end_time - self.start_time).total_seconds()
        self.status = status
        if error:
            self.error_message = error


class TestHarness:
    """Central orchestration for real-world testing.
    
    Manages test execution lifecycle, coordinates between test modules
    and PIC instances, and provides unified logging and monitoring.
    """
    
    def __init__(
        self,
        test_root: Optional[str] = None,
        sampling_rate: float = 1.0
    ):
        """Initialize test harness.
        
        Args:
            test_root: Root directory for test artifacts
            sampling_rate: PIC sampling rate (1.0 = 100%)
        """
        self.logger = logging.getLogger(__name__)
        
        # Initialize safety and sandbox
        self.safety_controller = SafetyController(test_root or "test_realworld")
        self.sandbox_manager = SandboxManager(
            base_path=self.safety_controller.test_root,
            safety_controller=self.safety_controller
        )
        
        # Initialize PIC components
        crypto_key_path = self.safety_controller.test_root / ".crypto" / "signing.key"
        self.crypto = CryptoCore(str(crypto_key_path))
        self.sampling_rate = sampling_rate
        
        # Test tracking
        self.test_results: List[TestResult] = []
        self.current_test: Optional[TestResult] = None
        
        self.logger.info("TestHarness initialized")
    
    def setup_pic_instance(self, sandbox_name: str) -> tuple[CellAgent, BrainCore]:
        """Set up a PIC instance for testing in a sandbox.
        
        Args:
            sandbox_name: Name of sandbox to use
            
        Returns:
            Tuple of (CellAgent, BrainCore) instances
        """
        sandbox_path = self.sandbox_manager.get_sandbox(sandbox_name)
        if not sandbox_path:
            sandbox_path = self.sandbox_manager.create_sandbox(sandbox_name)
        
        # Initialize storage in sandbox
        state_db = sandbox_path / "data" / "state.db"
        audit_log = sandbox_path / "logs" / "audit.log"
        
        state_store = StateStore(str(state_db))
        audit_store = AuditStore(str(audit_log), self.crypto)
        trace_store = TraceStore(capacity_per_function=1000)
        
        # Initialize brain
        brain = BrainCore(
            state_store=state_store,
            audit_store=audit_store,
            trace_store=trace_store,
            crypto_core=self.crypto
        )
        
        # Initialize agent with config
        from pic.config import PICConfig
        config = PICConfig.load()
        agent = CellAgent(config=config)
        
        self.logger.info(f"PIC instance set up in sandbox: {sandbox_name}")
        
        return agent, brain
    
    def start_test(self, test_name: str, metadata: Optional[Dict[str, Any]] = None) -> TestResult:
        """Start a new test.
        
        Args:
            test_name: Name of the test
            metadata: Optional test metadata
            
        Returns:
            TestResult object for tracking
        """
        result = TestResult(
            test_name=test_name,
            status=TestStatus.RUNNING,
            start_time=datetime.now(),
            metadata=metadata or {}
        )
        
        self.current_test = result
        self.test_results.append(result)
        
        self.logger.info(f"Started test: {test_name}")
        
        return result
    
    def complete_test(
        self,
        result: TestResult,
        status: TestStatus,
        error: Optional[str] = None
    ) -> None:
        """Complete a test.
        
        Args:
            result: TestResult to complete
            status: Final test status
            error: Optional error message
        """
        result.mark_complete(status, error)
        
        if self.current_test == result:
            self.current_test = None
        
        # Use ASCII for Windows console compatibility
        status_symbol = "[PASS]" if status == TestStatus.PASSED else "[FAIL]" if status == TestStatus.FAILED else "[SKIP]"
        self.logger.info(
            f"{status_symbol} Test {result.test_name}: {status.value} "
            f"({result.duration_seconds:.2f}s)"
        )
        
        if error:
            self.logger.error(f"Test error: {error}")
    
    def record_detection(
        self,
        result: TestResult,
        anomaly_score: float,
        is_true_positive: bool = True
    ) -> None:
        """Record a detection event.
        
        Args:
            result: TestResult to update
            anomaly_score: Anomaly score from PIC
            is_true_positive: Whether detection was correct
        """
        result.anomaly_scores.append(anomaly_score)
        
        if is_true_positive:
            result.detections += 1
        else:
            result.false_positives += 1
    
    def record_miss(self, result: TestResult) -> None:
        """Record a missed detection (false negative).
        
        Args:
            result: TestResult to update
        """
        result.false_negatives += 1
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics for all tests.
        
        Returns:
            Dictionary with summary stats
        """
        if not self.test_results:
            return {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "total_duration": 0.0
            }
        
        passed = sum(1 for r in self.test_results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in self.test_results if r.status == TestStatus.FAILED)
        skipped = sum(1 for r in self.test_results if r.status == TestStatus.SKIPPED)
        
        total_duration = sum(r.duration_seconds for r in self.test_results)
        total_detections = sum(r.detections for r in self.test_results)
        total_false_positives = sum(r.false_positives for r in self.test_results)
        total_false_negatives = sum(r.false_negatives for r in self.test_results)
        
        # Calculate detection rate
        total_attacks = total_detections + total_false_negatives
        detection_rate = total_detections / total_attacks if total_attacks > 0 else 0.0
        
        # Calculate false positive rate
        total_normal = total_false_positives + (len(self.test_results) * 10)  # Estimate
        fpr = total_false_positives / total_normal if total_normal > 0 else 0.0
        
        return {
            "total_tests": len(self.test_results),
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "total_duration": total_duration,
            "total_detections": total_detections,
            "total_false_positives": total_false_positives,
            "total_false_negatives": total_false_negatives,
            "detection_rate": detection_rate,
            "false_positive_rate": fpr,
            "safety_violations": len(self.safety_controller.get_violations())
        }
    
    def cleanup(self) -> None:
        """Clean up all test resources."""
        self.logger.info("Cleaning up test harness...")
        
        # Cleanup sandboxes
        self.sandbox_manager.cleanup_all_sandboxes()
        
        # Cleanup safety controller
        self.safety_controller.cleanup_test_artifacts()
        
        self.logger.info("Test harness cleanup complete")
