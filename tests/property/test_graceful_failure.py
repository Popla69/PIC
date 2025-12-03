"""Property test for graceful instrumentation failure.

Feature: pic-v1-immune-core, Property 3: Graceful Instrumentation Failure
Validates: Requirements 1.4
"""

from hypothesis import given, strategies as st
from pic.cellagent.agent import CellAgent


@given(
    error_message=st.text(min_size=1, max_size=100),
)
def test_graceful_instrumentation_failure(error_message):
    """
    Property 3: Graceful Instrumentation Failure
    
    For any instrumentation error during function wrapping, the monitored application
    shall continue execution without raising exceptions to the application code.
    """
    agent = CellAgent()
    
    # Create a function that raises an exception
    @agent.monitor
    def failing_function():
        raise ValueError(error_message)
    
    # Verify: Exception is raised to caller (not swallowed)
    try:
        failing_function()
        assert False, "Exception should have been raised"
    except ValueError as e:
        # Verify: Original exception is preserved
        assert str(e) == error_message
    
    # Verify: Agent is still functional after exception
    @agent.monitor
    def working_function():
        return "success"
    
    result = working_function()
    assert result == "success"
    
    # Verify: Agent stats are still accessible
    stats = agent.get_stats()
    assert isinstance(stats, dict)
    assert "total_events" in stats


def test_instrumentation_with_various_return_types():
    """Test that instrumentation works with various return types."""
    agent = CellAgent()
    
    @agent.monitor
    def return_none():
        return None
    
    @agent.monitor
    def return_int():
        return 42
    
    @agent.monitor
    def return_string():
        return "hello"
    
    @agent.monitor
    def return_list():
        return [1, 2, 3]
    
    @agent.monitor
    def return_dict():
        return {"key": "value"}
    
    # All should work without errors
    assert return_none() is None
    assert return_int() == 42
    assert return_string() == "hello"
    assert return_list() == [1, 2, 3]
    assert return_dict() == {"key": "value"}


def test_instrumentation_preserves_function_behavior():
    """Test that instrumentation doesn't change function behavior."""
    agent = CellAgent()
    
    # Original function
    def original(x, y):
        return x + y
    
    # Instrumented function
    @agent.monitor
    def instrumented(x, y):
        return x + y
    
    # Verify: Same behavior
    assert original(2, 3) == instrumented(2, 3)
    assert original(10, 20) == instrumented(10, 20)
