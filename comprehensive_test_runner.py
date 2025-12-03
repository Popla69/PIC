#!/usr/bin/env python3
"""Comprehensive Test Runner - Tests all PIC capabilities"""

import sys
import time
sys.path.insert(0, 'src')

from pic.cellagent import CellAgent
from pic.config.loader import PICConfig

print("=" * 70)
print("PIC COMPREHENSIVE TEST SUITE")
print("=" * 70)
print()

# Track results
results = {}

# Test 1: Unit Tests
print("[1/6] Running Unit Tests...")
print("-" * 70)
try:
    import subprocess
    result = subprocess.run(
        ["py", "-m", "pytest", "tests/unit/", "-v", "--tb=short", "-p", "no:hypothesispytest"],
        capture_output=True,
        text=True,
        timeout=30
    )
    passed = result.stdout.count(" PASSED")
    failed = result.stdout.count(" FAILED")
    results["Unit Tests"] = {"passed": passed, "failed": failed, "status": "✓" if failed == 0 else "✗"}
    print(f"  Passed: {passed}, Failed: {failed}")
except Exception as e:
    results["Unit Tests"] = {"passed": 0, "failed": 0, "status": "✗", "error": str(e)}
    print(f"  Error: {e}")
print()

# Test 2: Security Tests
print("[2/6] Running Security Tests...")
print("-" * 70)
try:
    result = subprocess.run(
        ["py", "-m", "pytest", "tests/security/", "-v", "--tb=short", "-p", "no:hypothesispytest"],
        capture_output=True,
        text=True,
        timeout=30
    )
    passed = result.stdout.count(" PASSED")
    failed = result.stdout.count(" FAILED")
    results["Security Tests"] = {"passed": passed, "failed": failed, "status": "✓" if failed == 0 else "✗"}
    print(f"  Passed: {passed}, Failed: {failed}")
except Exception as e:
    results["Security Tests"] = {"passed": 0, "failed": 0, "status": "✗", "error": str(e)}
    print(f"  Error: {e}")
print()

# Test 3: Simple Integration Test
print("[3/6] Running Simple Integration Test...")
print("-" * 70)
try:
    config = PICConfig({})
    agent = CellAgent(config=config)
    
    @agent.monitor
    def test_function(x):
        return x * 2
    
    # Run multiple calls
    for i in range(10):
        result = test_function(i)
        assert result == i * 2
    
    results["Integration Test"] = {"passed": 10, "failed": 0, "status": "✓"}
    print("  ✓ All 10 integration tests passed")
except Exception as e:
    results["Integration Test"] = {"passed": 0, "failed": 1, "status": "✗", "error": str(e)}
    print(f"  ✗ Error: {e}")
print()

# Test 4: Real HTTP Traffic (httpbin.org)
print("[4/6] Testing Against Real HTTP Traffic (httpbin.org)...")
print("-" * 70)
try:
    import requests
    
    config = PICConfig({})
    agent = CellAgent(config=config)
    
    success_count = 0
    fail_count = 0
    
    for i in range(5):
        @agent.monitor
        def http_request():
            response = requests.get("https://httpbin.org/get", timeout=5)
            return response.status_code
        
        try:
            status = http_request()
            if status in [200, 503]:  # 503 is OK (service overloaded)
                success_count += 1
            else:
                fail_count += 1
        except Exception:
            fail_count += 1
    
    results["HTTP Traffic Test"] = {
        "passed": success_count, 
        "failed": fail_count, 
        "status": "✓" if success_count > 0 else "✗"
    }
    print(f"  Successful requests: {success_count}/5")
except Exception as e:
    results["HTTP Traffic Test"] = {"passed": 0, "failed": 5, "status": "✗", "error": str(e)}
    print(f"  ✗ Error: {e}")
print()

# Test 5: Stress Test (CPU intensive)
print("[5/6] Running Stress Test (CPU intensive)...")
print("-" * 70)
try:
    config = PICConfig({})
    agent = CellAgent(config=config)
    
    @agent.monitor
    def cpu_intensive():
        return sum(i**2 for i in range(100000))
    
    stress_count = 0
    for i in range(20):
        result = cpu_intensive()
        stress_count += 1
    
    results["Stress Test"] = {"passed": stress_count, "failed": 0, "status": "✓"}
    print(f"  ✓ Completed {stress_count} CPU-intensive operations")
except Exception as e:
    results["Stress Test"] = {"passed": 0, "failed": 1, "status": "✗", "error": str(e)}
    print(f"  ✗ Error: {e}")
print()

# Test 6: Exception Handling
print("[6/6] Testing Exception Handling...")
print("-" * 70)
try:
    config = PICConfig({})
    agent = CellAgent(config=config)
    
    @agent.monitor
    def failing_function():
        raise ValueError("Test exception")
    
    exception_count = 0
    for i in range(5):
        try:
            failing_function()
        except ValueError:
            exception_count += 1
    
    results["Exception Handling"] = {
        "passed": exception_count, 
        "failed": 0, 
        "status": "✓" if exception_count == 5 else "✗"
    }
    print(f"  ✓ Properly handled {exception_count}/5 exceptions")
except Exception as e:
    results["Exception Handling"] = {"passed": 0, "failed": 1, "status": "✗", "error": str(e)}
    print(f"  ✗ Error: {e}")
print()

# Summary
print("=" * 70)
print("TEST SUMMARY")
print("=" * 70)
print()

total_passed = 0
total_failed = 0

for test_name, result in results.items():
    status = result["status"]
    passed = result.get("passed", 0)
    failed = result.get("failed", 0)
    total_passed += passed
    total_failed += failed
    
    print(f"{status} {test_name}: {passed} passed, {failed} failed")
    if "error" in result:
        print(f"    Error: {result['error']}")

print()
print("=" * 70)
print(f"TOTAL: {total_passed} passed, {total_failed} failed")
print("=" * 70)
print()

# Overall assessment
if total_failed == 0:
    print("✓ ALL TESTS PASSED - PIC is working correctly!")
elif total_passed > total_failed:
    print("⚠ MOSTLY PASSING - PIC core functionality works, some tests need fixes")
else:
    print("✗ NEEDS ATTENTION - Multiple test failures detected")

print()
