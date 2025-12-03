"""Telemetry transport for batch transmission with retry."""

import time
import requests
from typing import List
from pic.models.events import TelemetryEvent


class TelemetryTransport:
    """Reliable batch transmission with simple retry logic."""
    
    def __init__(self, endpoint: str, max_retries: int = 3, retry_delay: float = 1.0):
        """Initialize transport.
        
        Args:
            endpoint: SentinelBrain endpoint URL
            max_retries: Maximum retry attempts
            retry_delay: Delay between retries in seconds
        """
        self.endpoint = endpoint
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._stats = {"sent": 0, "failed": 0, "retries": 0}
    
    def send_batch(self, events: List[TelemetryEvent]) -> bool:
        """Send batch with retry logic.
        
        Args:
            events: List of TelemetryEvent to send
            
        Returns:
            True if successful, False otherwise
        """
        if not events:
            return True
        
        # Serialize events
        payload = [event.to_dict() for event in events]
        
        # Retry loop
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    f"{self.endpoint}/api/v1/telemetry",
                    json={"events": payload},
                    timeout=5
                )
                
                if response.status_code == 200:
                    self._stats["sent"] += len(events)
                    return True
                
            except Exception as e:
                print(f"Transport error (attempt {attempt + 1}): {e}")
                self._stats["retries"] += 1
            
            # Wait before retry
            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay)
        
        # All retries failed
        self._stats["failed"] += len(events)
        return False
    
    def get_stats(self) -> dict:
        """Get transmission statistics."""
        return self._stats.copy()
