"""TraceStore - In-memory ring buffer for recent telemetry events."""

from collections import deque, defaultdict
from typing import List, Dict
from threading import Lock

from pic.models.events import TelemetryEvent


class TraceStore:
    """In-memory buffer of recent telemetry events for validation and analysis.
    
    Features:
    - Ring buffer with configurable capacity per function
    - Automatic eviction of oldest events
    - Fast lookup by function name
    - Thread-safe operations
    """
    
    def __init__(self, capacity_per_function: int = 1000):
        """Initialize TraceStore.
        
        Args:
            capacity_per_function: Maximum events to store per function
        """
        self.capacity_per_function = capacity_per_function
        self._buffers: Dict[str, deque] = defaultdict(lambda: deque(maxlen=capacity_per_function))
        self._lock = Lock()
        self._total_events = 0
    
    def add_event(self, event: TelemetryEvent) -> None:
        """Add event to buffer (evict oldest if full).
        
        Args:
            event: TelemetryEvent to add
        """
        with self._lock:
            key = f"{event.module_name}.{event.function_name}"
            self._buffers[key].append(event)
            self._total_events += 1
    
    def get_recent_events(self, function_name: str, module_name: str = "", count: int = 100) -> List[TelemetryEvent]:
        """Get recent events for a function.
        
        Args:
            function_name: Name of the function
            module_name: Module name (optional, for disambiguation)
            count: Maximum number of events to return
            
        Returns:
            List of recent TelemetryEvent instances (newest first)
        """
        with self._lock:
            # Try with module name first
            if module_name:
                key = f"{module_name}.{function_name}"
                if key in self._buffers:
                    buffer = self._buffers[key]
                    # Return newest first (reverse order)
                    return list(reversed(list(buffer)))[-count:]
            
            # Try without module name (search all buffers)
            matching_events = []
            for key, buffer in self._buffers.items():
                if key.endswith(f".{function_name}"):
                    matching_events.extend(buffer)
            
            # Sort by timestamp (newest first) and limit
            matching_events.sort(key=lambda e: e.timestamp, reverse=True)
            return matching_events[:count]
    
    def get_all_events(self, function_name: str, module_name: str = "") -> List[TelemetryEvent]:
        """Get all buffered events for a function.
        
        Args:
            function_name: Name of the function
            module_name: Module name (optional)
            
        Returns:
            List of all TelemetryEvent instances for the function
        """
        return self.get_recent_events(function_name, module_name, count=self.capacity_per_function)
    
    def get_stats(self) -> Dict[str, any]:
        """Return buffer statistics.
        
        Returns:
            Dictionary with statistics
        """
        with self._lock:
            return {
                "total_events_processed": self._total_events,
                "functions_tracked": len(self._buffers),
                "capacity_per_function": self.capacity_per_function,
                "current_buffer_sizes": {
                    key: len(buffer) for key, buffer in self._buffers.items()
                }
            }
    
    def clear(self) -> None:
        """Clear all buffers."""
        with self._lock:
            self._buffers.clear()
            self._total_events = 0
    
    def get_function_count(self, function_name: str, module_name: str = "") -> int:
        """Get number of events buffered for a function.
        
        Args:
            function_name: Name of the function
            module_name: Module name (optional)
            
        Returns:
            Number of buffered events
        """
        with self._lock:
            if module_name:
                key = f"{module_name}.{function_name}"
                return len(self._buffers.get(key, []))
            
            # Count across all matching buffers
            count = 0
            for key, buffer in self._buffers.items():
                if key.endswith(f".{function_name}"):
                    count += len(buffer)
            return count
