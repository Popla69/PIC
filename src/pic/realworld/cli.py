"""Command-Line Interface for Real-World Testing Suite

Provides CLI commands for running real-world tests.
"""

import sys
import logging
import argparse
from pathlib import Path
from typing import Optional

from .suite import RealWorldTestSuite, TestSuiteConfig


def setup_logging(verbose: bool = False):
    """Setup logging configuration.
    
    Args:
        verbose: Enable verbose logging
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('realworld_tests.log')
        ]
    )


def cmd_run_all(args):
    """Run all test categories."""
    config = TestSuiteConfig(
        test_root=Path(args.test_root),
        output_dir=Path(args.output_dir),
        parallel_execution=args.parallel,
        max_workers=args.workers,
        cleanup_after_tests=not args.no_cleanup
    )
    
    suite = RealWorldTestSuite(config)
    report = suite.run_all_tests()
    
    # Exit with error code if tests failed
    if report["summary"]["failed"] > 0:
        sys.exit(1)


def cmd_run_category(args):
    """Run specific test category."""
    config = TestSuiteConfig(
        test_root=Path(args.test_root),
        output_dir=Path(args.output_dir),
        cleanup_after_tests=not args.no_cleanup
    )
    
    suite = RealWorldTestSuite(config)
    
    try:
        results = suite.run_category(args.category)
        
        # Print results - handle both list and dict formats
        if isinstance(results, dict):
            # Dict format from stress/malware/etc testers
            passed = results.get("passed_tests", 0)
            failed = results.get("total_tests", 0) - passed
            total = results.get("total_tests", 0)
        elif isinstance(results, list):
            # List format from latency/runtime testers
            from pic.realworld.harness import TestStatus
            passed = sum(1 for r in results if r.status == TestStatus.PASSED)
            failed = sum(1 for r in results if r.status == TestStatus.FAILED)
            total = len(results)
        else:
            passed = failed = total = 0
        
        print(f"\n{args.category} Results:")
        print(f"  Passed: {passed}")
        print(f"  Failed: {failed}")
        print(f"  Total: {total}")
        
        if failed > 0:
            sys.exit(1)
            
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)


def cmd_list_categories(args):
    """List available test categories."""
    config = TestSuiteConfig()
    suite = RealWorldTestSuite(config)
    
    categories = suite.list_categories()
    
    print("\nAvailable Test Categories:")
    for category in categories:
        print(f"  - {category}")
    print()


def cmd_run_latency(args):
    """Run latency anomaly detection tests."""
    args.category = "latency"
    cmd_run_category(args)


def cmd_run_runtime(args):
    """Run runtime attack detection tests."""
    args.category = "runtime"
    cmd_run_category(args)


def cmd_run_stress(args):
    """Run stress and abuse resistance tests."""
    args.category = "stress"
    cmd_run_category(args)


def cmd_run_malware(args):
    """Run malicious pattern recognition tests."""
    args.category = "malware"
    cmd_run_category(args)


def cmd_run_webservice(args):
    """Run web service integration tests."""
    args.category = "webservice"
    cmd_run_category(args)


def cmd_run_microservice(args):
    """Run microservice attack simulation tests."""
    args.category = "microservice"
    cmd_run_category(args)


def cmd_run_vulnerable(args):
    """Run vulnerable application tests."""
    args.category = "vulnerable_app"
    cmd_run_category(args)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="PIC Real-World Testing Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests
  pic-realworld run-all
  
  # Run specific category
  pic-realworld run-category latency
  
  # Run with custom directories
  pic-realworld run-all --test-root /tmp/pic_tests --output-dir ./results
  
  # List available categories
  pic-realworld list-categories
  
  # Run specific test types
  pic-realworld run-latency
  pic-realworld run-stress
  pic-realworld run-webservice
        """
    )
    
    # Global options
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--test-root',
        default='test_data/realworld',
        help='Root directory for test data (default: test_data/realworld)'
    )
    
    parser.add_argument(
        '--output-dir',
        default='test_results/realworld',
        help='Output directory for reports (default: test_results/realworld)'
    )
    
    parser.add_argument(
        '--no-cleanup',
        action='store_true',
        help='Skip cleanup of test artifacts'
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # run-all command
    parser_run_all = subparsers.add_parser(
        'run-all',
        help='Run all test categories'
    )
    parser_run_all.add_argument(
        '--parallel',
        action='store_true',
        help='Run tests in parallel'
    )
    parser_run_all.add_argument(
        '--workers',
        type=int,
        default=4,
        help='Number of parallel workers (default: 4)'
    )
    parser_run_all.set_defaults(func=cmd_run_all)
    
    # run-category command
    parser_run_category = subparsers.add_parser(
        'run-category',
        help='Run specific test category'
    )
    parser_run_category.add_argument(
        'category',
        help='Category name (use list-categories to see available)'
    )
    parser_run_category.set_defaults(func=cmd_run_category)
    
    # list-categories command
    parser_list = subparsers.add_parser(
        'list-categories',
        help='List available test categories'
    )
    parser_list.set_defaults(func=cmd_list_categories)
    
    # Convenience commands for specific categories
    parser_latency = subparsers.add_parser(
        'run-latency',
        help='Run latency anomaly detection tests'
    )
    parser_latency.set_defaults(func=cmd_run_latency)
    
    parser_runtime = subparsers.add_parser(
        'run-runtime',
        help='Run runtime attack detection tests'
    )
    parser_runtime.set_defaults(func=cmd_run_runtime)
    
    parser_stress = subparsers.add_parser(
        'run-stress',
        help='Run stress and abuse resistance tests'
    )
    parser_stress.set_defaults(func=cmd_run_stress)
    
    parser_malware = subparsers.add_parser(
        'run-malware',
        help='Run malicious pattern recognition tests'
    )
    parser_malware.set_defaults(func=cmd_run_malware)
    
    parser_webservice = subparsers.add_parser(
        'run-webservice',
        help='Run web service integration tests'
    )
    parser_webservice.set_defaults(func=cmd_run_webservice)
    
    parser_microservice = subparsers.add_parser(
        'run-microservice',
        help='Run microservice attack simulation tests'
    )
    parser_microservice.set_defaults(func=cmd_run_microservice)
    
    parser_vulnerable = subparsers.add_parser(
        'run-vulnerable',
        help='Run vulnerable application tests'
    )
    parser_vulnerable.set_defaults(func=cmd_run_vulnerable)
    
    parser_enterprise = subparsers.add_parser(
        'run-enterprise',
        help='Run enterprise security tests'
    )
    def run_enterprise(args):
        args.category = 'enterprise'
        cmd_run_category(args)
    parser_enterprise.set_defaults(func=run_enterprise)
    
    parser_highvolume = subparsers.add_parser(
        'run-highvolume',
        help='Run high-volume performance tests'
    )
    def run_highvolume(args):
        args.category = 'highvolume'
        cmd_run_category(args)
    parser_highvolume.set_defaults(func=run_highvolume)
    
    parser_multistage = subparsers.add_parser(
        'run-multistage',
        help='Run multi-stage attack chain tests'
    )
    def run_multistage(args):
        args.category = 'multistage'
        cmd_run_category(args)
    parser_multistage.set_defaults(func=run_multistage)
    
    parser_aptstealth = subparsers.add_parser(
        'run-aptstealth',
        help='Run APT stealth attack tests'
    )
    def run_aptstealth(args):
        args.category = 'aptstealth'
        cmd_run_category(args)
    parser_aptstealth.set_defaults(func=run_aptstealth)
    
    parser_memoryconsistency = subparsers.add_parser(
        'run-memoryconsistency',
        help='Run memory consistency and recovery tests'
    )
    def run_memoryconsistency(args):
        args.category = 'memoryconsistency'
        cmd_run_category(args)
    parser_memoryconsistency.set_defaults(func=run_memoryconsistency)
    
    # Parse arguments
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Execute command
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
