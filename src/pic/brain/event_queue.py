"""Event queue with backpressure handling for BrainCore."""

import logging
import threading
from collections import deque
from typing import Optional

from pic.models.events import TelemetryEvent


class EventQueue:
    """Thread-safe bounded queue with backpressure detection.
    
    Features:
    - Bounded queue with configurable size
    - Backpressure detection based on utilization
    - Drop oldest events when full
    - Thread-safe operations
    """
    
    def __init__(
        self,
        max_size: int = 10000,
        backpressure_threshold: float = 0.8
    ):
        """Initialize EventQueue.
        
        Args:
            max_size: Maximum queue size
            backpressure_threshold: Threshold for backpressure (0.0-1.0)
        """
        self.max_size = max_size
        self.backpressure_threshold = backpressure_threshold
        self.logger = logging.getLogger(__name__)
        
        # Queue
        self._queue: deque = deque(maxlen=max_size)
        self._lock = threading.Lock()
        
        # Statistics
        self._total_enqueued = 0
        self._total_dequeued = 0
        self._total_dropped = 0
    
    def enqueue(self, event: TelemetryEvent) -> bool:
        """Add event to queue.
        
        If queue is full, oldest event is dropped.
        
        Args:
            event: TelemetryEvent to enqueue
            
        Returns:
            True if enqueued, False if dropped
        """
        with self._lock:
            # Check if queue is full
            was_full = len(self._queue) >= self.max_size
            
            # Add to queue (deque automatically drops oldest if full)
            self._queue.append(event)
            self._total_enqueued += 1
            
            if was_full:
                self._total_dropped += 1
                self.logger.warning(f"Queue full, dropped oldest event. Total dropped: {self._total_dropped}")
                return False
            
            return True
    
    def dequeue(self) -> Optional[TelemetryEvent]:
        """Remove and return oldest event from queue.
        
        Returns:
            TelemetryEvent or None if queue is empty
        """
        with self._lock:
            if self._queue:
                self._total_dequeued += 1
                return self._queue.popleft()
            return None
    
    def peek(self) -> Optional[TelemetryEvent]:
        """View oldest event without removing it.
        
        Returns:
            TelemetryEvent or None if queue is empty
        """
        with self._lock:
            if self._queue:
                return self._queue[0]
            return None
    
    def size(self) -> int:
        """Get current queue size.
        
        Returns:
            Number of events in queue
        """
        with self._lock:
            return len(self._queue)
    
    def is_empty(self) -> bool:
        """Check if queue is empty.
        
        Returns:
            True if queue is empty
        """
        with self._lock:
            return len(self._queue) == 0
    
    def is_full(self) -> bool:
        """Check if queue is full.
        
        Returns:
            True if queue is at max capacity
        """
        with self._lock:
            return len(self._queue) >= self.max_size
    
    def get_utilization(self) -> float:
        """Get queue utilization percentage.
        
        Returns:
            Utilization (0.0-1.0)
        """
        with self._lock:
            return len(self._queue) / self.max_size
    
    def has_backpressure(self) -> bool:
        """Check if backpressure threshold is exceeded.
        
        Returns:
            True if backpressure is active
        """
        return self.get_utilization() >= self.backpressure_threshold
    
    def clear(self) -> int:
        """Clear all events from queue.
        
        Returns:
            Number of events cleared
        """
        with self._lock:
            count = len(self._queue)
            self._queue.clear()
            return count
    
    def get_stats(self) -> dict:
        """Get queue statistics.
        
        Returns:
            Dictionary with statistics
        """
        with self._lock:
            return {
                "size": len(self._queue),
                "max_size": self.max_size,
                "utilization": self.get_utilization(),
                "backpressure_active": self.has_backpressure(),
                "total_enqueued": self._total_enqueued,
                "total_dequeued": self._total_dequeued,
                "total_dropped": self._total_dropped,
                "drop_rate": (
                    self._total_dropped / self._total_enqueued
                    if self._total_enqueued > 0
                    else 0.0
                )
            }
