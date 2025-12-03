"""Simple validator for detection candidate promotion."""

from typing import List
from pic.models.detector import DetectionCandidate
from pic.models.events import TelemetryEvent
from pic.storage.trace_store import TraceStore


class SimpleValidator:
    """Validate detection candidates before promotion to detectors.
    
    Uses false positive rate (FPR) validation against recent benign events.
    """
    
    def __init__(self, trace_store: TraceStore, max_fp_rate: float = 0.05):
        """Initialize validator.
        
        Args:
            trace_store: TraceStore for loading benign events
            max_fp_rate: Maximum acceptable false positive rate (default: 5%)
        """
        self.trace_store = trace_store
        self.max_fp_rate = max_fp_rate
    
    def validate_candidate(
        self,
        candidate: DetectionCandidate,
        validation_sample_size: int = 100
    ) -> bool:
        """Validate a detection candidate.
        
        Loads recent benign events and computes false positive rate.
        Candidate passes if FP rate ≤ max_fp_rate.
        
        Args:
            candidate: DetectionCandidate to validate
            validation_sample_size: Number of benign events to test (default: 100)
            
        Returns:
            True if candidate passes validation (FP rate ≤ threshold)
        """
        # Load recent benign events for this function
        benign_events = self.trace_store.get_recent_events(
            candidate.function_name,
            module_name=candidate.module_name,
            count=validation_sample_size
        )
        
        if not benign_events:
            # No benign events available - cannot validate
            # Conservative approach: reject candidate
            return False
        
        # Compute false positive rate
        fp_rate = self.compute_fp_rate(benign_events, candidate)
        
        # Pass if FP rate is acceptable
        return fp_rate <= self.max_fp_rate
    
    def compute_fp_rate(
        self,
        benign_events: List[TelemetryEvent],
        candidate: DetectionCandidate
    ) -> float:
        """Compute false positive rate for a candidate.
        
        Args:
            benign_events: List of known benign events
            candidate: DetectionCandidate with threshold
            
        Returns:
            False positive rate (0.0 to 1.0)
        """
        if not benign_events:
            return 1.0  # Conservative: assume 100% FP if no data
        
        # Count how many benign events would trigger this candidate
        false_positives = 0
        
        for event in benign_events:
            # Check if event would exceed candidate threshold
            # Using simple duration-based check
            deviation = abs(event.duration_ms - candidate.baseline_mean)
            normalized_deviation = deviation / candidate.baseline_std if candidate.baseline_std > 0 else 0
            
            # If deviation is large enough to trigger the candidate
            if normalized_deviation * 50 >= candidate.threshold_percentile:
                false_positives += 1
        
        # Compute FP rate
        fp_rate = false_positives / len(benign_events)
        return fp_rate
    
    def is_eligible_for_promotion(
        self,
        candidate: DetectionCandidate,
        validation_sample_size: int = 100
    ) -> bool:
        """Check if candidate is eligible for promotion to detector.
        
        This is an alias for validate_candidate for clarity.
        
        Args:
            candidate: DetectionCandidate to check
            validation_sample_size: Number of benign events to test
            
        Returns:
            True if eligible for promotion
        """
        return self.validate_candidate(candidate, validation_sample_size)
