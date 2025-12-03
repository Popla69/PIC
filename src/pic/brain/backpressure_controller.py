"""Backpressure controller for managing event flow."""

import logging
from typing import Optional

from pic.brain.event_queue import EventQueue
from pic.models.integration import BackpressureSignal


class BackpressureController:
    """Controls backpressure based on queue utilization.
    
    Features:
    - Monitor queue utilization
    - Generate backpressure signals
    - Calculate recommended sampling rates
    - Adaptive rate adjustment
    """
    
    def __init__(self, event_queue: EventQueue):
        """Initialize BackpressureController.
        
        Args:
            event_queue: EventQueue to monitor
        """
        self.queue = event_queue
        self.logger = logging.getLogger(__name__)
        
        # State
        self._backpressure_active = False
        self._last_utilization = 0.0
        
        # Statistics
        self._total_checks = 0
        self._backpressure_activations = 0
    
    def check_and_signal(self) -> BackpressureSignal:
        """Check queue state and generate backpressure signal.
        
        Returns:
            BackpressureSignal with current state
        """
        self._total_checks += 1
        
        # Get current utilization
        utilization = self.queue.get_utilization()
        self._last_utilization = utilization
        
        # Check if backpressure should be active
        was_active = self._backpressure_active
        self._backpressure_active = self.queue.has_backpressure()
        
        # Log activation/deactivation
        if self._backpressure_active and not was_active:
            self._backpressure_activations += 1
            self.logger.warning(f"Backpressure activated (utilization: {utilization:.1%})")
        elif not self._backpressure_active and was_active:
            self.logger.info(f"Backpressure deactivated (utilization: {utilization:.1%})")
        
        # Calculate recommended rate
        recommended_rate = self.get_recommended_rate(utilization)
        
        # Generate reason
        if self._backpressure_active:
            reason = f"Queue utilization high: {utilization:.1%}"
        else:
            reason = "Normal operation"
        
        return BackpressureSignal(
            active=self._backpressure_active,
            recommended_rate=recommended_rate,
            queue_utilization=utilization,
            reason=reason
        )
    
    def get_recommended_rate(self, utilization: Optional[float] = None) -> float:
        """Calculate recommended sampling rate based on utilization.
        
        Args:
            utilization: Queue utilization (uses current if None)
            
        Returns:
            Recommended sampling rate (0.0-1.0)
        """
        if utilization is None:
            utilization = self.queue.get_utilization()
        
        # Adaptive rate calculation
        if utilization >= 0.95:
            # Critical: reduce to 10%
            return 0.1
        elif utilization >= 0.9:
            # Severe: reduce to 25%
            return 0.25
        elif utilization >= 0.8:
            # High: reduce to 50%
            return 0.5
        elif utilization >= 0.7:
            # Moderate: reduce to 75%
            return 0.75
        else:
            # Normal: full rate
            return 1.0
    
    def is_backpressure_active(self) -> bool:
        """Check if backpressure is currently active.
        
        Returns:
            True if backpressure is active
        """
        return self._backpressure_active
    
    def get_stats(self) -> dict:
        """Get backpressure controller statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            "backpressure_active": self._backpressure_active,
            "last_utilization": self._last_utilization,
            "total_checks": self._total_checks,
            "backpressure_activations": self._backpressure_activations,
            "queue_stats": self.queue.get_stats()
        }
