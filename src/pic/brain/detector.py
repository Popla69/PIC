"""Anomaly detector using percentile-based thresholds."""

import math
from typing import Optional
from pic.models.baseline import BaselineProfile
from pic.models.events import TelemetryEvent
from pic.models.detector import DetectionCandidate
from pic.brain.normalizer import FeatureNormalizer


class AnomalyDetector:
    """Detect anomalies using percentile-based thresholds."""
    
    def __init__(self, threshold_percentile: float = 95.0, candidate_score_threshold: float = 80.0):
        """Initialize detector.
        
        Args:
            threshold_percentile: Percentile threshold for detection (0-100)
            candidate_score_threshold: Score threshold for creating candidates (0-100)
        """
        self.threshold_percentile = threshold_percentile
        self.candidate_score_threshold = candidate_score_threshold
        self.normalizer = FeatureNormalizer()
    
    def compute_anomaly_score(self, event: TelemetryEvent, baseline: BaselineProfile) -> float:
        """Compute anomaly score for an event using L2 distance and percentile ranking.
        
        Args:
            event: TelemetryEvent to score
            baseline: BaselineProfile for comparison
            
        Returns:
            Anomaly score (0-100)
        """
        # Normalize the event duration
        normalized_duration = self.normalizer.normalize_value(
            event.duration_ms,
            baseline.mean_duration_ms,
            baseline.std_duration_ms
        )
        
        # Compute L2 distance from baseline mean (which is 0 after normalization)
        l2_distance = abs(normalized_duration)
        
        # Compute percentile rank based on distance
        # Map distance to percentile: 0 std = 50th, 1 std = ~84th, 2 std = ~97.5th, 3 std = ~99.9th
        percentile_rank = self._distance_to_percentile(l2_distance)
        
        # Convert percentile rank to anomaly score (0-100)
        # Higher percentile = higher anomaly score
        anomaly_score = percentile_rank
        
        return min(100.0, max(0.0, anomaly_score))
    
    def _distance_to_percentile(self, distance: float) -> float:
        """Convert L2 distance (in standard deviations) to percentile rank.
        
        Uses normal distribution approximation:
        - 0 std = 50th percentile
        - 1 std = 84th percentile
        - 2 std = 97.5th percentile
        - 3 std = 99.9th percentile
        
        Args:
            distance: L2 distance in standard deviations
            
        Returns:
            Percentile rank (0-100)
        """
        # Approximate percentile using normal distribution
        # For simplicity, use linear interpolation between known points
        if distance <= 0:
            return 50.0
        elif distance <= 1.0:
            return 50.0 + (distance * 34.0)  # 50 to 84
        elif distance <= 2.0:
            return 84.0 + ((distance - 1.0) * 13.5)  # 84 to 97.5
        elif distance <= 3.0:
            return 97.5 + ((distance - 2.0) * 2.4)  # 97.5 to 99.9
        else:
            return 99.9 + min(0.1, (distance - 3.0) * 0.01)  # Cap at ~100
    
    def is_anomaly(self, score: float) -> bool:
        """Check if score indicates anomaly.
        
        Args:
            score: Anomaly score
            
        Returns:
            True if anomaly
        """
        return score >= self.threshold_percentile
    
    def create_candidate(
        self,
        event: TelemetryEvent,
        baseline: BaselineProfile,
        score: float
    ) -> Optional[DetectionCandidate]:
        """Create detection candidate if score exceeds threshold.
        
        Args:
            event: TelemetryEvent that triggered detection
            baseline: BaselineProfile used for detection
            score: Anomaly score
            
        Returns:
            DetectionCandidate if score > threshold, None otherwise
        """
        if score < self.candidate_score_threshold:
            return None
        
        return DetectionCandidate(
            function_name=event.function_name,
            module_name=event.module_name,
            anomaly_score=score,
            threshold_percentile=self.threshold_percentile,
            baseline_mean=baseline.mean_duration_ms,
            baseline_std=baseline.std_duration_ms,
            observed_value=event.duration_ms,
            sample_count=baseline.sample_count
        )
