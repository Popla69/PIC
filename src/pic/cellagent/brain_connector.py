"""Brain connector for CellAgent to communicate with BrainCore."""

import time
import logging
from typing import Optional

from pic.config import PICConfig
from pic.crypto import CryptoCore
from pic.brain.core import BrainCore
from pic.models.events import TelemetryEvent
from pic.models.decision import Decision
from pic.cellagent.secure_transport import SecureTransport


class BrainConnector:
    """Manages secure connection between CellAgent and BrainCore.
    
    Features:
    - Secure event transmission with HMAC
    - Retry logic with exponential backoff
    - Fail-open and fail-closed modes
    - Timeout handling
    """
    
    def __init__(
        self,
        brain_core: BrainCore,
        crypto_core: CryptoCore,
        config: PICConfig
    ):
        """Initialize BrainConnector.
        
        Args:
            brain_core: BrainCore instance
            crypto_core: CryptoCore instance
            config: PICConfig instance
        """
        self.brain = brain_core
        self.crypto = crypto_core
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.fail_mode = config.get("cellagent.fail_mode", "open")  # "open" or "closed"
        self.timeout_ms = config.get("cellagent.brain_timeout_ms", 10)
        self.retry_attempts = config.get("cellagent.retry_attempts", 3)
        self.retry_backoff_ms = config.get("cellagent.retry_backoff_ms", 100)
        
        # Secure transport
        self.transport = SecureTransport(crypto_core)
        
        # Statistics
        self._total_requests = 0
        self._successful_requests = 0
        self._failed_requests = 0
        self._retries = 0
        
    def send_event(self, event: TelemetryEvent) -> Decision:
        """Send event to BrainCore and get decision.
        
        Args:
            event: TelemetryEvent to send
            
        Returns:
            Decision from BrainCore
        """
        self._total_requests += 1
        
        # Try with retries
        for attempt in range(self.retry_attempts):
            try:
                # Sign event
                signed_event = self.transport.sign_event(event)
                
                # Send to BrainCore with timeout
                start_time = time.time()
                decision = self.brain.process_event(event)
                elapsed_ms = (time.time() - start_time) * 1000
                
                # Check timeout
                if elapsed_ms > self.timeout_ms:
                    self.logger.warning(f"BrainCore response exceeded timeout: {elapsed_ms:.2f}ms")
                    if attempt < self.retry_attempts - 1:
                        self._retries += 1
                        time.sleep(self._get_backoff_delay(attempt) / 1000)
                        continue
                    else:
                        return self.handle_failure(TimeoutError("BrainCore timeout"))
                
                # Success
                self._successful_requests += 1
                return decision
                
            except Exception as e:
                self.logger.error(f"Error sending event to BrainCore (attempt {attempt + 1}): {e}")
                
                if attempt < self.retry_attempts - 1:
                    # Retry with backoff
                    self._retries += 1
                    time.sleep(self._get_backoff_delay(attempt) / 1000)
                else:
                    # All retries exhausted
                    self._failed_requests += 1
                    return self.handle_failure(e)
        
        # Should not reach here
        return self.handle_failure(Exception("Unknown error"))
    
    def _get_backoff_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay in milliseconds.
        
        Args:
            attempt: Current attempt number (0-indexed)
            
        Returns:
            Delay in milliseconds
        """
        return self.retry_backoff_ms * (2 ** attempt)
    
    def is_available(self) -> bool:
        """Check if BrainCore is available.
        
        Returns:
            True if BrainCore is available, False otherwise
        """
        try:
            # Simple health check - try to get stats
            stats = self.brain.get_stats()
            return stats is not None
        except Exception as e:
            self.logger.error(f"BrainCore health check failed: {e}")
            return False
    
    def handle_failure(self, error: Exception) -> Decision:
        """Handle BrainCore failure based on fail mode.
        
        Args:
            error: Exception that caused the failure
            
        Returns:
            Decision based on fail mode
        """
        if self.fail_mode == "open":
            # Fail-open: allow traffic
            self.logger.warning(f"Fail-open mode: allowing traffic due to error: {error}")
            return Decision.allow(f"Fail-open: {str(error)}")
        else:
            # Fail-closed: block traffic
            self.logger.warning(f"Fail-closed mode: blocking traffic due to error: {error}")
            return Decision.block(f"Fail-closed: {str(error)}")
    
    def get_stats(self) -> dict:
        """Get connector statistics.
        
        Returns:
            Dictionary with statistics
        """
        success_rate = (
            self._successful_requests / self._total_requests
            if self._total_requests > 0
            else 0.0
        )
        
        return {
            "total_requests": self._total_requests,
            "successful_requests": self._successful_requests,
            "failed_requests": self._failed_requests,
            "retries": self._retries,
            "success_rate": success_rate,
            "fail_mode": self.fail_mode,
            "transport_stats": self.transport.get_cache_stats()
        }
