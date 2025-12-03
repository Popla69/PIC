"""Event data models."""

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any, Optional


@dataclass
class TelemetryEvent:
    """Telemetry event captured from monitored application.
    
    Attributes:
        timestamp: Event timestamp
        event_id: Unique event identifier (UUID)
        process_id: Process ID
        thread_id: Thread ID
        function_name: Name of instrumented function
        module_name: Module containing the function
        duration_ms: Execution duration in milliseconds
        args_metadata: Metadata about function arguments (hashed)
        resource_tags: Resource usage tags (I/O, network, etc.)
        redaction_applied: Whether PII redaction was applied
        sampling_rate: Sampling rate used
    """
    
    timestamp: datetime
    event_id: str
    process_id: int
    thread_id: int
    function_name: str
    module_name: str
    duration_ms: float
    args_metadata: Dict[str, Any]
    resource_tags: Dict[str, int]
    redaction_applied: bool
    sampling_rate: float
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return json.dumps(data)
    
    @classmethod
    def from_json(cls, json_str: str) -> "TelemetryEvent":
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


@dataclass
class AuditEvent:
    """Audit log event for immutable logging.
    
    Attributes:
        timestamp: Event timestamp
        event_type: Type of event (detection, promotion, rollback, etc.)
        actor: Who/what triggered the event (system, operator, etc.)
        action: Action taken (allow, block, promote, etc.)
        target: Target of the action (function name, detector ID, etc.)
        result: Result of the action (success, failure, etc.)
        anomaly_score: Anomaly score if applicable
        signature: HMAC-SHA256 signature of the event
        metadata: Additional metadata
    """
    
    timestamp: datetime
    event_type: str
    actor: str
    action: str
    result: str
    signature: str
    target: Optional[str] = None
    anomaly_score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return json.dumps(data)
    
    @classmethod
    def from_json(cls, json_str: str) -> "AuditEvent":
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data
    
    def get_signable_data(self) -> bytes:
        """Get data to be signed (excludes signature field).
        
        Returns:
            Bytes representation of event data for signing
        """
        data = self.to_dict()
        # Remove signature field before signing
        data.pop("signature", None)
        return json.dumps(data, sort_keys=True).encode("utf-8")
