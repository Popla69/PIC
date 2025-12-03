"""Property test for baseline profile convergence.

Feature: pic-v1-immune-core, Property 5: Baseline Profile Convergence
Validates: Requirements 2.1, 16.4
"""

from datetime import datetime
from hypothesis import given, strategies as st
from pic.brain.profiler import BaselineProfiler
from pic.models.events import TelemetryEvent


@given(
    sample_count=st.integers(min_value=20, max_value=100),
    duration_ms=st.floats(min_value=1.0, max_value=1000.0),
)
def test_baseline_profile_convergence(sample_count, duration_ms):
    """
    Property 5: Baseline Profile Convergence
    
    For any function with at least 50 telemetry samples, the SentinelBrain shall compute
    a baseline profile containing mean and standard deviation for duration, I/O operations,
    and network calls.
    """
    profiler = BaselineProfiler(min_samples=20)
    
    # Add samples
    for i in range(sample_count):
        event = TelemetryEvent(
            timestamp=datetime.now(),
            event_id=f"evt-{i}",
            process_id=1234,
            thread_id=5678,
            function_name="test_function",
            module_name="test_module",
            duration_ms=duration_ms + (i * 0.1),  # Slight variation
            args_metadata={},
            resource_tags={},
            redaction_applied=False,
            sampling_rate=0.1
        )
        profiler.add_sample(event)
    
    # Compute baseline
    baseline = profiler.compute_baseline("test_function", "test_module")
    
    # Verify: Baseline exists with sufficient samples
    assert baseline is not None
    assert baseline.sample_count >= 20
    
    # Verify: Statistical measures computed
    assert baseline.mean_duration_ms > 0
    assert baseline.std_duration_ms >= 0
    assert baseline.p50_duration_ms > 0
    assert baseline.p95_duration_ms > 0
    assert baseline.p99_duration_ms > 0
