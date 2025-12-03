"""Error recovery and graceful degradation for PIC."""

import logging
import time
from typing import Dict, Optional
from collections import deque
from datetime import datetime, timedelta


class ErrorRecovery:
    """Handles error recovery and graceful degradation.
    
    Features:
    - Track error frequency by type
    - Detect degraded mode conditions
    - Provide recovery strategies
    - Alert on critical conditions
    """
    
    def __init__(
        self,
        error_threshold: int = 10,
        time_window_seconds: int = 60,
        degraded_mode_threshold: int = 50
    ):
        """Initialize ErrorRecovery.
        
        Args:
            error_threshold: Errors per window before alerting
            time_window_seconds: Time window for error tracking
            degraded_mode_threshold: Errors per window to enter degraded mode
        """
        self.error_threshold = error_threshold
        self.time_window_seconds = time_window_seconds
        self.degraded_mode_threshold = degraded_mode_threshold
        self.logger = logging.getLogger(__name__)
        
        # Error tracking
        self._error_history: deque = deque(maxlen=1000)
        self._error_counts: Dict[str, int] = {}
        
        # State
        self._degraded_mode = False
        self._degraded_mode_entered = None
        
        # Statistics
        self._total_errors = 0
        self._communication_errors = 0
        self._security_errors = 0
        self._performance_errors = 0
    
    def handle_communication_error(self, error: Exception, context: str = "") -> None:
        """Handle communication error (network, timeout, etc.).
        
        Args:
            error: Exception that occurred
            context: Additional context about the error
        """
        self._communication_errors += 1
        self._record_error("communication", error, context)
        
        self.logger.error(f"Communication error: {error} (context: {context})")
        
        # Check if we should enter degraded mode
        self._check_degraded_mode()
    
    def handle_security_error(self, error: Exception, context: str = "") -> None:
        """Handle security error (invalid signature, replay attack, etc.).
        
        Args:
            error: Exception that occurred
            context: Additional context about the error
        """
        self._security_errors += 1
        self._record_error("security", error, context)
        
        self.logger.error(f"Security error: {error} (context: {context})")
        
        # Security errors are critical - check degraded mode
        self._check_degraded_mode()
    
    def handle_performance_degradation(self, metric: str, value: float, threshold: float) -> None:
        """Handle performance degradation.
        
        Args:
            metric: Performance metric name
            value: Current value
            threshold: Threshold that was exceeded
        """
        self._performance_errors += 1
        error_msg = f"{metric} exceeded threshold: {value} > {threshold}"
        self._record_error("performance", Exception(error_msg), metric)
        
        self.logger.warning(f"Performance degradation: {error_msg}")
        
        # Check if we should enter degraded mode
        self._check_degraded_mode()
    
    def _record_error(self, error_type: str, error: Exception, context: str) -> None:
        """Record error in history.
        
        Args:
            error_type: Type of error
            error: Exception that occurred
            context: Additional context
        """
        self._total_errors += 1
        
        # Add to history
        self._error_history.append({
            "timestamp": datetime.now(),
            "type": error_type,
            "error": str(error),
            "context": context
        })
        
        # Update counts
        if error_type not in self._error_counts:
            self._error_counts[error_type] = 0
        self._error_counts[error_type] += 1
    
    def _check_degraded_mode(self) -> None:
        """Check if system should enter degraded mode."""
        # Count recent errors
        cutoff_time = datetime.now() - timedelta(seconds=self.time_window_seconds)
        recent_errors = sum(
            1 for entry in self._error_history
            if entry["timestamp"] > cutoff_time
        )
        
        # Check if we should enter degraded mode
        if recent_errors >= self.degraded_mode_threshold and not self._degraded_mode:
            self._enter_degraded_mode()
        elif recent_errors < self.error_threshold and self._degraded_mode:
            self._exit_degraded_mode()
    
    def _enter_degraded_mode(self) -> None:
        """Enter degraded mode."""
        self._degraded_mode = True
        self._degraded_mode_entered = datetime.now()
        
        self.logger.critical(
            f"ENTERING DEGRADED MODE: Error rate exceeded threshold. "
            f"Total errors in window: {self._get_recent_error_count()}"
        )
        
        # TODO: Send alert to administrators
    
    def _exit_degraded_mode(self) -> None:
        """Exit degraded mode."""
        duration = None
        if self._degraded_mode_entered:
            duration = (datetime.now() - self._degraded_mode_entered).total_seconds()
        
        self._degraded_mode = False
        self._degraded_mode_entered = None
        
        self.logger.info(
            f"EXITING DEGRADED MODE: Error rate normalized. "
            f"Duration: {duration:.1f}s" if duration else "EXITING DEGRADED MODE"
        )
    
    def _get_recent_error_count(self) -> int:
        """Get count of recent errors within time window.
        
        Returns:
            Number of recent errors
        """
        cutoff_time = datetime.now() - timedelta(seconds=self.time_window_seconds)
        return sum(
            1 for entry in self._error_history
            if entry["timestamp"] > cutoff_time
        )
    
    def is_degraded(self) -> bool:
        """Check if system is in degraded mode.
        
        Returns:
            True if in degraded mode
        """
        return self._degraded_mode
    
    def get_error_rate(self) -> float:
        """Get current error rate (errors per second).
        
        Returns:
            Error rate
        """
        recent_count = self._get_recent_error_count()
        return recent_count / self.time_window_seconds
    
    def get_stats(self) -> dict:
        """Get error recovery statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            "total_errors": self._total_errors,
            "communication_errors": self._communication_errors,
            "security_errors": self._security_errors,
            "performance_errors": self._performance_errors,
            "recent_error_count": self._get_recent_error_count(),
            "error_rate": self.get_error_rate(),
            "degraded_mode": self._degraded_mode,
            "degraded_mode_duration": (
                (datetime.now() - self._degraded_mode_entered).total_seconds()
                if self._degraded_mode_entered
                else None
            ),
            "error_counts_by_type": dict(self._error_counts)
        }
