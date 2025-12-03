"""Rate limiter for CellAgent - prevents telemetry floods."""

import time
import logging
from typing import Dict, Set
from collections import defaultdict


class RateLimiter:
    """Rate limiting and self-throttling for CellAgent.
    
    Features:
    - Global rate limiting (events/sec across all functions)
    - Per-function rate limiting
    - Automatic self-throttling when limits exceeded
    - Sliding window algorithm
    - Dynamic sampling rate adjustment
    """
    
    def __init__(
        self,
        global_limit: int = 10000,
        per_function_limit: int = 1000,
        throttle_threshold: float = 0.8,
        window_seconds: int = 1
    ):
        """Initialize RateLimiter.
        
        Args:
            global_limit: Maximum events/sec globally
            per_function_limit: Maximum events/sec per function
            throttle_threshold: Threshold to activate throttling (0.0-1.0)
            window_seconds: Time window for rate calculation
        """
        self.global_limit = global_limit
        self.per_function_limit = per_function_limit
        self.throttle_threshold = throttle_threshold
        self.window_seconds = window_seconds
        self.logger = logging.getLogger(__name__)
        
        # Counters
        self._global_counter = 0
        self._function_counters: Dict[str, int] = defaultdict(int)
        self._window_start = time.time()
        
        # Throttling state
        self._throttled_functions: Set[str] = set()
        self._throttling_active = False
        self._dropped_events = 0
        
        # Statistics
        self._total_checks = 0
        self._total_allowed = 0
        self._total_throttled = 0
    
    def check_rate(self, function_name: str) -> bool:
        """Check if event should be allowed based on rate limits.
        
        Args:
            function_name: Name of the function generating the event
            
        Returns:
            True if event should be allowed, False if throttled
        """
        self._total_checks += 1
        
        # Reset window if needed
        current_time = time.time()
        if current_time - self._window_start >= self.window_seconds:
            self._reset_window()
        
        # Check global limit
        if self._global_counter >= self.global_limit:
            self._throttling_active = True
            self._total_throttled += 1
            self._dropped_events += 1
            return False
        
        # Check per-function limit
        if self._function_counters[function_name] >= self.per_function_limit:
            self._throttled_functions.add(function_name)
            self._total_throttled += 1
            self._dropped_events += 1
            return False
        
        # Allow event
        self._global_counter += 1
        self._function_counters[function_name] += 1
        self._total_allowed += 1
        return True
    
    def should_throttle(self) -> bool:
        """Check if system should enter throttling mode.
        
        Returns:
            True if throttling should be active
        """
        global_utilization = self._global_counter / self.global_limit
        return global_utilization >= self.throttle_threshold
    
    def get_adjusted_sampling_rate(self, base_rate: float) -> float:
        """Get adjusted sampling rate based on current load.
        
        Args:
            base_rate: Base sampling rate (0.0-1.0)
            
        Returns:
            Adjusted sampling rate
        """
        if not self.should_throttle():
            return base_rate
        
        # Calculate throttling multiplier
        global_utilization = self._global_counter / self.global_limit
        
        if global_utilization >= 1.0:
            # Severe throttling
            return base_rate * 0.1
        elif global_utilization >= 0.9:
            # Heavy throttling
            return base_rate * 0.5
        else:
            # Light throttling
            return base_rate * 0.75
    
    def _reset_window(self) -> None:
        """Reset rate limiting window."""
        # Log if throttling was active
        if self._throttling_active:
            self.logger.info(
                f"Rate limit window reset. Dropped {self._dropped_events} events. "
                f"Throttled functions: {len(self._throttled_functions)}"
            )
        
        # Reset counters
        self._global_counter = 0
        self._function_counters.clear()
        self._throttled_functions.clear()
        self._throttling_active = False
        self._dropped_events = 0
        self._window_start = time.time()
    
    def get_stats(self) -> dict:
        """Get rate limiter statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            "total_checks": self._total_checks,
            "total_allowed": self._total_allowed,
            "total_throttled": self._total_throttled,
            "current_global_rate": self._global_counter,
            "global_limit": self.global_limit,
            "throttled_functions": list(self._throttled_functions),
            "throttling_active": self._throttling_active,
            "dropped_events": self._dropped_events,
            "allow_rate": (
                self._total_allowed / self._total_checks
                if self._total_checks > 0
                else 1.0
            )
        }
