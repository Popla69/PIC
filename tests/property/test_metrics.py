"""Property tests for performance metrics.

Feature: pic-v1-immune-core
Property 48: FPR Calculation Correctness - Validates: Requirements 16.1
Property 49: TPR Calculation Correctness - Validates: Requirements 16.2
"""

from hypothesis import given, strategies as st
from pic.testing.metrics import PerformanceMetrics


@given(
    flagged=st.integers(min_value=0, max_value=1000),
    total_benign=st.integers(min_value=1, max_value=1000),
)
def test_fpr_calculation_correctness(flagged, total_benign):
    """
    Property 48: FPR Calculation Correctness
    
    For any set of benign events and flagged events, the false positive rate
    shall be calculated as flagged / total_benign and be in range [0, 1].
    """
    # Ensure flagged <= total_benign
    flagged = min(flagged, total_benign)
    
    # Calculate FPR
    fpr = PerformanceMetrics.calculate_fpr(flagged, total_benign)
    
    # Verify: FPR is in valid range
    assert 0.0 <= fpr <= 1.0, f"FPR {fpr} not in range [0, 1]"
    
    # Verify: FPR calculation is correct
    expected_fpr = flagged / total_benign
    assert abs(fpr - expected_fpr) < 1e-10, f"FPR {fpr} != expected {expected_fpr}"
    
    # Verify: Edge cases
    if flagged == 0:
        assert fpr == 0.0
    if flagged == total_benign:
        assert fpr == 1.0


@given(
    detected=st.integers(min_value=0, max_value=1000),
    total_malicious=st.integers(min_value=1, max_value=1000),
)
def test_tpr_calculation_correctness(detected, total_malicious):
    """
    Property 49: TPR Calculation Correctness
    
    For any set of malicious events and detected events, the true positive rate
    shall be calculated as detected / total_malicious and be in range [0, 1].
    """
    # Ensure detected <= total_malicious
    detected = min(detected, total_malicious)
    
    # Calculate TPR
    tpr = PerformanceMetrics.calculate_tpr(detected, total_malicious)
    
    # Verify: TPR is in valid range
    assert 0.0 <= tpr <= 1.0, f"TPR {tpr} not in range [0, 1]"
    
    # Verify: TPR calculation is correct
    expected_tpr = detected / total_malicious
    assert abs(tpr - expected_tpr) < 1e-10, f"TPR {tpr} != expected {expected_tpr}"
    
    # Verify: Edge cases
    if detected == 0:
        assert tpr == 0.0
    if detected == total_malicious:
        assert tpr == 1.0


def test_fpr_zero_benign():
    """Test FPR with zero benign events."""
    fpr = PerformanceMetrics.calculate_fpr(0, 0)
    assert fpr == 0.0


def test_tpr_zero_malicious():
    """Test TPR with zero malicious events."""
    tpr = PerformanceMetrics.calculate_tpr(0, 0)
    assert tpr == 0.0


def test_latency_percentiles():
    """Test latency percentile calculations."""
    latencies = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]
    percentiles = PerformanceMetrics.calculate_latency_percentiles(latencies)
    
    assert "p50" in percentiles
    assert "p95" in percentiles
    assert "p99" in percentiles
    
    # P50 should be around median
    assert 40.0 <= percentiles["p50"] <= 60.0
    # P95 should be high
    assert percentiles["p95"] >= 80.0
    # P99 should be very high
    assert percentiles["p99"] >= 90.0


def test_overhead_calculation():
    """Test overhead calculation."""
    baseline = [10.0, 10.0, 10.0]
    instrumented = [11.0, 11.0, 11.0]
    
    overhead = PerformanceMetrics.calculate_overhead(instrumented, baseline)
    
    # 10% overhead expected
    assert abs(overhead - 10.0) < 1.0
