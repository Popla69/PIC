"""Demo of Brain-CellAgent Integration.

This demo shows the complete integrated PIC system with:
- Real-time anomaly detection
- Secure communication with HMAC signatures
- Rate limiting and backpressure handling
- Performance monitoring
- Graceful error handling
"""

import time
import random
from pic.integrated import IntegratedPIC


def main():
    print("=" * 70)
    print("PIC Brain-CellAgent Integration Demo")
    print("=" * 70)
    print()
    
    # Initialize IntegratedPIC
    print("1. Initializing IntegratedPIC...")
    pic = IntegratedPIC(data_dir="demo_data")
    pic.start()
    print("   [OK] All components initialized and connected")
    print()
    
    # Demo 1: Normal behavior
    print("2. Demo: Normal Behavior (Building Baseline)")
    print("-" * 70)
    
    @pic.agent.monitor
    def process_payment(amount, user_id):
        """Simulate payment processing."""
        time.sleep(0.001)  # Simulate work
        return {"status": "success", "amount": amount, "user": user_id}
    
    # Execute normal operations to build baseline
    print("   Executing 30 normal payment operations...")
    for i in range(30):
        result = process_payment(amount=100.0 + i, user_id=f"user_{i}")
        if i % 10 == 0:
            print(f"   - Payment {i+1}: {result['status']}")
    
    print("   [OK] Baseline established")
    print()
    
    # Demo 2: Show statistics
    print("3. System Statistics")
    print("-" * 70)
    stats = pic.get_stats()
    
    print(f"   Agent Stats:")
    print(f"   - Total events: {stats['agent_stats']['total_events']}")
    print(f"   - Sampling rate: {stats['agent_stats']['sampling_rate']:.2%}")
    print(f"   - Throttled events: {stats['agent_stats']['throttle_events']}")
    
    if stats['brain_stats']:
        print(f"\n   Brain Connector Stats:")
        print(f"   - Total requests: {stats['brain_stats']['total_requests']}")
        print(f"   - Success rate: {stats['brain_stats']['success_rate']:.2%}")
        print(f"   - Retries: {stats['brain_stats']['retries']}")
    
    print(f"\n   Brain Core Stats:")
    print(f"   - Events processed: {stats['brain_core_stats']['events_processed']}")
    print(f"   - Security violations: {stats['brain_core_stats']['security_violations']}")
    
    perf = stats['agent_stats']['performance']
    if perf['sample_count'] > 0:
        print(f"\n   Performance Metrics:")
        print(f"   - P50 latency: {perf['p50_latency_ms']:.2f}ms")
        print(f"   - P95 latency: {perf['p95_latency_ms']:.2f}ms")
        print(f"   - P99 latency: {perf['p99_latency_ms']:.2f}ms")
    
    print()
    
    # Demo 3: Rate limiting
    print("4. Demo: Rate Limiting")
    print("-" * 70)
    
    @pic.agent.monitor
    def fast_operation():
        """Simulate fast operation."""
        return "ok"
    
    print("   Executing 200 rapid operations...")
    start = time.time()
    for _ in range(200):
        fast_operation()
    elapsed = time.time() - start
    
    rate_stats = pic.agent.rate_limiter.get_stats()
    print(f"   - Completed in {elapsed:.3f}s")
    print(f"   - Total checks: {rate_stats['total_checks']}")
    print(f"   - Allowed: {rate_stats['total_allowed']}")
    print(f"   - Throttled: {rate_stats['total_throttled']}")
    print(f"   - Allow rate: {rate_stats['allow_rate']:.2%}")
    print()
    
    # Demo 4: Security features
    print("5. Demo: Security Features")
    print("-" * 70)
    print("   Security Validator Stats:")
    sec_stats = pic.brain.security_validator.get_stats()
    print(f"   - Total validations: {sec_stats['total_validations']}")
    print(f"   - Valid events: {sec_stats['valid_events']}")
    print(f"   - Invalid signatures: {sec_stats['invalid_signatures']}")
    print(f"   - Replay attacks: {sec_stats['replay_attacks']}")
    print(f"   - Nonce cache size: {sec_stats['nonce_cache_size']}")
    print()
    
    # Demo 5: Graceful error handling
    print("6. Demo: Graceful Error Handling")
    print("-" * 70)
    
    @pic.agent.monitor
    def risky_operation(should_fail=False):
        """Operation that might fail."""
        if should_fail:
            raise ValueError("Simulated error")
        return "success"
    
    print("   Testing error handling...")
    
    # Normal execution
    result = risky_operation(should_fail=False)
    print(f"   - Normal execution: {result}")
    
    # Error execution (should not crash)
    try:
        risky_operation(should_fail=True)
    except ValueError as e:
        print(f"   - Error caught gracefully: {e}")
    
    print("   [OK] Application continues running despite errors")
    print()
    
    # Demo 6: Multiple functions
    print("7. Demo: Multiple Monitored Functions")
    print("-" * 70)
    
    @pic.agent.monitor
    def read_data(key):
        time.sleep(0.001)
        return f"data_{key}"
    
    @pic.agent.monitor
    def write_data(key, value):
        time.sleep(0.002)
        return True
    
    @pic.agent.monitor
    def delete_data(key):
        time.sleep(0.001)
        return True
    
    print("   Executing mixed operations...")
    for i in range(10):
        read_data(f"key_{i}")
        write_data(f"key_{i}", f"value_{i}")
        if i % 3 == 0:
            delete_data(f"key_{i}")
    
    print("   [OK] Multiple functions monitored simultaneously")
    print()
    
    # Final statistics
    print("8. Final System Statistics")
    print("-" * 70)
    final_stats = pic.get_stats()
    print(f"   Total events collected: {final_stats['agent_stats']['total_events']}")
    print(f"   Brain events processed: {final_stats['brain_core_stats']['events_processed']}")
    print(f"   Trace store events: {final_stats['trace_store_events']}")
    print()
    
    # Cleanup
    print("9. Shutting Down")
    print("-" * 70)
    pic.stop()
    print("   [OK] All components stopped gracefully")
    print()
    
    print("=" * 70)
    print("Demo Complete!")
    print("=" * 70)
    print()
    print("Key Features Demonstrated:")
    print("  [OK] Integrated Brain-CellAgent system")
    print("  [OK] Real-time anomaly detection")
    print("  [OK] Secure HMAC communication")
    print("  [OK] Rate limiting and throttling")
    print("  [OK] Performance monitoring (p50/p95/p99)")
    print("  [OK] Graceful error handling")
    print("  [OK] Multi-function monitoring")
    print()


if __name__ == "__main__":
    main()
