"""Property test for signature hash storage.

Feature: pic-v1-immune-core, Property 24: Signature Hash Storage
Validates: Requirements 7.1, 14.1
"""

import tempfile
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, settings

from pic.storage.state_store import StateStore
from pic.models.detector import Detector
from pic.crypto import CryptoCore


@settings(deadline=None)
@given(
    function_name=st.text(min_size=1, max_size=100),
    threshold=st.floats(min_value=0.0, max_value=100.0),
)
def test_signature_hash_storage(function_name, threshold):
    """
    Property 24: Signature Hash Storage
    
    For any promoted detection candidate, the Memory Bank shall store a SHA-256 hash
    of the threat pattern (not the raw pattern).
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create StateStore
        store = StateStore(f"{tmpdir}/test.db")
        
        # Create detector with hashed signature
        threat_pattern = f"pattern_for_{function_name}"
        signature_hash = CryptoCore.sha256_hash_string(threat_pattern)
        
        detector = Detector(
            id=f"det-{function_name}",
            function_name=function_name,
            threshold=threshold,
            signature_hash=signature_hash,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=90),
            is_active=True
        )
        
        # Store detector
        store.store_detector(detector)
        
        # Retrieve detector
        detectors = store.get_active_detectors(function_name)
        
        # Verify: Signature is stored as hash (64 hex chars for SHA-256)
        assert len(detectors) > 0
        retrieved = detectors[0]
        assert len(retrieved.signature_hash) == 64  # SHA-256 hex length
        assert retrieved.signature_hash == signature_hash
        
        # Verify: Raw pattern is NOT stored (only hash)
        assert threat_pattern not in retrieved.signature_hash
        
        store.close()
