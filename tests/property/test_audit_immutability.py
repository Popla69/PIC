"""Property tests for audit log immutability and HMAC signing.

Feature: pic-v1-immune-core
Property 21: Audit Log Immutability - Validates: Requirements 6.1
Property 56: Audit Log HMAC Signing - Validates: Requirements 18.5
"""

import tempfile
from datetime import datetime
from hypothesis import given, strategies as st, settings

from pic.storage.audit_store import AuditStore
from pic.models.events import AuditEvent
from pic.crypto import CryptoCore


@settings(deadline=None)
@given(
    event_type=st.sampled_from(["detection", "promotion", "rollback", "config_change"]),
    actor=st.sampled_from(["system", "operator", "admin"]),
    action=st.sampled_from(["allow", "block", "promote", "reject"]),
    result=st.sampled_from(["success", "failure"]),
)
def test_audit_log_immutability(event_type, actor, action, result):
    """
    Property 21: Audit Log Immutability
    
    For any detection or remediation decision, an audit log entry shall be created
    that cannot be modified or deleted (append-only).
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create AuditStore
        crypto = CryptoCore(f"{tmpdir}/key")
        store = AuditStore(f"{tmpdir}/audit.log", crypto)
        
        # Create and log event
        event = AuditEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            actor=actor,
            action=action,
            result=result,
            signature=""  # Will be set by store
        )
        
        store.log_event(event)
        
        # Verify: Event is in log
        events = store.export_logs()
        assert len(events) == 1
        
        # Verify: Event has signature
        logged_event = events[0]
        assert logged_event.signature != ""
        assert len(logged_event.signature) == 64  # SHA-256 hex
        
        # Verify: Signature is valid
        assert store.verify_log_integrity() is True
        
        # Verify: Log is append-only (no modification API exists)
        # The AuditStore class has no methods to modify or delete entries
        assert not hasattr(store, "delete_event")
        assert not hasattr(store, "update_event")
        assert not hasattr(store, "modify_event")


@given(
    event_count=st.integers(min_value=1, max_value=10),
)
def test_audit_log_hmac_signing(event_count):
    """
    Property 56: Audit Log HMAC Signing
    
    For any audit log entry, the entry shall include an HMAC-SHA256 signature
    computed over the entry content and timestamp.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create AuditStore
        crypto = CryptoCore(f"{tmpdir}/key")
        store = AuditStore(f"{tmpdir}/audit.log", crypto)
        
        # Log multiple events
        for i in range(event_count):
            event = AuditEvent(
                timestamp=datetime.now(),
                event_type="detection",
                actor="system",
                action="allow",
                result="success",
                signature=""
            )
            store.log_event(event)
        
        # Verify: All events have HMAC signatures
        events = store.export_logs()
        assert len(events) == event_count
        
        for event in events:
            # Verify signature exists
            assert event.signature != ""
            assert len(event.signature) == 64  # HMAC-SHA256 hex
            
            # Verify signature is valid
            signable_data = event.get_signable_data()
            assert crypto.verify_signature(signable_data, event.signature) is True
        
        # Verify: Overall log integrity
        assert store.verify_log_integrity() is True
