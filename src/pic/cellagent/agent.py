"""CellAgent - In-process instrumentation for Python applications."""

import time
import os
import logging
import threading
import uuid
from functools import wraps
from collections import deque
from datetime import datetime
from typing import Callable, Any, Optional

from pic.config import PICConfig
from pic.models.events import TelemetryEvent
from pic.models.decision import Decision
from pic.cellagent.redaction import PIIRedactor
from pic.cellagent.rate_limiter import RateLimiter


class CellAgent:
    """Lightweight instrumentation layer for collecting behavioral telemetry.
    
    Features:
    - Decorator-based instrumentation
    - Configurable sampling
    - PII redaction
    - Ring buffer with overflow handling
    - Graceful error handling (never crashes monitored app)
    - Rate limiting and throttling
    """
    
    def __init__(self, config: Optional[PICConfig] = None):
        """Initialize CellAgent.
        
        Args:
            config: PICConfig instance (loads default if None)
        """
        self.config = config or PICConfig.load()
        self.redactor = PIIRedactor()
        
        # Configuration
        self.sampling_rate = self.config.get("cellagent.sampling_rate", 0.1)
        self.buffer_size = self.config.get("cellagent.buffer_size", 10000)
        self.batch_size = self.config.get("cellagent.batch_size", 100)
        self.batch_interval_sec = self.config.get("cellagent.batch_interval_sec", 5)
        self.cpu_threshold = self.config.get("cellagent.cpu_threshold", 0.02)
        
        # State
        self._buffer = deque(maxlen=self.buffer_size)
        self._lock = threading.Lock()
        self._sample_counter = 0
        self._total_events = 0
        self._running = False
        self._batch_thread: Optional[threading.Thread] = None
        
        # Callbacks for sending telemetry
        self._send_callback: Optional[Callable] = None
        
        # Brain connector (optional)
        self._brain_connector = None
        self._observe_only = self.config.get("cellagent.observe_only", False)
        
        # Rate limiter
        global_limit = self.config.get("cellagent.global_rate_limit", 10000)
        per_function_limit = self.config.get("cellagent.per_function_rate_limit", 1000)
        self.rate_limiter = RateLimiter(
            global_limit=global_limit,
            per_function_limit=per_function_limit
        )
        
        # Performance tracking
        self._latencies = deque(maxlen=1000)  # Track last 1000 latencies
        self._throttle_events = 0
        
        # Logger
        self.logger = logging.getLogger(__name__)
    
    def monitor(self, func: Callable) -> Callable:
        """Decorator to instrument a function.
        
        Args:
            func: Function to instrument
            
        Returns:
            Wrapped function
            
        Example:
            @agent.monitor
            def process_payment(amount, user_id):
                return {"status": "success"}
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check rate limit first
            if not self.rate_limiter.check_rate(func.__name__):
                self._throttle_events += 1
                # Execute without instrumentation if throttled
                return func(*args, **kwargs)
            
            # Check if we should sample this call
            should_sample = self._should_sample()
            
            if not should_sample:
                # Execute without instrumentation
                return func(*args, **kwargs)
            
            # Capture start time
            start_time = time.perf_counter()
            exception_occurred = None
            result = None
            decision = None
            brain_latency_ms = 0.0
            
            try:
                # Create telemetry event BEFORE execution if Brain is connected
                if self._brain_connector:
                    # Create event with estimated duration (will be updated)
                    event = self._create_telemetry_event(
                        func=func,
                        args=args,
                        kwargs=kwargs,
                        duration_ms=0.0,  # Will be updated
                        exception=None
                    )
                    
                    # Send to Brain and get decision
                    try:
                        brain_start = time.perf_counter()
                        decision = self._brain_connector.send_event(event)
                        brain_latency_ms = (time.perf_counter() - brain_start) * 1000
                        
                        # Track latency
                        self._latencies.append(brain_latency_ms)
                        
                        # Enforce decision if not in observe-only mode
                        if not self._observe_only and decision.action == "block":
                            raise SecurityException(f"Blocked by PIC: {decision.reason}")
                    except Exception as brain_error:
                        # Never let Brain errors crash the app
                        print(f"Brain error (non-fatal): {brain_error}")
                        decision = Decision.allow("Brain error, fail-open")
                
                # Execute function
                result = func(*args, **kwargs)
                return result
                
            except SecurityException:
                # Re-raise security blocks
                raise
            except Exception as e:
                # Capture exception but re-raise it
                exception_occurred = e
                raise
                
            finally:
                # Always capture telemetry (even on exception)
                try:
                    end_time = time.perf_counter()
                    duration_ms = (end_time - start_time) * 1000
                    
                    # Create telemetry event
                    event = self._create_telemetry_event(
                        func=func,
                        args=args,
                        kwargs=kwargs,
                        duration_ms=duration_ms,
                        exception=exception_occurred
                    )
                    
                    # Add to buffer
                    self._add_to_buffer(event)
                    
                except Exception as e:
                    # Never let instrumentation crash the app
                    print(f"CellAgent error (non-fatal): {e}")
        
        return wrapper
    
    def _should_sample(self) -> bool:
        """Determine if this event should be sampled.
        
        Returns:
            True if event should be sampled
        """
        with self._lock:
            self._sample_counter += 1
            
            # Simple sampling: 1 in N events
            sample_interval = int(1 / self.sampling_rate) if self.sampling_rate > 0 else 1
            should_sample = (self._sample_counter % sample_interval) == 0
            
            return should_sample
    
    def _create_telemetry_event(
        self,
        func: Callable,
        args: tuple,
        kwargs: dict,
        duration_ms: float,
        exception: Optional[Exception] = None
    ) -> TelemetryEvent:
        """Create a telemetry event from function execution.
        
        Args:
            func: Function that was called
            args: Positional arguments
            kwargs: Keyword arguments
            duration_ms: Execution duration in milliseconds
            exception: Exception if one occurred
            
        Returns:
            TelemetryEvent instance
        """
        # Redact and hash arguments
        args_metadata = self.redactor.redact_and_hash_args(args, kwargs)
        
        # Resource tags (simplified for MVP)
        resource_tags = {
            "io_operations": 0,  # TODO: Track in future version
            "network_calls": 0,  # TODO: Track in future version
            "file_access": 0,    # TODO: Track in future version
        }
        
        # Create event
        event = TelemetryEvent(
            timestamp=datetime.now(),
            event_id=str(uuid.uuid4()),
            process_id=os.getpid(),
            thread_id=threading.get_ident(),
            function_name=func.__name__,
            module_name=func.__module__,
            duration_ms=duration_ms,
            args_metadata=args_metadata,
            resource_tags=resource_tags,
            redaction_applied=True,
            sampling_rate=self.sampling_rate
        )
        
        return event
    
    def _add_to_buffer(self, event: TelemetryEvent) -> None:
        """Add event to buffer.
        
        Args:
            event: TelemetryEvent to buffer
        """
        with self._lock:
            self._buffer.append(event)
            self._total_events += 1
    
    def start(self) -> None:
        """Start the agent (begins batch transmission if configured)."""
        self._running = True
        
        # Start batch transmission thread if callback is set
        if self._send_callback and not self._batch_thread:
            self._batch_thread = threading.Thread(target=self._batch_sender, daemon=True)
            self._batch_thread.start()
    
    def stop(self) -> None:
        """Stop the agent and flush buffers."""
        self._running = False
        
        # Wait for batch thread to finish
        if self._batch_thread:
            self._batch_thread.join(timeout=5)
        
        # Flush remaining events
        self.flush()
    
    def flush(self) -> None:
        """Flush all buffered events."""
        if self._send_callback:
            with self._lock:
                events = list(self._buffer)
                self._buffer.clear()
            
            if events:
                try:
                    self._send_callback(events)
                except Exception as e:
                    print(f"Error flushing events: {e}")
    
    def _batch_sender(self) -> None:
        """Background thread for batch transmission."""
        while self._running:
            time.sleep(self.batch_interval_sec)
            
            # Check if we have enough events to send
            with self._lock:
                if len(self._buffer) >= self.batch_size:
                    # Extract batch
                    batch = []
                    for _ in range(min(self.batch_size, len(self._buffer))):
                        batch.append(self._buffer.popleft())
            
                    # Send batch
                    if batch and self._send_callback:
                        try:
                            self._send_callback(batch)
                        except Exception as e:
                            print(f"Error sending batch: {e}")
    
    def set_send_callback(self, callback: Callable) -> None:
        """Set callback for sending telemetry batches.
        
        Args:
            callback: Function that accepts list of TelemetryEvent
        """
        self._send_callback = callback
    
    def handle_backpressure(self, signal) -> None:
        """Handle backpressure signal from BrainCore.
        
        Args:
            signal: BackpressureSignal from BrainCore
        """
        if signal.active:
            # Adjust sampling rate based on recommendation
            old_rate = self.sampling_rate
            self.sampling_rate = signal.recommended_rate
            self.logger.info(
                f"Backpressure active: adjusted sampling rate from {old_rate:.2f} to {self.sampling_rate:.2f}"
            )
        else:
            # Restore normal sampling rate if configured
            default_rate = self.config.get("cellagent.sampling_rate", 0.1)
            if self.sampling_rate != default_rate:
                self.sampling_rate = default_rate
                self.logger.info(f"Backpressure cleared: restored sampling rate to {default_rate:.2f}")
    
    def get_performance_stats(self) -> dict:
        """Get performance statistics.
        
        Returns:
            Dictionary with performance metrics
        """
        if not self._latencies:
            return {
                "p50_latency_ms": 0.0,
                "p95_latency_ms": 0.0,
                "p99_latency_ms": 0.0,
                "sample_count": 0
            }
        
        # Calculate percentiles
        sorted_latencies = sorted(self._latencies)
        n = len(sorted_latencies)
        
        p50_idx = int(n * 0.50)
        p95_idx = int(n * 0.95)
        p99_idx = int(n * 0.99)
        
        return {
            "p50_latency_ms": sorted_latencies[p50_idx] if p50_idx < n else 0.0,
            "p95_latency_ms": sorted_latencies[p95_idx] if p95_idx < n else 0.0,
            "p99_latency_ms": sorted_latencies[p99_idx] if p99_idx < n else 0.0,
            "sample_count": n
        }
    
    def get_stats(self) -> dict:
        """Get agent statistics.
        
        Returns:
            Dictionary with statistics
        """
        with self._lock:
            stats = {
                "total_events": self._total_events,
                "buffered_events": len(self._buffer),
                "sampling_rate": self.sampling_rate,
                "buffer_size": self.buffer_size,
                "running": self._running,
                "throttle_events": self._throttle_events,
                "rate_limiter_stats": self.rate_limiter.get_stats(),
                "performance": self.get_performance_stats()
            }
            return stats

    def set_brain_connector(self, connector) -> None:
        """Set Brain connector for real-time analysis.
        
        Args:
            connector: BrainConnector instance
        """
        self._brain_connector = connector
    
    def get_brain_stats(self) -> dict:
        """Get Brain connector statistics.
        
        Returns:
            Dictionary with Brain statistics or None if not connected
        """
        if self._brain_connector:
            return self._brain_connector.get_stats()
        return None


class SecurityException(Exception):
    """Exception raised when operation is blocked by PIC."""
    pass
