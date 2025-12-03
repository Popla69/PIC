"""Integration models for Brain-CellAgent communication.

This module defines data models used for secure communication between
CellAgent and BrainCore, including signed events, signed decisions,
backpressure signals, and rate limit status.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Any
import json

from pic.models.events import TelemetryEvent
from pic.models.decision import Decision


@dataclass
class SignedEvent:
    """Telemetry event with HMAC signature for secure transmission.
    
    Attributes:
        event: The TelemetryEvent being transmitted
        signature: HMAC-SHA256 signature of the event
        nonce: Unique identifier for replay protection (UUID)
        timestamp: When the signature was created
    """
    event: TelemetryEvent
    signature: str
    nonce: str
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary.
        
        Returns:
            Dictionary representation of SignedEvent
        """
        return {
            "event": self.event.to_dict(),
            "signature": self.signature,
            "nonce": self.nonce,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SignedEvent':
        """Deserialize from dictionary.
        
        Args:
            data: Dictionary representation
            
        Returns:
            SignedEvent instance
        """
        # Reconstruct TelemetryEvent from dict
        event_data = data["event"].copy()
        event_data["timestamp"] = datetime.fromisoformat(event_data["timestamp"])
        event = TelemetryEvent(**event_data)
        
        return cls(
            event=event,
            signature=data["signature"],
            nonce=data["nonce"],
            timestamp=datetime.fromisoformat(data["timestamp"])
        )
    
    def to_json(self) -> str:
        """Serialize to JSON string.
        
        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> 'SignedEvent':
        """Deserialize from JSON string.
        
        Args:
            json_str: JSON string representation
            
        Returns:
            SignedEvent instance
        """
        return cls.from_dict(json.loads(json_str))


@dataclass
class SignedDecision:
    """Decision with HMAC signature for secure transmission.
    
    Attributes:
        decision: The Decision being returned
        signature: HMAC-SHA256 signature of the decision
        timestamp: When the signature was created
    """
    decision: Decision
    signature: str
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary.
        
        Returns:
            Dictionary representation of SignedDecision
        """
        return {
            "decision": asdict(self.decision),
            "signature": self.signature,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SignedDecision':
        """Deserialize from dictionary.
        
        Args:
            data: Dictionary representation
            
        Returns:
            SignedDecision instance
        """
        return cls(
            decision=Decision(**data["decision"]),
            signature=data["signature"],
            timestamp=datetime.fromisoformat(data["timestamp"])
        )
    
    def to_json(self) -> str:
        """Serialize to JSON string.
        
        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> 'SignedDecision':
        """Deserialize from JSON string.
        
        Args:
            json_str: JSON string representation
            
        Returns:
            SignedDecision instance
        """
        return cls.from_dict(json.loads(json_str))


@dataclass
class BackpressureSignal:
    """Backpressure signal from BrainCore to CellAgent.
    
    Attributes:
        active: Whether backpressure is currently active
        recommended_rate: Recommended sampling rate (0.0-1.0)
        queue_utilization: Current queue fill percentage (0.0-1.0)
        reason: Human-readable reason for backpressure
    """
    active: bool
    recommended_rate: float
    queue_utilization: float
    reason: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary.
        
        Returns:
            Dictionary representation
        """
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BackpressureSignal':
        """Deserialize from dictionary.
        
        Args:
            data: Dictionary representation
            
        Returns:
            BackpressureSignal instance
        """
        return cls(**data)


@dataclass
class RateLimitStatus:
    """Rate limiting status information.
    
    Attributes:
        global_rate: Current global events per second
        throttled_functions: List of function names currently throttled
        dropped_events: Number of events dropped in current window
        throttling_active: Whether throttling is currently active
    """
    global_rate: int
    throttled_functions: List[str]
    dropped_events: int
    throttling_active: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary.
        
        Returns:
            Dictionary representation
        """
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RateLimitStatus':
        """Deserialize from dictionary.
        
        Args:
            data: Dictionary representation
            
        Returns:
            RateLimitStatus instance
        """
        return cls(**data)
