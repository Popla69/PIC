"""High-Volume Data Stream Testing

Real-world high-volume performance validation.
Tests PIC under sustained load conditions.
"""

import time
import logging
import threading
from pathlib import Path
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics

from pic.cellagent import CellAgent
from pic.realworld.safety import SafetyController
from pic.realworld.harness import TestHarness


class HighVolumeTester:
    """High-volume data stream testing.
    
    Tests PIC performance under sustained load.
    """
    
    def __init__(self, harness: TestHarness):
        """Initialize high-volume tester.
        
        Args:
            harness: TestHarness for PIC setup
        """
        self.harness = harness
        self.logger = logging.getLogger(__name__)
        self.results = []
    
    def test_sustained_load(self) -> Dict[str, Any]:
        """Test 1: Sustained high-volume load.
        
        Tests PIC under continuous high request rate.
        """
        self.logger.info("[HIGH-VOLUME] Starting sustained load test")
        
        start_time = time.time()
        
        # Setup PIC instance
        agent, brain = self.harness.setup_pic_instance("sustained_load_test")
        
        # Test parameters
        duration_seconds = 30
        target_rps = 100  # requests per second
        total_requests = duration_seconds * target_rps
        
        # Track metrics
        request_times = []
        successful_requests = 0
        failed_requests = 0
        
        # Run sustained load
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            
            for i in range(total_requests):
                future = executor.submit(self._send_request, agent, i)
                futures.append(future)
                
                # Rate limiting to achieve target RPS
                if (i + 1) % target_rps == 0:
                    time.sleep(1.0)
            
            # Collect results
            for future in as_completed(futures):
                try:
                    req_time, success = future.result()
                    request_times.append(req_time)
                    if success:
                        successful_requests += 1
                    else:
                        failed_requests += 1
                except Exception as e:
                    self.logger.error(f"Request failed: {e}")
                    failed_requests += 1
        
        duration = time.time() - start_time
        
        # Calculate metrics
        avg_latency = statistics.mean(request_times) if request_times else 0
        p50_latency = statistics.median(request_times) if request_times else 0
        p95_latency = statistics.quantiles(request_times, n=20)[18] if len(request_times) > 20 else 0
        p99_latency = statistics.quantiles(request_times, n=100)[98] if len(request_times) > 100 else 0
        actual_rps = total_requests / duration
        success_rate = (successful_requests / total_requests) * 100 if total_requests > 0 else 0
        
        return {
            "test_name": "sustained_load",
            "duration_seconds": duration,
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "success_rate_percent": success_rate,
            "target_rps": target_rps,
            "actual_rps": actual_rps,
            "avg_latency_ms": avg_latency * 1000,
            "p50_latency_ms": p50_latency * 1000,
            "p95_latency_ms": p95_latency * 1000,
            "p99_latency_ms": p99_latency * 1000,
            "passed": success_rate >= 95.0 and p99_latency < 1.0
        }
    
    def test_burst_traffic(self) -> Dict[str, Any]:
        """Test burst traffic patterns.
        
        Tests PIC handling of sudden traffic spikes.
        """
        self.logger.info("[HIGH-VOLUME] Starting burst traffic test")
        
        start_time = time.time()
        
        # Setup PIC instance
        agent, brain = self.harness.setup_pic_instance("burst_traffic_test")
        
        # Test parameters
        burst_size = 500
        burst_count = 5
        
        burst_results = []
        
        for burst_num in range(burst_count):
            self.logger.info(f"[HIGH-VOLUME] Burst {burst_num + 1}/{burst_count}")
            
            burst_start = time.time()
            request_times = []
            successful = 0
            
            # Send burst
            with ThreadPoolExecutor(max_workers=50) as executor:
                futures = [
                    executor.submit(self._send_request, agent, i)
                    for i in range(burst_size)
                ]
                
                for future in as_completed(futures):
                    try:
                        req_time, success = future.result()
                        request_times.append(req_time)
                        if success:
                            successful += 1
                    except Exception as e:
                        self.logger.error(f"Burst request failed: {e}")
            
            burst_duration = time.time() - burst_start
            burst_rps = burst_size / burst_duration
            
            burst_results.append({
                "burst_number": burst_num + 1,
                "requests": burst_size,
                "successful": successful,
                "duration_seconds": burst_duration,
                "rps": burst_rps,
                "avg_latency_ms": statistics.mean(request_times) * 1000 if request_times else 0
            })
            
            # Cool down between bursts
            time.sleep(2.0)
        
        duration = time.time() - start_time
        
        # Calculate overall metrics
        total_requests = burst_size * burst_count
        total_successful = sum(b["successful"] for b in burst_results)
        success_rate = (total_successful / total_requests) * 100
        avg_burst_rps = statistics.mean([b["rps"] for b in burst_results])
        
        return {
            "test_name": "burst_traffic",
            "duration_seconds": duration,
            "burst_count": burst_count,
            "burst_size": burst_size,
            "total_requests": total_requests,
            "total_successful": total_successful,
            "success_rate_percent": success_rate,
            "avg_burst_rps": avg_burst_rps,
            "burst_results": burst_results,
            "passed": success_rate >= 90.0
        }
    
    def test_concurrent_streams(self) -> Dict[str, Any]:
        """Test multiple concurrent data streams.
        
        Tests PIC handling multiple independent streams.
        """
        self.logger.info("[HIGH-VOLUME] Starting concurrent streams test")
        
        start_time = time.time()
        
        # Setup PIC instance
        agent, brain = self.harness.setup_pic_instance("concurrent_streams_test")
        
        # Test parameters
        stream_count = 10
        requests_per_stream = 100
        
        stream_results = []
        
        def run_stream(stream_id: int) -> Dict[str, Any]:
            """Run a single data stream."""
            stream_start = time.time()
            request_times = []
            successful = 0
            
            for i in range(requests_per_stream):
                req_time, success = self._send_request(agent, f"stream_{stream_id}_req_{i}")
                request_times.append(req_time)
                if success:
                    successful += 1
                time.sleep(0.01)  # Small delay between requests
            
            stream_duration = time.time() - stream_start
            
            return {
                "stream_id": stream_id,
                "requests": requests_per_stream,
                "successful": successful,
                "duration_seconds": stream_duration,
                "avg_latency_ms": statistics.mean(request_times) * 1000 if request_times else 0
            }
        
        # Run streams concurrently
        with ThreadPoolExecutor(max_workers=stream_count) as executor:
            futures = [
                executor.submit(run_stream, stream_id)
                for stream_id in range(stream_count)
            ]
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    stream_results.append(result)
                except Exception as e:
                    self.logger.error(f"Stream failed: {e}")
        
        duration = time.time() - start_time
        
        # Calculate overall metrics
        total_requests = stream_count * requests_per_stream
        total_successful = sum(s["successful"] for s in stream_results)
        success_rate = (total_successful / total_requests) * 100
        avg_stream_latency = statistics.mean([s["avg_latency_ms"] for s in stream_results])
        
        return {
            "test_name": "concurrent_streams",
            "duration_seconds": duration,
            "stream_count": stream_count,
            "requests_per_stream": requests_per_stream,
            "total_requests": total_requests,
            "total_successful": total_successful,
            "success_rate_percent": success_rate,
            "avg_stream_latency_ms": avg_stream_latency,
            "stream_results": stream_results,
            "passed": success_rate >= 95.0
        }
    
    def _send_request(self, agent: CellAgent, request_id: Any) -> tuple:
        """Send a single request and measure time.
        
        Returns:
            Tuple of (request_time, success)
        """
        start = time.time()
        try:
            @agent.monitor
            def test_request():
                # Simulate some work
                time.sleep(0.001)
                return f"response_{request_id}"
            
            result = test_request()
            duration = time.time() - start
            return (duration, result is not None)
        except Exception as e:
            duration = time.time() - start
            return (duration, False)
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all high-volume tests.
        
        Returns:
            Comprehensive test results
        """
        self.logger.info("[HIGH-VOLUME] Starting all high-volume tests")
        
        results = {
            "sustained_load": self.test_sustained_load(),
            "burst_traffic": self.test_burst_traffic(),
            "concurrent_streams": self.test_concurrent_streams()
        }
        
        # Calculate overall metrics
        total_tests = len(results)
        passed_tests = sum(1 for r in results.values() if r.get("passed", False))
        
        return {
            "test_category": "high_volume",
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "pass_rate": passed_tests / total_tests if total_tests > 0 else 0,
            "individual_results": results,
            "performance_grade": self._calculate_performance_grade(results)
        }
    
    def _calculate_performance_grade(self, results: Dict[str, Any]) -> str:
        """Calculate overall performance grade."""
        passed = sum(1 for r in results.values() if r.get("passed", False))
        total = len(results)
        
        if passed == total:
            return "A"
        elif passed >= total * 0.66:
            return "B"
        elif passed >= total * 0.33:
            return "C"
        else:
            return "F"
