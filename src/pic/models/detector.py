"""Detector data model."""

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class DetectionCandidate:
    """Candidate for promotion to a detector.
    
    Attributes:
        function_name: Function that triggered the candidate
        module_name: Module containing the function
        anomaly_score: Computed anomaly score (0-100)
        threshold_percentile: Percentile threshold used
        baseline_mean: Baseline mean value
        baseline_std: Baseline standard deviation
        observed_value: Observed value that triggered detection
        sample_count: Number of samples in baseline
    """
    
    function_name: str
    module_name: str
    anomaly_score: float
    threshold_percentile: float
    baseline_mean: float
    baseline_std: float
    observed_value: float
    sample_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class Detector:
    """Detection signature for anomalous behavior.
    
    Attributes:
        id: Unique detector identifier (UUID)
        function_name: Function this detector monitors
        threshold: Anomaly score threshold (percentile)
        signature_hash: SHA-256 hash of the detection pattern
        created_at: When detector was created
        expires_at: When detector expires (TTL)
        is_active: Whether detector is currently active
    """
    
    id: str
    function_name: str
    threshold: float
    signature_hash: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool = True
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        if self.expires_at:
            data["expires_at"] = self.expires_at.isoformat()
        return json.dumps(data)
    
    @classmethod
    def from_json(cls, json_str: str) -> "Detector":
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        if data.get("expires_at"):
            data["expires_at"] = datetime.fromisoformat(data["expires_at"])
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        if self.expires_at:
            data["expires_at"] = self.expires_at.isoformat()
        return data
    
    def is_expired(self, current_time: Optional[datetime] = None) -> bool:
        """Check if detector has expired.
        
        Args:
            current_time: Current time (default: now)
            
        Returns:
            True if expired
        """
        if self.expires_at is None:
            return False
        
        if current_time is None:
            current_time = datetime.now()
        
        return current_time >= self.expires_at
