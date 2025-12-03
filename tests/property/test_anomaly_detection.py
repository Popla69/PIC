"""Property tests for anomaly detection.

Feature: pic-v1-immune-core
Property 6: Anomaly Score Monotonicity - Validates: Requirements 2.2
Property 7: Candidate Generation Threshold - Validates: Requirements 2.3
"""

from datetime import datetime
from hypothesis import given, strategies as st, settings, HealthCheck
from pic.brain.detector import AnomalyDetector
from pic.models.baseline import BaselineProfile
from pic.models.events import TelemetryEvent


@settings(suppress_health_check=[HealthCheck.too_slow])
@given(
    baseline_mean=st.floats(min_value=10.0, max_value=100.0),
    baseline_std=st.floats(min_value=1.0, max_value=20.0),
    duration1=st.floats(min_value=10.0, max_value=200.0),
    duration2=st.floats(min_value=10.0, max_value=200.0),
)
def test_anomaly_score_monotonicity(baseline_mean, baseline_std, duration1, duration2):
    """
    Property 6: Anomaly Score Monotonicity
    
    For any two telemetry events where event A has a greater deviation from the baseline
    than event B, the anomaly score for A shall be greater than or equal to the score for B.
    """
    detector = AnomalyDetector(threshold_percentile=95.0)
    
    # Create baseline
    baseline = BaselineProfile(
        function_name="test_function",
        module_name="test_module",
        version=1,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        sample_count=100,
        mean_duration_ms=baseline_mean,
        std_duration_ms=baseline_std,
        p50_duration_ms=baseline_mean,
        p95_duration_ms=baseline_mean + (2 * baseline_std),
        p99_duration_ms=baseline_mean + (3 * baseline_std),
        historical_distances=[]
    )
    
    # Create two events
    event1 = TelemetryEvent(
        timestamp=datetime.now(),
        event_id="evt-1",
        process_id=1234,
        thread_id=5678,
        function_name="test_function",
        module_name="test_module",
        duration_ms=duration1,
        args_metadata={},
        resource_tags={},
        redaction_applied=False,
        sampling_rate=0.1
    )
    
    event2 = TelemetryEvent(
        timestamp=datetime.now(),
        event_id="evt-2",
        process_id=1234,
        thread_id=5678,
        function_name="test_function",
        module_name="test_module",
        duration_ms=duration2,
        args_metadata={},
        resource_tags={},
        redaction_applied=False,
        sampling_rate=0.1
    )
    
    # Compute scores
    score1 = detector.compute_anomaly_score(event1, baseline)
    score2 = detector.compute_anomaly_score(event2, baseline)
    
    # Verify: Greater deviation => greater or equal score
    deviation1 = abs(duration1 - baseline_mean)
    deviation2 = abs(duration2 - baseline_mean)
    
    if deviation1 > deviation2:
        assert score1 >= score2, f"Score1 ({score1}) should be >= Score2 ({score2}) when deviation1 ({deviation1}) > deviation2 ({deviation2})"
    elif deviation2 > deviation1:
        assert score2 >= score1, f"Score2 ({score2}) should be >= Score1 ({score1}) when deviation2 ({deviation2}) > deviation1 ({deviation1})"
    # If deviations are equal, scores should be equal (within floating point tolerance)


@given(
    baseline_mean=st.floats(min_value=10.0, max_value=100.0),
    baseline_std=st.floats(min_value=1.0, max_value=20.0),
    duration=st.floats(min_value=10.0, max_value=500.0),
)
def test_candidate_generation_threshold(baseline_mean, baseline_std, duration):
    """
    Property 7: Candidate Generation Threshold
    
    For any telemetry event with an anomaly score exceeding the candidate threshold (80),
    a detection candidate shall be created.
    """
    candidate_threshold = 80.0
    detector = AnomalyDetector(
        threshold_percentile=95.0,
        candidate_score_threshold=candidate_threshold
    )
    
    # Create baseline
    baseline = BaselineProfile(
        function_name="test_function",
        module_name="test_module",
        version=1,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        sample_count=100,
        mean_duration_ms=baseline_mean,
        std_duration_ms=baseline_std,
        p50_duration_ms=baseline_mean,
        p95_duration_ms=baseline_mean + (2 * baseline_std),
        p99_duration_ms=baseline_mean + (3 * baseline_std),
        historical_distances=[]
    )
    
    # Create event
    event = TelemetryEvent(
        timestamp=datetime.now(),
        event_id="evt-1",
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
    
    # Compute score
    score = detector.compute_anomaly_score(event, baseline)
    
    # Create candidate
    candidate = detector.create_candidate(event, baseline, score)
    
    # Verify: Candidate created if and only if score > threshold
    if score >= candidate_threshold:
        assert candidate is not None, f"Candidate should be created when score ({score}) >= threshold ({candidate_threshold})"
        assert candidate.anomaly_score == score
        assert candidate.function_name == event.function_name
        assert candidate.observed_value == duration
    else:
        assert candidate is None, f"Candidate should NOT be created when score ({score}) < threshold ({candidate_threshold})"
