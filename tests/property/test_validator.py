"""Property test for validator promotion eligibility.

Feature: pic-v1-immune-core, Property 11: Promotion Eligibility Rule
Validates: Requirements 3.5
"""

from datetime import datetime
from hypothesis import given, strategies as st
from pic.brain.validator import SimpleValidator
from pic.models.detector import DetectionCandidate
from pic.models.events import TelemetryEvent
from pic.storage.trace_store import TraceStore


@given(
    benign_count=st.integers(min_value=50, max_value=150),
    baseline_mean=st.floats(min_value=10.0, max_value=100.0),
    baseline_std=st.floats(min_value=1.0, max_value=20.0),
    fp_rate=st.floats(min_value=0.0, max_value=0.15),
)
def test_promotion_eligibility_rule(benign_count, baseline_mean, baseline_std, fp_rate):
    """
    Property 11: Promotion Eligibility Rule
    
    For any detection candidate, the candidate shall be eligible for promotion to a detector
    if and only if the false positive rate on recent benign events is ≤ 5%.
    """
    # Create trace store
    trace_store = TraceStore(capacity_per_function=1000)
    
    # Create validator with 5% FP threshold
    validator = SimpleValidator(trace_store, max_fp_rate=0.05)
    
    # Create benign events with durations near baseline
    for i in range(benign_count):
        # Generate duration that will produce desired FP rate
        # If fp_rate is low, keep durations close to baseline
        # If fp_rate is high, add more outliers
        if i < int(benign_count * fp_rate):
            # These will be "false positives" - far from baseline
            duration = baseline_mean + (5 * baseline_std)
        else:
            # These are normal - close to baseline
            duration = baseline_mean + (0.5 * baseline_std)
        
        event = TelemetryEvent(
            timestamp=datetime.now(),
            event_id=f"evt-{i}",
            process_id=1234,
            thread_id=5678,
            function_name="test_function",
            module_name="test_module",
            duration_ms=duration,
            args_metadata={},
            resource_tags={},
            redaction_applied=False,
            sampling_rate=0.1
        )
        trace_store.add_event(event)
    
    # Create detection candidate
    candidate = DetectionCandidate(
        function_name="test_function",
        module_name="test_module",
        anomaly_score=85.0,
        threshold_percentile=95.0,
        baseline_mean=baseline_mean,
        baseline_std=baseline_std,
        observed_value=baseline_mean + (4 * baseline_std),
        sample_count=100
    )
    
    # Validate candidate
    is_eligible = validator.is_eligible_for_promotion(candidate, validation_sample_size=benign_count)
    
    # Compute actual FP rate
    actual_fp_rate = validator.compute_fp_rate(
        trace_store.get_recent_events("test_function", module_name="test_module", count=benign_count),
        candidate
    )
    
    # Verify: Eligible if and only if FP rate ≤ 5%
    if actual_fp_rate <= 0.05:
        assert is_eligible, f"Candidate should be eligible when FP rate ({actual_fp_rate:.2%}) ≤ 5%"
    else:
        assert not is_eligible, f"Candidate should NOT be eligible when FP rate ({actual_fp_rate:.2%}) > 5%"
