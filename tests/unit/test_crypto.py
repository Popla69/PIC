"""Unit tests for CryptoCore."""

import tempfile
import pytest
from pathlib import Path

from pic.crypto import CryptoCore


def test_key_generation():
    """Test automatic key generation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        key_path = Path(tmpdir) / "test.key"
        
        crypto = CryptoCore(str(key_path))
        
        assert key_path.exists()
        assert key_path.stat().st_size == 32  # 256 bits


def test_key_loading():
    """Test loading existing key."""
    with tempfile.TemporaryDirectory() as tmpdir:
        key_path = Path(tmpdir) / "test.key"
        
        # Create first instance
        crypto1 = CryptoCore(str(key_path))
        fingerprint1 = crypto1.get_key_fingerprint()
        
        # Create second instance (should load same key)
        crypto2 = CryptoCore(str(key_path))
        fingerprint2 = crypto2.get_key_fingerprint()
        
        assert fingerprint1 == fingerprint2


def test_hmac_signing():
    """Test HMAC-SHA256 signing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        key_path = Path(tmpdir) / "test.key"
        crypto = CryptoCore(str(key_path))
        
        data = b"test audit log entry"
        signature = crypto.hmac_sign(data)
        
        assert isinstance(signature, str)
        assert len(signature) == 64  # SHA-256 hex = 64 chars


def test_signature_verification():
    """Test signature verification."""
    with tempfile.TemporaryDirectory() as tmpdir:
        key_path = Path(tmpdir) / "test.key"
        crypto = CryptoCore(str(key_path))
        
        data = b"test audit log entry"
        signature = crypto.hmac_sign(data)
        
        # Valid signature
        assert crypto.verify_signature(data, signature) is True
        
        # Invalid signature
        assert crypto.verify_signature(data, "invalid_signature") is False
        
        # Modified data
        assert crypto.verify_signature(b"modified data", signature) is False


def test_sha256_hash():
    """Test SHA-256 hashing."""
    data = b"test data"
    hash1 = CryptoCore.sha256_hash(data)
    hash2 = CryptoCore.sha256_hash(data)
    
    assert isinstance(hash1, str)
    assert len(hash1) == 64  # SHA-256 hex = 64 chars
    assert hash1 == hash2  # Deterministic


def test_sha256_hash_string():
    """Test SHA-256 hashing of strings."""
    text = "test string"
    hash1 = CryptoCore.sha256_hash_string(text)
    hash2 = CryptoCore.sha256_hash_string(text)
    
    assert isinstance(hash1, str)
    assert len(hash1) == 64
    assert hash1 == hash2


def test_key_rotation():
    """Test key rotation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        key_path = Path(tmpdir) / "test.key"
        crypto = CryptoCore(str(key_path))
        
        # Get original fingerprint
        original_fingerprint = crypto.get_key_fingerprint()
        
        # Sign data with original key
        data = b"test data"
        original_signature = crypto.hmac_sign(data)
        
        # Rotate key
        crypto.rotate_key()
        
        # New fingerprint should be different
        new_fingerprint = crypto.get_key_fingerprint()
        assert new_fingerprint != original_fingerprint
        
        # Old signature should not verify with new key
        assert crypto.verify_signature(data, original_signature) is False
        
        # New signature should work
        new_signature = crypto.hmac_sign(data)
        assert crypto.verify_signature(data, new_signature) is True
        
        # Old key should be backed up
        backup_path = Path(str(key_path) + ".old")
        assert backup_path.exists()


def test_hash_consistency():
    """Test that hashing is consistent."""
    data = b"consistent data"
    
    hash1 = CryptoCore.sha256_hash(data)
    hash2 = CryptoCore.sha256_hash(data)
    hash3 = CryptoCore.sha256_hash(data)
    
    assert hash1 == hash2 == hash3
