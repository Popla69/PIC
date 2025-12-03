#!/usr/bin/env python3
"""Integration test for Real-World Testing Suite

Verifies that all components can be imported and initialized.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    
    try:
        from pic.realworld import RealWorldTestSuite
        print("✅ RealWorldTestSuite imported")
    except Exception as e:
        print(f"❌ Failed to import RealWorldTestSuite: {e}")
        return False
    
    try:
        from pic.realworld import ReportGenerator
        print("✅ ReportGenerator imported")
    except Exception as e:
        print(f"❌ Failed to import ReportGenerator: {e}")
        return False
    
    try:
        from pic.realworld import SafetyController
        print("✅ SafetyController imported")
    except Exception as e:
        print(f"❌ Failed to import SafetyController: {e}")
        return False
    
    try:
        from pic.realworld import SandboxManager
        print("✅ SandboxManager imported")
    except Exception as e:
        print(f"❌ Failed to import SandboxManager: {e}")
        return False
    
    try:
        from pic.realworld import TestHarness
        print("✅ TestHarness imported")
    except Exception as e:
        print(f"❌ Failed to import TestHarness: {e}")
        return False
    
    return True


def test_initialization():
    """Test that components can be initialized."""
    print("\nTesting initialization...")
    
    try:
        from pic.realworld import SafetyController
        from pathlib import Path
        
        safety = SafetyController(test_root=Path("test_data/integration"))
        print("✅ SafetyController initialized")
        
        stats = safety.get_stats()
        print(f"   Stats: {stats}")
        
    except Exception as e:
        print(f"❌ Failed to initialize SafetyController: {e}")
        return False
    
    try:
        from pic.realworld import ReportGenerator
        from pathlib import Path
        
        reporter = ReportGenerator(output_dir=Path("test_results/integration"))
        print("✅ ReportGenerator initialized")
        
    except Exception as e:
        print(f"❌ Failed to initialize ReportGenerator: {e}")
        return False
    
    return True


def test_suite_creation():
    """Test that test suite can be created."""
    print("\nTesting suite creation...")
    
    try:
        from pic.realworld import RealWorldTestSuite
        from pic.realworld.suite import TestSuiteConfig
        from pathlib import Path
        
        config = TestSuiteConfig(
            test_root=Path("test_data/integration"),
            output_dir=Path("test_results/integration"),
            enable_latency_tests=True,
            enable_runtime_tests=False,  # Disable others for quick test
            enable_stress_tests=False,
            enable_malware_tests=False,
            enable_webservice_tests=False,
            enable_microservice_tests=False,
            enable_vulnerable_app_tests=False
        )
        
        suite = RealWorldTestSuite(config)
        print("✅ RealWorldTestSuite created")
        
        categories = suite.list_categories()
        print(f"   Available categories: {categories}")
        
    except Exception as e:
        print(f"❌ Failed to create RealWorldTestSuite: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def main():
    """Run all integration tests."""
    print("="*60)
    print("PIC Real-World Testing Suite - Integration Tests")
    print("="*60)
    print()
    
    all_passed = True
    
    # Test imports
    if not test_imports():
        all_passed = False
    
    # Test initialization
    if not test_initialization():
        all_passed = False
    
    # Test suite creation
    if not test_suite_creation():
        all_passed = False
    
    print()
    print("="*60)
    if all_passed:
        print("✅ ALL INTEGRATION TESTS PASSED")
        print("="*60)
        return 0
    else:
        print("❌ SOME INTEGRATION TESTS FAILED")
        print("="*60)
        return 1


if __name__ == '__main__':
    sys.exit(main())
