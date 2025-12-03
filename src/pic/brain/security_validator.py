"""Security validator for BrainCore - HMAC verification and replay detection."""

import time
import logging
from datetime import datetime
from typing import Set, Dict
from collections import deque

from pic.crypto import CryptoCore
from pic.models.integration import SignedEvent
from pic.models.events import TelemetryEvent


class SecurityValidator:
    """Validates security properties of incoming events.
    
    Features:
    - HMAC signature verification
    - Replay attack detection via nonce tracking
    - Timestamp freshness validation
    - Automatic nonce expiry and cleanup
    """
    
    def __init__(
        self,
        crypto_core: CryptoCore,
        nonce_expiry_seconds: int = 300,
        max_nonce_cache: int = 100000
    ):
        """Initialize SecurityValidator.
        
        Args:
            crypto_core: CryptoCore instance for signature verification
            nonce_expiry_seconds: How long nonces are valid (default 5 minutes)
            max_nonce_cache: Maximum nonces to cache
        """
        self.crypto = crypto_core
        self.nonce_expiry_seconds = nonce_expiry_seconds
        self.max_nonce_cache = max_nonce_cache
        self.logger = logging.getLogger(__name__)
        
        # Nonce tracking
        self._seen_nonces: Set[str] = set()
        self._nonce_timestamps: deque = deque(maxlen=max_nonce_cache)
        
        # Statistics
        self._total_validations = 0
        self._valid_events = 0
        self._invalid_signatures = 0
        self._replay_attacks = 0
        self._expired_events = 0
    
    def verify_event(self, signed_event: SignedEvent) -> tuple[bool, str]:
        """Verify HMAC signature and check for replay attacks.
        
        Args:
            signed_event: SignedEvent to verify
            
        Returns:
            Tuple of (is_valid, reason)
        """
        self._total_validations += 1
        
        # Check timestamp freshness
        age_seconds = (datetime.now() - signed_event.timestamp).total_seconds()
        if age_seconds > self.nonce_expiry_seconds:
            self._expired_events += 1
            return False, f"Event expired (age: {age_seconds:.1f}s)"
        
        # Check for replay attack
        if self.is_replay_attack(signed_event.nonce, signed_event.timestamp):
            self._replay_attacks += 1
            self.logger.warning(f"Replay attack detected: nonce={signed_event.nonce}")
            return False, "Replay attack detected"
        
        # Verify HMAC signature
        event_dict = signed_event.event.to_dict()
        sign_data = f"{event_dict}|{signed_event.nonce}|{signed_event.timestamp.isoformat()}"
        
        is_valid = self.crypto.verify_hmac(sign_data.encode(), signed_event.signature)
        
        if is_valid:
            self._valid_events += 1
            # Add nonce to seen set
            self._add_nonce(signed_event.nonce, signed_event.timestamp)
            return True, "Valid signature"
        else:
            self._invalid_signatures += 1
            self.logger.warning(f"Invalid signature detected for event {signed_event.event.event_id}")
            return False, "Invalid signature"
    
    def is_replay_attack(self, nonce: str, timestamp: datetime) -> bool:
        """Check if event is a replay attack.
        
        Args:
            nonce: Nonce to check
            timestamp: Event timestamp
            
        Returns:
            True if replay attack detected, False otherwise
        """
        return nonce in self._seen_nonces
    
    def _add_nonce(self, nonce: str, timestamp: datetime) -> None:
        """Add nonce to seen set with timestamp.
        
        Args:
            nonce: Nonce to add
            timestamp: Timestamp of the nonce
        """
        self._seen_nonces.add(nonce)
        self._nonce_timestamps.append((nonce, timestamp))
        
        # Cleanup if cache is getting full
        if len(self._seen_nonces) > self.max_nonce_cache * 0.9:
            self.cleanup_old_nonces()
    
    def cleanup_old_nonces(self) -> int:
        """Remove expired nonces from cache.
        
        Returns:
            Number of nonces removed
        """
        current_time = datetime.now()
        cutoff_time = current_time.timestamp() - self.nonce_expiry_seconds
        
        removed_count = 0
        
        # Remove old nonces
        while self._nonce_timestamps:
            nonce, timestamp = self._nonce_timestamps[0]
            if timestamp.timestamp() < cutoff_time:
                self._nonce_timestamps.popleft()
                self._seen_nonces.discard(nonce)
                removed_count += 1
            else:
                break
        
        if removed_count > 0:
            self.logger.debug(f"Cleaned up {removed_count} expired nonces")
        
        return removed_count
    
    def get_stats(self) -> dict:
        """Get validation statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            "total_validations": self._total_validations,
            "valid_events": self._valid_events,
            "invalid_signatures": self._invalid_signatures,
            "replay_attacks": self._replay_attacks,
            "expired_events": self._expired_events,
            "nonce_cache_size": len(self._seen_nonces),
            "validation_success_rate": (
                self._valid_events / self._total_validations
                if self._total_validations > 0
                else 0.0
            )
        }
