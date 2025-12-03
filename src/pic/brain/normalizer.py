"""Feature normalizer for stable anomaly detection."""

from typing import Optional, List
from pic.models.baseline import BaselineProfile
from pic.models.events import TelemetryEvent


class FeatureNormalizer:
    """Normalize telemetry features before anomaly detection."""
    
    def __init__(self, baseline: Optional[BaselineProfile] = None):
        """Initialize with optional baseline statistics.
        
        Args:
            baseline: Optional BaselineProfile for normalization parameters
        """
        self.baseline = baseline
    
    def normalize_value(self, value: float, mean: float, std: float) -> float:
        """Normalize a value using z-score normalization.
        
        Args:
            value: Value to normalize
            mean: Mean for normalization
            std: Standard deviation for normalization
            
        Returns:
            Normalized value (in standard deviations from mean)
        """
        if std == 0:
            return 0.0
        
        return (value - mean) / std
    
    def normalize(self, event: TelemetryEvent) -> float:
        """Normalize event duration to [0, 1] range using min-max scaling.
        
        Args:
            event: TelemetryEvent to normalize
            
        Returns:
            Normalized duration value
        """
        if self.baseline is None:
            return 0.0
        
        duration = event.duration_ms
        
        # Handle missing baseline
        if self.baseline.p99_duration_ms == 0:
            return 0.0
        
        # Cap outliers at p99
        if duration > self.baseline.p99_duration_ms:
            duration = self.baseline.p99_duration_ms
        
        # Min-max scaling
        min_val = 0.0
        max_val = self.baseline.p99_duration_ms
        
        if max_val == min_val:
            return 0.0
        
        normalized = (duration - min_val) / (max_val - min_val)
        return max(0.0, min(1.0, normalized))
    
    def normalize_batch(self, values: List[float]) -> List[float]:
        """Normalize a batch of values using min-max scaling.
        
        Args:
            values: List of values to normalize
            
        Returns:
            List of normalized values
        """
        if not values:
            return []
        
        min_val = min(values)
        max_val = max(values)
        
        if max_val == min_val:
            return [0.5] * len(values)
        
        return [(v - min_val) / (max_val - min_val) for v in values]
    
    def update_baseline(self, baseline: BaselineProfile) -> None:
        """Update normalization parameters.
        
        Args:
            baseline: New BaselineProfile
        """
        self.baseline = baseline
