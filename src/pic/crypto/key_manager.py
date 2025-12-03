"""Key manager for cryptographic key rotation and management."""

import os
import time
import logging
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime, timedelta

from pic.crypto import CryptoCore


class KeyManager:
    """Manages cryptographic keys with rotation support.
    
    Features:
    - Primary and backup key management
    - Automatic key rotation on schedule
    - Graceful key rotation (verify with both keys)
    - Secure key storage
    """
    
    def __init__(
        self,
        key_dir: str = "pic_keys",
        rotation_days: int = 30
    ):
        """Initialize KeyManager.
        
        Args:
            key_dir: Directory to store keys
            rotation_days: Days between key rotations
        """
        self.key_dir = Path(key_dir)
        self.key_dir.mkdir(parents=True, exist_ok=True)
        
        self.rotation_days = rotation_days
        self.logger = logging.getLogger(__name__)
        
        # Key paths
        self.primary_key_path = self.key_dir / "primary.key"
        self.backup_key_path = self.key_dir / "backup.key"
        self.rotation_log_path = self.key_dir / "rotation.log"
        
        # Load or generate keys
        self.primary_crypto = self._load_or_generate_key(self.primary_key_path, "primary")
        self.backup_crypto = self._load_or_generate_key(self.backup_key_path, "backup")
        
        # Statistics
        self._rotations = 0
        self._last_rotation = self._get_last_rotation_time()
    
    def _load_or_generate_key(self, key_path: Path, key_name: str) -> CryptoCore:
        """Load existing key or generate new one.
        
        Args:
            key_path: Path to key file
            key_name: Name of the key (for logging)
            
        Returns:
            CryptoCore instance with the key
        """
        if key_path.exists():
            self.logger.info(f"Loading {key_name} key from {key_path}")
            return CryptoCore(key_path=str(key_path))
        else:
            self.logger.info(f"Generating new {key_name} key at {key_path}")
            crypto = CryptoCore(key_path=str(key_path))
            return crypto
    
    def rotate_keys(self) -> None:
        """Rotate keys: backup becomes primary, generate new backup.
        
        Rotation process:
        1. Backup key becomes new primary key
        2. Generate new backup key
        3. Update key files
        4. Log rotation
        """
        self.logger.info("Starting key rotation...")
        
        # Step 1: Backup becomes primary
        # Copy backup key to primary location
        if self.backup_key_path.exists():
            # Read backup key
            with open(self.backup_key_path, 'rb') as f:
                backup_key_data = f.read()
            
            # Write to primary location
            with open(self.primary_key_path, 'wb') as f:
                f.write(backup_key_data)
            
            # Reload primary crypto
            self.primary_crypto = CryptoCore(key_path=str(self.primary_key_path))
            self.logger.info("✓ Backup key promoted to primary")
        
        # Step 2: Generate new backup
        # Remove old backup
        if self.backup_key_path.exists():
            self.backup_key_path.unlink()
        
        # Generate new backup
        self.backup_crypto = CryptoCore(key_path=str(self.backup_key_path))
        self.logger.info("✓ New backup key generated")
        
        # Step 3: Log rotation
        self._log_rotation()
        self._rotations += 1
        self._last_rotation = datetime.now()
        
        self.logger.info(f"✓ Key rotation complete (rotation #{self._rotations})")
    
    def should_rotate(self) -> bool:
        """Check if keys should be rotated.
        
        Returns:
            True if rotation is due
        """
        if self._last_rotation is None:
            return False
        
        days_since_rotation = (datetime.now() - self._last_rotation).days
        return days_since_rotation >= self.rotation_days
    
    def verify_with_any_key(self, data: bytes, signature: str) -> bool:
        """Verify signature with either primary or backup key.
        
        This supports graceful key rotation where some events may still
        be signed with the old key.
        
        Args:
            data: Data that was signed
            signature: HMAC signature to verify
            
        Returns:
            True if signature is valid with either key
        """
        # Try primary key first
        if self.primary_crypto.verify_hmac(data, signature):
            return True
        
        # Fall back to backup key
        if self.backup_crypto.verify_hmac(data, signature):
            self.logger.debug("Signature verified with backup key")
            return True
        
        return False
    
    def sign_with_primary(self, data: bytes) -> str:
        """Sign data with primary key.
        
        Args:
            data: Data to sign
            
        Returns:
            HMAC signature
        """
        return self.primary_crypto.sign_hmac(data)
    
    def get_primary_crypto(self) -> CryptoCore:
        """Get primary CryptoCore instance.
        
        Returns:
            Primary CryptoCore
        """
        return self.primary_crypto
    
    def get_backup_crypto(self) -> CryptoCore:
        """Get backup CryptoCore instance.
        
        Returns:
            Backup CryptoCore
        """
        return self.backup_crypto
    
    def _log_rotation(self) -> None:
        """Log key rotation to file."""
        with open(self.rotation_log_path, 'a') as f:
            timestamp = datetime.now().isoformat()
            f.write(f"{timestamp}: Key rotation #{self._rotations + 1}\n")
    
    def _get_last_rotation_time(self) -> Optional[datetime]:
        """Get timestamp of last rotation from log.
        
        Returns:
            Datetime of last rotation or None
        """
        if not self.rotation_log_path.exists():
            return None
        
        try:
            with open(self.rotation_log_path, 'r') as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1]
                    timestamp_str = last_line.split(':')[0]
                    return datetime.fromisoformat(timestamp_str)
        except Exception as e:
            self.logger.error(f"Error reading rotation log: {e}")
        
        return None
    
    def get_stats(self) -> dict:
        """Get key manager statistics.
        
        Returns:
            Dictionary with statistics
        """
        days_since_rotation = None
        if self._last_rotation:
            days_since_rotation = (datetime.now() - self._last_rotation).days
        
        return {
            "rotations": self._rotations,
            "last_rotation": self._last_rotation.isoformat() if self._last_rotation else None,
            "days_since_rotation": days_since_rotation,
            "rotation_due": self.should_rotate(),
            "rotation_interval_days": self.rotation_days
        }
