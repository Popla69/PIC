"""Main Real-World Test Suite Runner

Orchestrates execution of all real-world testing categories.
"""

import logging
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from .harness import TestHarness
from .safety import SafetyController, NetworkPolicy, ResourceLimits, CleanupPolicy
from .sandbox import SandboxManager
from .reporting import ReportGenerator, TestResult, PerformanceMetrics
from .testers import (
    LatencyAnomalyTester,
    RuntimeAttackTester,
    StressAbuseTester,
    MalwarePatternTester,
    WebServiceTester,
    MicroserviceTester,
    VulnerableAppTester
)
from .testers.enterprise import EnterpriseSecurityTester
from .testers.highvolume import HighVolumeTester
from .testers.multistage import MultiStageAttackTester
from .testers.aptstealth import APTStealthTester
from .testers.memoryconsistency import MemoryConsistencyTester


@dataclass
class TestSuiteConfig:
    """Configuration for test suite execution."""
    test_root: Path = Path("test_data/realworld")
    output_dir: Path = Path("test_results/realworld")
    enable_latency_tests: bool = True
    enable_runtime_tests: bool = True
    enable_stress_tests: bool = True
    enable_malware_tests: bool = True
    enable_webservice_tests: bool = True
    enable_microservice_tests: bool = True
    enable_vulnerable_app_tests: bool = True
    enable_enterprise_tests: bool = True
    enable_highvolume_tests: bool = True
    enable_multistage_tests: bool = True
    enable_aptstealth_tests: bool = True
    enable_memoryconsistency_tests: bool = True
    parallel_execution: bool = False
    max_workers: int = 4
    cleanup_after_tests: bool = True


