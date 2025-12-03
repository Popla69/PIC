"""Baseline profile data model."""

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any


@dataclass
class BaselineProfile:
    """Statistical baseline profile for a function.
    
    Attributes:
        function_name: Name of the function
        module_name: Module containing the function
        version: Profile version (incremented on updates)
        created_at: When profile was created
        updated_at: When profile was last updated
        sample_count: Number of samples in profile
        mean_duration_ms: Mean execution duration
        std_duration_ms: Standard deviation of duration
        p50_duration_ms: 50th percentile (median) duration
        p95_duration_ms: 95th percentile duration
        p99_duration_ms: 99th percentile duration
        historical_distances: List of L2 distances for percentile calculation
    """
    
    function_name: str
    module_name: str
    version: int
    created_at: datetime
    updated_at: datetime
    sample_count: int
    mean_duration_ms: float
    std_duration_ms: float
    p50_duration_ms: float
    p95_duration_ms: float
    p99_duration_ms: float
    historical_distances: list[float]
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        return json.dumps(data)
    
    @classmethod
    def from_json(cls, json_str: str) -> "BaselineProfile":
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        return data
    
    def is_sufficient(self, min_samples: int = 20) -> bool:
        """Check if profile has sufficient samples for detection.
        
        Args:
            min_samples: Minimum required samples
            
        Returns:
            True if profile is sufficient
        """
        return self.sample_count >= min_samples
