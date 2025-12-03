"""Automated Overnight Security Test Runner for PIC v1

This script runs comprehensive security tests overnight and generates a detailed report.
All tests are safe and non-destructive.
"""

import subprocess
import time
import json
from datetime import datetime
from pathlib import Path


def run_test_suite(name, command, log_file):
    """Run a test suite and log results."""
    print(f"\n{'='*80}")
    print(f"Running: {name}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout per suite
        )
        
        duration = time.time() - start_time
        
        # Write output to log
        with open(log_file, 'w') as f:
            f.write(f"Test Suite: {name}\n")
            f.write(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Duration: {duration:.2f} seconds\n")
            f.write(f"Exit Code: {result.returncode}\n")
            f.write(f"\n{'='*80}\n")
            f.write("STDOUT:\n")
            f.write(result.stdout)
            f.write(f"\n{'='*80}\n")
            f.write("STDERR:\n")
            f.write(result.stderr)
        
        success = result.returncode == 0
        print(f"✅ PASSED" if success else f"❌ FAILED (exit code: {result.returncode})")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Log: {log_file}")
        
        return {
            "name": name,
            "success": success,
            "duration": duration,
            "exit_code": result.returncode,
            "log_file": str(log_file)
        }
        
    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        print(f"⏱️ TIMEOUT after {duration:.2f} seconds")
        return {
            "name": name,
            "success": False,
            "duration": duration,
            "exit_code": -1,
            "error": "Timeout"
        }
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ ERROR: {e}")
        return {
            "name": name,
            "success": False,
            "duration": duration,
            "exit_code": -1,
            "error": str(e)
        }


def main():
    """Run all overnight tests."""
    print("=" * 80)
    print("PIC v1 OVERNIGHT SECURITY TEST SUITE")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    print("This will run comprehensive security tests covering:")
    print("  1. Static Code Injection Tests")
    print("  2. Dynamic Behavior Simulation")
    print("  3. Network Defense Tests")
    print("  4. File System Immunity Tests")
    print("  5. Self-Healing & Regeneration Tests")
    print("  6. Stress & Overload Resistance")
    print("  7. Zero-Day Pattern Testing")
    print("  8. Red Team Logic Testing")
    print("  9. PIC Personality & Decision-Making Testing")
    print()
    print("All tests are SAFE and non-destructive.")
    print("=" * 80)
    print()
    
    # Create logs directory
    logs_dir = Path("test_logs")
    logs_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Define test suites
    test_suites = [
        {
            "name": "1. Unit Tests",
            "command": "pytest tests/unit/ -v --tb=short",
            "log": logs_dir / f"{timestamp}_unit_tests.log"
        },
        {
            "name": "2. Property-Based Tests",
            "command": "pytest tests/property/ -v --tb=short",
            "log": logs_dir / f"{timestamp}_property_tests.log"
        },
        {
            "name": "3. Comprehensive Security Tests",
            "command": "pytest tests/security/test_comprehensive_security.py -v --tb=short",
            "log": logs_dir / f"{timestamp}_security_tests.log"
        },
        {
            "name": "4. Full Test Suite",
            "command": "pytest tests/ -v --tb=short --maxfail=0",
            "log": logs_dir / f"{timestamp}_full_suite.log"
        },
        {
            "name": "5. Coverage Report",
            "command": "pytest tests/ --cov=src/pic --cov-report=html --cov-report=term",
            "log": logs_dir / f"{timestamp}_coverage.log"
        },
    ]
    
    # Run all test suites
    results = []
    overall_start = time.time()
    
    for suite in test_suites:
        result = run_test_suite(suite["name"], suite["command"], suite["log"])
        results.append(result)
        time.sleep(2)  # Brief pause between suites
    
    overall_duration = time.time() - overall_start
    
    # Generate summary report
    print("\n" + "=" * 80)
    print("OVERNIGHT TEST SUMMARY")
    print("=" * 80)
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Duration: {overall_duration/60:.2f} minutes")
    print("=" * 80)
    print()
    
    passed = sum(1 for r in results if r["success"])
    failed = len(results) - passed
    
    print(f"Results: {passed}/{len(results)} test suites passed")
    print()
    
    for result in results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"{status} | {result['name']:<40} | {result['duration']:>8.2f}s")
    
    print()
    print("=" * 80)
    
    # Save JSON report
    report_file = logs_dir / f"{timestamp}_summary.json"
    with open(report_file, 'w') as f:
        json.dump({
            "timestamp": timestamp,
            "started": datetime.now().isoformat(),
            "duration_seconds": overall_duration,
            "total_suites": len(results),
            "passed": passed,
            "failed": failed,
            "results": results
        }, f, indent=2)
    
    print(f"Summary report saved to: {report_file}")
    print("=" * 80)
    
    # Exit with appropriate code
    exit_code = 0 if failed == 0 else 1
    print(f"\nExiting with code: {exit_code}")
    return exit_code


if __name__ == "__main__":
    exit(main())
