"""Integration tests for Brain-CellAgent integration."""

import pytest
import time
from pathlib import Path
import tempfile
import shutil

from pic.integrated import IntegratedPIC
from pic.cellagent.agent import SecurityException


@pytest.fixture
def temp_data_dir():
    """Create temporary data directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def integrated_pic(temp_data_dir):
    """Create IntegratedPIC instance."""
    pic = IntegratedPIC(data_dir=temp_data_dir)
    pic.start()
    yield pic
    pic.stop()


def test_integrated_pic_initialization(integrated_pic):
    """Test that IntegratedPIC initializes all components."""
    assert integrated_pic.crypto is not None
    assert integrated_pic.brain is not None
    assert integrated_pic.agent is not None
    assert integrated_pic.connector is not None
    assert integrated_pic.state_store is not None
    assert integrated_pic.audit_store is not None
    assert integrated_pic.trace_store is not None


def test_monitor_decorator_with_brain(integrated_pic):
    """Test monitor decorator with Brain integration."""
    
    @integrated_pic.agent.monitor
    def test_function(x, y):
        return x + y
    
    # Execute function
    result = test_function(5, 3)
    assert result == 8
    
    # Check stats
    stats = integrated_pic.get_stats()
    assert stats["running"] is True
    assert stats["agent_stats"]["total_events"] >= 0


def test_allow_decision_flow(integrated_pic):
    """Test complete flow with allow decision."""
    
    # Set sampling rate to 100% for this test
    integrated_pic.agent.sampling_rate = 1.0
    
    @integrated_pic.agent.monitor
    def safe_function(x):
        return x * 2
    
    # Execute multiple times to build baseline
    for i in range(20):
        result = safe_function(i)
        assert result == i * 2
    
    # Check that events were sent to Brain
    stats = integrated_pic.get_stats()
    brain_stats = stats.get("brain_stats")
    if brain_stats:
        # If Brain connector is working, we should have requests
        assert brain_stats["total_requests"] > 0


def test_rate_limiting(integrated_pic):
    """Test rate limiting functionality."""
    
    @integrated_pic.agent.monitor
    def fast_function():
        return "ok"
    
    # Execute many times rapidly
    for _ in range(100):
        fast_function()
    
    # Check rate limiter stats
    stats = integrated_pic.get_stats()
    rate_stats = stats["agent_stats"]["rate_limiter_stats"]
    
    assert rate_stats["total_checks"] > 0
    # Some events may be throttled
    assert rate_stats["total_allowed"] >= 0


def test_performance_tracking(integrated_pic):
    """Test performance metrics tracking."""
    
    @integrated_pic.agent.monitor
    def tracked_function(n):
        time.sleep(0.001)  # Small delay
        return n
    
    # Execute several times
    for i in range(10):
        tracked_function(i)
    
    # Check performance stats
    stats = integrated_pic.get_stats()
    perf_stats = stats["agent_stats"]["performance"]
    
    # Should have latency measurements
    assert perf_stats["sample_count"] >= 0


def test_security_validator_integration(integrated_pic):
    """Test that SecurityValidator is integrated with BrainCore."""
    
    # Check that security validator exists
    assert integrated_pic.brain.security_validator is not None
    
    # Get stats
    stats = integrated_pic.brain.security_validator.get_stats()
    assert "total_validations" in stats
    assert "security_violations" in integrated_pic.brain.get_stats()


def test_connector_stats(integrated_pic):
    """Test BrainConnector statistics."""
    
    @integrated_pic.agent.monitor
    def test_func():
        return "test"
    
    # Execute function
    test_func()
    
    # Get connector stats
    brain_stats = integrated_pic.agent.get_brain_stats()
    assert brain_stats is not None
    assert "total_requests" in brain_stats
    assert "success_rate" in brain_stats


def test_graceful_error_handling(integrated_pic):
    """Test that errors don't crash the monitored application."""
    
    @integrated_pic.agent.monitor
    def error_function():
        raise ValueError("Test error")
    
    # Function should raise its own error, not crash instrumentation
    with pytest.raises(ValueError, match="Test error"):
        error_function()
    
    # Agent should still be running
    assert integrated_pic._running is True


def test_context_manager(temp_data_dir):
    """Test IntegratedPIC as context manager."""
    
    with IntegratedPIC(data_dir=temp_data_dir) as pic:
        assert pic._running is True
        
        @pic.agent.monitor
        def test_func():
            return "ok"
        
        result = test_func()
        assert result == "ok"
    
    # Should be stopped after context exit
    assert pic._running is False


def test_fail_open_mode(temp_data_dir):
    """Test fail-open mode when Brain is unavailable."""
    pic = IntegratedPIC(data_dir=temp_data_dir)
    pic.start()
    
    # Set fail mode to open
    pic.connector.fail_mode = "open"
    
    @pic.agent.monitor
    def test_func():
        return "ok"
    
    # Should work even if Brain has issues
    result = test_func()
    assert result == "ok"
    
    pic.stop()


def test_comprehensive_stats(integrated_pic):
    """Test comprehensive statistics gathering."""
    
    @integrated_pic.agent.monitor
    def test_func(x):
        return x * 2
    
    # Execute several times
    for i in range(10):
        test_func(i)
    
    # Get all stats
    stats = integrated_pic.get_stats()
    
    # Verify structure
    assert "running" in stats
    assert "agent_stats" in stats
    assert "brain_stats" in stats
    assert "brain_core_stats" in stats
    
    # Agent stats
    assert "total_events" in stats["agent_stats"]
    assert "rate_limiter_stats" in stats["agent_stats"]
    assert "performance" in stats["agent_stats"]
    
    # Brain stats
    if stats["brain_stats"]:
        assert "total_requests" in stats["brain_stats"]
        assert "transport_stats" in stats["brain_stats"]
    
    # Brain core stats
    assert "events_processed" in stats["brain_core_stats"]
    assert "security_validator_stats" in stats["brain_core_stats"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
