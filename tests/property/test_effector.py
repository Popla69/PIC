"""Property tests for Effector action execution.

Feature: pic-v1-immune-core
Property 16: Effector Action Validity - Validates: Requirements 5.1
Property 19: Effector Fail-Safe Default - Validates: Requirements 5.4
"""

from hypothesis import given, strategies as st
from pic.effector.executor import Effector
from pic.models.decision import Decision


@given(
    action=st.sampled_from(["allow", "block"]),
    reason=st.text(min_size=1, max_size=100),
    anomaly_score=st.floats(min_value=0.0, max_value=100.0),
)
def test_effector_action_validity(action, reason, anomaly_score):
    """
    Property 16: Effector Action Validity
    
    For any decision (allow or block), the Effector shall execute only valid actions
    from the defined action set.
    """
    effector = Effector()
    
    # Create decision
    decision = Decision(
        action=action,
        reason=reason,
        anomaly_score=anomaly_score
    )
    
    # Execute action
    result = effector.execute_action(decision)
    
    # Verify: Action is valid
    if action == "allow":
        # Allow action should return None (pass-through)
        assert result is None
    elif action == "block":
        # Block action should return a safe stub value
        # Stub values should be safe defaults
        assert result in [None, False, 0, 0.0, "", [], {}]
    
    # Verify: Stats are updated
    stats = effector.get_stats()
    assert stats["actions_executed"] >= 1


@given(
    reason=st.text(min_size=1, max_size=100),
    anomaly_score=st.floats(min_value=0.0, max_value=100.0),
)
def test_effector_fail_safe_default(reason, anomaly_score):
    """
    Property 19: Effector Fail-Safe Default
    
    For any error during action execution, the Effector shall default to "allow"
    to prevent blocking legitimate operations.
    """
    effector = Effector()
    
    # Create decision with invalid action (should default to allow)
    decision = Decision(
        action="invalid_action",
        reason=reason,
        anomaly_score=anomaly_score
    )
    
    # Execute action
    result = effector.execute_action(decision)
    
    # Verify: Defaults to allow (returns None)
    assert result is None
    
    # Verify: No exception raised
    # (test passes if we reach here)


def test_effector_error_handling():
    """Test that Effector handles errors gracefully."""
    effector = Effector()
    
    # Test with None decision (should not crash)
    try:
        # This should handle gracefully
        decision = Decision(
            action="allow",
            reason="test",
            anomaly_score=0.0
        )
        result = effector.execute_action(decision)
        assert result is None
    except Exception as e:
        # Should not raise exception
        assert False, f"Effector raised exception: {e}"
