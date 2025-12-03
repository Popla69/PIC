"""Secure transport layer for Brain-CellAgent communication.

Handles HMAC signing, signature verification, and replay attack protection.
"""

import uuid
import time
from datetime import datetime
from typing import Set, Optional
from collections import deque

from pic.crypto import CryptoCore
from pic.models.integration import SignedEvent, SignedDecision
from pic.models.events import TelemetryEvent
from pic.models.decision import Decision


class SecureTransport:
    """Secure transport layer for telemetry with HMAC signing and replay protection.
    
    Features:
    - HMAC-SHA256 signing of events
    - Nonce-based replay attack protection
    - Signature verification for decisions
    - Automatic nonce cleanup
    """
    
    def __init__(self, crypto_core: CryptoCore, nonce_cache_size: int = 10000):
        """Initialize SecureTransport.
        
        Args:
            crypto_core: CryptoCore instance for cryptographic operations
            nonce_cache_size: Maximum number of nonces to cache
        """
        self.crypto = crypto_core
        self._nonce_cache: Set[str] = set()
        self._nonce_cache_size = nonce_cache_size
        self._nonce_timestamps: deque = deque(maxlen=nonce_cache_size)
        
    def sign_event(self, event: TelemetryEvent) -> SignedEvent:
        """Sign telemetry event with HMAC and add nonce for replay protection.
        
        Args:
            event: TelemetryEvent to sign
            
        Returns:
            SignedEvent with signature and nonce
        """
        # Generate unique nonce
        nonce = str(uuid.uuid4())
        timestamp = datetime.now()
        
        # Create data to sign (event + nonce + timestamp)
        event_dict = event.to_dict()
        sign_data = f"{event_dict}|{nonce}|{timestamp.isoformat()}"
        
        # Compute HMAC signature
        signature = self.crypto.sign_hmac(sign_data.encode())
        
        return SignedEvent(
            event=event,
            signature=signature,
            nonce=nonce,
            timestamp=timestamp
        )
    
    def verify_event(self, signed_event: SignedEvent) -> bool:
        """Verify HMAC signature and check for replay attacks.
        
        Args:
            signed_event: SignedEvent to verify
            
        Returns:
            True if signature is valid and not a replay, False otherwise
        """
        # Check for replay attack
        if signed_event.nonce in self._nonce_cache:
            return False
        
        # Verify signature
        event_dict = signed_event.event.to_dict()
        sign_data = f"{event_dict}|{signed_event.nonce}|{signed_event.timestamp.isoformat()}"
        
        is_valid = self.crypto.verify_hmac(sign_data.encode(), signed_event.signature)
        
        if is_valid:
            # Add nonce to cache
            self._add_nonce(signed_event.nonce, signed_event.timestamp)
        
        return is_valid
    
    def sign_decision(self, decision: Decision) -> SignedDecision:
        """Sign decision with HMAC.
        
        Args:
            decision: Decision to sign
            
        Returns:
            SignedDecision with signature
        """
        timestamp = datetime.now()
        
        # Create data to sign
        sign_data = f"{decision.action}|{decision.reason}|{decision.confidence}|{timestamp.isoformat()}"
        
        # Compute HMAC signature
        signature = self.crypto.sign_hmac(sign_data.encode())
        
        return SignedDecision(
            decision=decision,
            signature=signature,
            timestamp=timestamp
        )
    
    def verify_decision(self, signed_decision: SignedDecision) -> bool:
        """Verify decision signature.
        
        Args:
            signed_decision: SignedDecision to verify
            
        Returns:
            True if signature is valid, False otherwise
        """
        decision = signed_decision.decision
        sign_data = f"{decision.action}|{decision.reason}|{decision.confidence}|{signed_decision.timestamp.isoformat()}"
        
        return self.crypto.verify_hmac(sign_data.encode(), signed_decision.signature)
    
    def _add_nonce(self, nonce: str, timestamp: datetime) -> None:
        """Add nonce to cache with timestamp.
        
        Args:
            nonce: Nonce to add
            timestamp: Timestamp of the nonce
        """
        # Add to cache
        self._nonce_cache.add(nonce)
        self._nonce_timestamps.append((nonce, timestamp))
        
        # Cleanup if cache is full
        if len(self._nonce_cache) > self._nonce_cache_size:
            self._cleanup_old_nonces()
    
    def _cleanup_old_nonces(self, max_age_seconds: int = 300) -> None:
        """Remove nonces older than max_age_seconds.
        
        Args:
            max_age_seconds: Maximum age of nonces to keep (default 5 minutes)
        """
        current_time = datetime.now()
        cutoff_time = current_time.timestamp() - max_age_seconds
        
        # Remove old nonces
        while self._nonce_timestamps:
            nonce, timestamp = self._nonce_timestamps[0]
            if timestamp.timestamp() < cutoff_time:
                self._nonce_timestamps.popleft()
                self._nonce_cache.discard(nonce)
            else:
                break
    
    def get_cache_stats(self) -> dict:
        """Get nonce cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        return {
            "nonce_cache_size": len(self._nonce_cache),
            "max_cache_size": self._nonce_cache_size,
            "cache_utilization": len(self._nonce_cache) / self._nonce_cache_size
        }