class RealWorldTestSuite:
    """Main test suite for real-world PIC validation.
    
    Orchestrates execution of all test categories:
    - Latency anomaly detection
    - Runtime attack detection
    - Stress and abuse resistance
    - Malicious pattern recognition
    - Web service integration
    - Microservice attack simulation
    - Vulnerable application testing
    """
    
    def __init__(self, config: Optional[TestSuiteConfig] = None):
        """Initialize test suite.
        
        Args:
            config: Test suite configuration
        """
        self.config = config or TestSuiteConfig()
        self.logger = logging.getLogger(__name__)
        
        # Create directories
        self.config.test_root.mkdir(parents=True, exist_ok=True)
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.safety = SafetyController(
            test_root=self.config.test_root,
            network_policy=NetworkPolicy(),
            resource_limits=ResourceLimits(),
            cleanup_policy=CleanupPolicy()
        )
        
        self.sandbox = SandboxManager(
            base_path=self.config.test_root,
            safety_controller=self.safety
        )
        
        self.harness = TestHarness(
            test_root=str(self.config.test_root),
            sampling_rate=1.0
        )
        
        self.reporter = ReportGenerator(output_dir=self.config.output_dir)
        
        # Initialize testers
        self.testers = self._initialize_testers()
        
        self.logger.info("RealWorldTestSuite initialized")
    
    def _initialize_testers(self) -> Dict[str, Any]:
        """Initialize all test category modules.
        
        Returns:
            Dictionary of tester instances
        """
        testers = {}
        
        if self.config.enable_latency_tests:
            testers["latency"] = LatencyAnomalyTester(
                harness=self.harness
            )
        
        if self.config.enable_runtime_tests:
            testers["runtime"] = RuntimeAttackTester(
                harness=self.harness
            )
        
        if self.config.enable_stress_tests:
            # StressAbuseTester needs agent and safety
            agent, _ = self.harness.setup_pic_instance("stress_test")
            testers["stress"] = StressAbuseTester(
                agent=agent,
                safety=self.safety
            )
        
        if self.config.enable_malware_tests:
            # MalwarePatternTester needs agent and safety
            agent, _ = self.harness.setup_pic_instance("malware_test")
            testers["malware"] = MalwarePatternTester(
                agent=agent,
                safety=self.safety
            )
        
        if self.config.enable_webservice_tests:
            # WebServiceTester needs agent and safety
            agent, _ = self.harness.setup_pic_instance("webservice_test")
            testers["webservice"] = WebServiceTester(
                agent=agent,
                safety=self.safety
            )
        
        if self.config.enable_microservice_tests:
            # MicroserviceTester needs agent and safety
            agent, _ = self.harness.setup_pic_instance("microservice_test")
            testers["microservice"] = MicroserviceTester(
                agent=agent,
                safety=self.safety
            )
        
        if self.config.enable_vulnerable_app_tests:
            # VulnerableAppTester needs agent and safety
            agent, _ = self.harness.setup_pic_instance("vulnerable_test")
            testers["vulnerable_app"] = VulnerableAppTester(
                agent=agent,
                safety=self.safety
            )
        
        if self.config.enable_enterprise_tests:
            # EnterpriseSecurityTester needs harness
            testers["enterprise"] = EnterpriseSecurityTester(
                harness=self.harness
            )
        
        if self.config.enable_highvolume_tests:
            # HighVolumeTester needs harness
            testers["highvolume"] = HighVolumeTester(
                harness=self.harness
            )
        
        if self.config.enable_multistage_tests:
            # MultiStageAttackTester needs harness
            testers["multistage"] = MultiStageAttackTester(
                harness=self.harness
            )
        
        if self.config.enable_aptstealth_tests:
            # APTStealthTester needs harness
            testers["aptstealth"] = APTStealthTester(
                harness=self.harness
            )
        
        if self.config.enable_memoryconsistency_tests:
            # MemoryConsistencyTester needs harness
            testers["memoryconsistency"] = MemoryConsistencyTester(
                harness=self.harness
            )
        
        return testers
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all enabled test categories.
        
        Returns:
            Complete test report
        """
        self.logger.info("🚀 Starting Real-World Test Suite")
        self.logger.info(f"Enabled categories: {list(self.testers.keys())}")
        
        # Start monitoring
        self.reporter.start_monitoring()
        
        # Track overall metrics
        start_time = time.time()
        all_results: List[TestResult] = []
        total_events_processed = 0
        
        # Run each test category
        for category_name, tester in self.testers.items():
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"Running {category_name} tests...")
            self.logger.info(f"{'='*60}")
            
            try:
                # Run tests for this category
                category_results = tester.run_tests()
                all_results.extend(category_results)
                
                # Update monitoring
                for result in category_results:
                    self.reporter.update_test_status(
                        result.test_id,
                        result.status,
                        f"({result.duration_seconds:.2f}s)"
                    )
                
                # Track events
                for result in category_results:
                    if result.forensic_data and "events_processed" in result.forensic_data:
                        total_events_processed += result.forensic_data["events_processed"]
                
                self.logger.info(f"✅ {category_name} tests completed: {len(category_results)} tests")
                
            except Exception as e:
                self.logger.error(f"❌ {category_name} tests failed: {e}")
                
                # Create failure result
                failure_result = TestResult(
                    test_id=f"{category_name}_suite",
                    category=category_name,
                    status="failed",
                    duration_seconds=0,
                    error_message=str(e)
                )
                all_results.append(failure_result)
                
                self.reporter.update_test_status(
                    failure_result.test_id,
                    "failed",
                    str(e)
                )
        
        # Calculate overall metrics
        end_time = time.time()
        total_duration = end_time - start_time
        
        performance_metrics = PerformanceMetrics(
            throughput_events_per_second=total_events_processed / total_duration if total_duration > 0 else 0,
            memory_usage_mb=0,  # Would need psutil to measure accurately
            cpu_usage_percent=0,  # Would need psutil to measure accurately
            response_time_ms=total_duration * 1000 / len(all_results) if all_results else 0,
            total_events_processed=total_events_processed
        )
        
        # Get safety logs
        safety_logs = [
            {"level": "VIOLATION", "message": v, "check_type": "unknown"}
            for v in self.safety.get_violations()
        ]
        
        # Generate comprehensive report
        report = self.reporter.generate_report(
            test_results=all_results,
            performance_metrics=performance_metrics,
            safety_logs=safety_logs
        )
        
        # Cleanup if configured
        if self.config.cleanup_after_tests:
            self.logger.info("\n🧹 Cleaning up test artifacts...")
            self.safety.cleanup_test_artifacts()
        
        # Print summary
        self._print_summary(report)
        
        return report
    
    def run_category(self, category_name: str) -> List[TestResult]:
        """Run tests for a specific category.
        
        Args:
            category_name: Name of test category
            
        Returns:
            List of test results
        """
        if category_name not in self.testers:
            raise ValueError(f"Unknown test category: {category_name}")
        
        self.logger.info(f"Running {category_name} tests...")
        
        tester = self.testers[category_name]
        results = tester.run_all_tests()
        
        self.logger.info(f"Completed {category_name}: {len(results)} tests")
        
        return results
    
    def list_categories(self) -> List[str]:
        """List all available test categories.
        
        Returns:
            List of category names
        """
        return list(self.testers.keys())
    
    def _print_summary(self, report: Dict[str, Any]):
        """Print test execution summary.
        
        Args:
            report: Test report
        """
        summary = report["summary"]
        
        self.logger.info("\n" + "="*60)
        self.logger.info("REAL-WORLD TEST SUITE SUMMARY")
        self.logger.info("="*60)
        self.logger.info(f"Total Tests: {summary['total_tests']}")
        self.logger.info(f"Passed: {summary['passed']} ✅")
        self.logger.info(f"Failed: {summary['failed']} ❌")
        self.logger.info(f"Skipped: {summary['skipped']} ⏭️")
        self.logger.info(f"Pass Rate: {summary['pass_rate']:.1%}")
        self.logger.info(f"Duration: {summary['duration_seconds']:.2f}s")
        
        # Compliance status
        compliance = report["compliance"]
        self.logger.info(f"\nCompliance: {compliance['overall_status']}")
        
        if compliance["violations"]:
            self.logger.warning(f"⚠️  Safety Violations: {len(compliance['violations'])}")
        
        # Performance
        if report["performance_metrics"]:
            perf = report["performance_metrics"]
            self.logger.info(f"\nPerformance:")
            self.logger.info(f"  Throughput: {perf['throughput_events_per_second']:.2f} events/sec")
            self.logger.info(f"  Total Events: {perf['total_events_processed']}")
        
        self.logger.info("\n" + "="*60)
        self.logger.info(f"📊 Full report: {self.config.output_dir}")
        self.logger.info("="*60)
