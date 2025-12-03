"""Decision data model."""

import json
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any


@dataclass
class Decision:
    """Decision made by the system for a telemetry event.
    
    Attributes:
        action: Action to take (allow or block)
        reason: Reason for the decision
        anomaly_score: Anomaly score that triggered decision
        detector_id: ID of detector that made the decision (if any)
        metadata: Additional metadata about the decision
    """
    
    action: str  # "allow" or "block"
    reason: str
    anomaly_score: float
    detector_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(asdict(self))
    
    @classmethod
    def from_json(cls, json_str: str) -> "Decision":
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    def is_block(self) -> bool:
        """Check if decision is to block."""
        return self.action == "block"
    
    def is_allow(self) -> bool:
        """Check if decision is to allow."""
        return self.action == "allow"
    
    @classmethod
    def allow(cls, reason: str = "Normal behavior", anomaly_score: float = 0.0) -> "Decision":
        """Create an allow decision.
        
        Args:
            reason: Reason for allowing
            anomaly_score: Anomaly score
            
        Returns:
            Decision instance
        """
        return cls(action="allow", reason=reason, anomaly_score=anomaly_score)
    
    @classmethod
    def block(cls, reason: str, anomaly_score: float, detector_id: Optional[str] = None) -> "Decision":
        """Create a block decision.
        
        Args:
            reason: Reason for blocking
            anomaly_score: Anomaly score
            detector_id: ID of detector that triggered block
            
        Returns:
            Decision instance
        """
        return cls(
            action="block",
            reason=reason,
            anomaly_score=anomaly_score,
            detector_id=detector_id
        )
