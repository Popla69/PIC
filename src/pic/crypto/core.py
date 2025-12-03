"""Centralized cryptographic operations for PIC."""

import hmac
import hashlib
import secrets
from pathlib import Path
from typing import Optional


class CryptoCore:
    """Centralized cryptographic operations.
    
    Provides:
    - HMAC-SHA256 signing for audit logs
    - SHA-256 hashing for PII and signatures
    - Key generation and management
    - Signature verification
    """
    
    def __init__(self, key_path: str):
        """Initialize CryptoCore with key storage path.
        
        Args:
            key_path: Path to store/load cryptographic keys
        """
        self.key_path = Path(key_path)
        self._signing_key: Optional[bytes] = None
        self._load_or_generate_key()
    
    def _load_or_generate_key(self) -> None:
        """Load existing key or generate new one."""
        if self.key_path.exists():
            with open(self.key_path, "rb") as f:
                self._signing_key = f.read()
        else:
            # Generate new 256-bit key
            self._signing_key = secrets.token_bytes(32)
            
            # Ensure directory exists
            self.key_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save key with restrictive permissions
            with open(self.key_path, "wb") as f:
                f.write(self._signing_key)
            
            # Set file permissions to 600 (owner read/write only)
            self.key_path.chmod(0o600)
    
    def hmac_sign(self, data: bytes) -> str:
        """Generate HMAC-SHA256 signature for data.
        
        Args:
            data: Data to sign
            
        Returns:
            Hex-encoded HMAC signature
            
        Example:
            >>> crypto = CryptoCore("/path/to/key")
            >>> signature = crypto.hmac_sign(b"audit log entry")
            >>> signature
            'a1b2c3d4...'
        """
        if self._signing_key is None:
            raise RuntimeError("Signing key not initialized")
        
        signature = hmac.new(
            self._signing_key,
            data,
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def verify_signature(self, data: bytes, signature: str) -> bool:
        """Verify HMAC-SHA256 signature.
        
        Args:
            data: Original data
            signature: Hex-encoded signature to verify
            
        Returns:
            True if signature is valid, False otherwise
            
        Example:
            >>> crypto = CryptoCore("/path/to/key")
            >>> data = b"audit log entry"
            >>> sig = crypto.hmac_sign(data)
            >>> crypto.verify_signature(data, sig)
            True
        """
        if self._signing_key is None:
            raise RuntimeError("Signing key not initialized")
        
        expected_signature = self.hmac_sign(data)
        
        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(signature, expected_signature)
    
    @staticmethod
    def sha256_hash(data: bytes) -> str:
        """Generate SHA-256 hash of data.
        
        Args:
            data: Data to hash
            
        Returns:
            Hex-encoded SHA-256 hash
            
        Example:
            >>> CryptoCore.sha256_hash(b"sensitive data")
            'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
        """
        return hashlib.sha256(data).hexdigest()
    
    @staticmethod
    def sha256_hash_string(text: str) -> str:
        """Generate SHA-256 hash of string.
        
        Args:
            text: String to hash
            
        Returns:
            Hex-encoded SHA-256 hash
        """
        return CryptoCore.sha256_hash(text.encode("utf-8"))
    
    def rotate_key(self, new_key_path: Optional[str] = None) -> None:
        """Rotate signing key.
        
        Generates a new key and saves it. The old key is kept for verification
        of existing signatures.
        
        Args:
            new_key_path: Optional path for new key (default: append .new to current path)
        """
        if new_key_path is None:
            new_key_path = str(self.key_path) + ".new"
        
        new_key_path_obj = Path(new_key_path)
        
        # Generate new key
        new_key = secrets.token_bytes(32)
        
        # Save new key
        new_key_path_obj.parent.mkdir(parents=True, exist_ok=True)
        with open(new_key_path_obj, "wb") as f:
            f.write(new_key)
        new_key_path_obj.chmod(0o600)
        
        # Backup old key
        backup_path = Path(str(self.key_path) + ".old")
        if self.key_path.exists():
            self.key_path.rename(backup_path)
        
        # Move new key to primary location
        new_key_path_obj.rename(self.key_path)
        
        # Update in-memory key
        self._signing_key = new_key
    
    def get_key_fingerprint(self) -> str:
        """Get fingerprint of current signing key.
        
        Returns:
            SHA-256 hash of the signing key (for identification)
        """
        if self._signing_key is None:
            raise RuntimeError("Signing key not initialized")
        
        return self.sha256_hash(self._signing_key)

    # Aliases for compatibility
    def sign_hmac(self, data: bytes) -> str:
        """Alias for hmac_sign for compatibility."""
        return self.hmac_sign(data)
    
    def verify_hmac(self, data: bytes, signature: str) -> bool:
        """Alias for verify_signature for compatibility."""
        return self.verify_signature(data, signature)
