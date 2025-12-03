#!/usr/bin/env python3
"""Quick test for integration models."""

import sys
sys.path.insert(0, 'src')

from datetime import datetime
from pic.models.integration import SignedEvent, SignedDecision, BackpressureSignal, RateLimitStatus
from pic.models.events import TelemetryEvent
from pic.models.decision import Decision

print("Testing Integration Models...")
print("=" * 60)

# Test SignedEvent
print("\n[1/4] Testing SignedEvent...")
event = TelemetryEvent(
    timestamp=datetime.now(),
    event_id="test-123",
    process_id=12345,
    thread_id=67890,
    function_name="test_func",
    module_name="test_module",
    duration_ms=10.5,
    args_metadata={"arg1": "hash123"},
    resource_tags={"io": 0},
    redaction_applied=True,
    sampling_rate=1.0
)

signed_event = SignedEvent(
    event=event,
    signature="test_signature_abc123",
    nonce="nonce-uuid-123",
    timestamp=datetime.now()
)

# Test serialization
event_dict = signed_event.to_dict()
print(f"  ✓ Serialized to dict: {len(event_dict)} fields")

# Test deserialization
restored_event = SignedEvent.from_dict(event_dict)
print(f"  ✓ Deserialized from dict")
print(f"  ✓ Signature: {restored_event.signature}")
print(f"  ✓ Nonce: {restored_event.nonce}")

# Test JSON
json_str = signed_event.to_json()
print(f"  ✓ Serialized to JSON: {len(json_str)} bytes")

restored_from_json = SignedEvent.from_json(json_str)
print(f"  ✓ Deserialized from JSON")

# Test SignedDecision
print("\n[2/4] Testing SignedDecision...")
decision = Decision.allow("Normal behavior", 0.1)
signed_decision = SignedDecision(
    decision=decision,
    signature="decision_signature_xyz789",
    timestamp=datetime.now()
)

decision_dict = signed_decision.to_dict()
print(f"  ✓ Serialized to dict: {len(decision_dict)} fields")

restored_decision = SignedDecision.from_dict(decision_dict)
print(f"  ✓ Deserialized from dict")
print(f"  ✓ Action: {restored_decision.decision.action}")
print(f"  ✓ Signature: {restored_decision.signature}")

# Test BackpressureSignal
print("\n[3/4] Testing BackpressureSignal...")
signal = BackpressureSignal(
    active=True,
    recommended_rate=0.5,
    queue_utilization=0.85,
    reason="Queue near capacity"
)

signal_dict = signal.to_dict()
print(f"  ✓ Serialized to dict: {len(signal_dict)} fields")

restored_signal = BackpressureSignal.from_dict(signal_dict)
print(f"  ✓ Deserialized from dict")
print(f"  ✓ Active: {restored_signal.active}")
print(f"  ✓ Recommended rate: {restored_signal.recommended_rate}")
print(f"  ✓ Queue utilization: {restored_signal.queue_utilization}")

# Test RateLimitStatus
print("\n[4/4] Testing RateLimitStatus...")
status = RateLimitStatus(
    global_rate=5000,
    throttled_functions=["func1", "func2"],
    dropped_events=42,
    throttling_active=True
)

status_dict = status.to_dict()
print(f"  ✓ Serialized to dict: {len(status_dict)} fields")

restored_status = RateLimitStatus.from_dict(status_dict)
print(f"  ✓ Deserialized from dict")
print(f"  ✓ Global rate: {restored_status.global_rate} events/sec")
print(f"  ✓ Throttled functions: {len(restored_status.throttled_functions)}")
print(f"  ✓ Dropped events: {restored_status.dropped_events}")

print("\n" + "=" * 60)
print("✓ All Integration Models Working!")
print("=" * 60)
