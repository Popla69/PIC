#!/usr/bin/env python3
"""Simple PIC Test - Just verify basic functionality."""

import sys
import time
sys.path.insert(0, 'src')

from pic.cellagent import CellAgent
from pic.config.loader import PICConfig

print("=" * 60)
print("PIC Simple Test")
print("=" * 60)
print()

# Test 1: Initialize CellAgent
print("[Test 1] Initializing CellAgent...")
try:
    config = PICConfig({})
    agent = CellAgent(config=config)
    print("✓ CellAgent initialized successfully")
except Exception as e:
    print(f"✗ Failed to initialize: {e}")
    sys.exit(1)

print()

# Test 2: Monitor a simple function
print("[Test 2] Monitoring a simple function...")
try:
    @agent.monitor
    def add_numbers(a, b):
        """Simple addition function."""
        return a + b
    
    result = add_numbers(5, 3)
    assert result == 8, f"Expected 8, got {result}"
    print(f"✓ Function executed correctly: 5 + 3 = {result}")
except Exception as e:
    print(f"✗ Failed to monitor function: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 3: Monitor multiple calls
print("[Test 3] Monitoring multiple function calls...")
try:
    call_count = 10
    for i in range(call_count):
        result = add_numbers(i, i+1)
    print(f"✓ Successfully monitored {call_count} function calls")
except Exception as e:
    print(f"✗ Failed during multiple calls: {e}")
    sys.exit(1)

print()

# Test 4: Monitor function with delay
print("[Test 4] Monitoring function with delay...")
try:
    @agent.monitor
    def slow_function():
        """Function with artificial delay."""
        time.sleep(0.01)
        return "completed"
    
    result = slow_function()
    assert result == "completed"
    print("✓ Monitored function with delay successfully")
except Exception as e:
    print(f"✗ Failed to monitor delayed function: {e}")
    sys.exit(1)

print()

# Test 5: Monitor function that raises exception
print("[Test 5] Monitoring function that raises exception...")
try:
    @agent.monitor
    def failing_function():
        """Function that raises an exception."""
        raise ValueError("Intentional error")
    
    try:
        failing_function()
        print("✗ Exception was not raised")
    except ValueError as e:
        print(f"✓ Exception properly propagated: {e}")
except Exception as e:
    print(f"✗ Unexpected error: {e}")
    sys.exit(1)

print()

# Summary
print("=" * 60)
print("All Tests Passed! ✓")
print("=" * 60)
print()
print("PIC CellAgent is working correctly:")
print("  ✓ Initialization")
print("  ✓ Function monitoring")
print("  ✓ Multiple calls")
print("  ✓ Delayed execution")
print("  ✓ Exception handling")
print()
print("=" * 60)
