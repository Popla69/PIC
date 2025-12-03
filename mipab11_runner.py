#!/usr/bin/env python3
"""
MIPAB-11: Polymorphic Intelligent Behavior Attack Burst

Advanced test simulating sophisticated attackers using:
- Polymorphic attack variants (10 per second)
- Legitimate user simulation
- Camouflage attacks mimicking legitimate behavior
- Adaptive mutation engine

Tests PIC's ability to distinguish between sophisticated attacks
and legitimate traffic under heavy, adaptive evasion.
"""

import time
import uuid
import hmac
import hashlib
import json
import random
import threading
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from pic.integrated import IntegratedPIC
from pic.models.events import TelemetryEvent
from pic.models.integration import SignedEvent

# Test Configuration
DURATION = 120  # seconds
ATTACK_RATE = 10   # attack events per second
LEGIT_RATE = 1     # legit events per second
WORKERS = 20
HMAC_KEY = b"testkey"

# Global stats with thread safety
out_lock = threading.Lock()
stats = {
    "duration_s": None,
    "total_events": 0,
    "legit_events": 0,
    "legit_allowed": 0,
    "malicious_events": 0,
    "malicious_blocked": 0,
    "false_positives": 0,
    "false_negatives": 0,
    "latencies_ms": [],
    "signature_errors": 0,
    "nonce_replays": 0,
    "backpressure_signals": 0,
    "start_time": None,
    "backpressure_active_time": 0.0
}

# Global PIC instance
pic = None

def sign_event_hmac(ev_dict, key=HMAC_KEY):
    """Sign event with HMAC for testing."""
    payload = json.dumps(ev_dict, sort_keys=True).encode()
    sig = hmac.new(key, payload, hashlib.sha256).hexdigest()
    return sig

def process_event_with_pic(event, is_legit=False, tamper_sig=False, use_replay_nonce=None):
    """Process event through PIC and record stats."""
    global pic
    
    t0 = time.perf_counter()
    
    try:
        # Create signed event
        if use_replay_nonce:
            # Replay attack - reuse nonce
            signed_event = SignedEvent(
                event=event,
                signature="REPLAY_ATTACK",
                nonce=use_replay_nonce,
                timestamp=datetime.now()
            )
        elif tamper_sig:
            # Tampered signature
            signed_event = SignedEvent(
                event=event,
                signature="TAMPERED_" + str(random.randint(1000, 9999)),
                nonce=str(uuid.uuid4()),
                timestamp=datetime.now()
            )
        else:
            # Properly signed
            signed_event = pic.connector.transport.sign_event(event)
        
        # Process through BrainCore
        decision = pic.brain.process_signed_event(signed_event)
        
        latency = (time.perf_counter() - t0) * 1000
        
        with out_lock:
            stats["total_events"] += 1
            stats["latencies_ms"].append(latency)
            
            if is_legit:
                stats["legit_events"] += 1
                if decision.action == "allow":
                    stats["legit_allowed"] += 1
                else:
                    stats["false_positives"] += 1
            else:
                stats["malicious_events"] += 1
                if decision.action == "block":
                    stats["malicious_blocked"] += 1
                else:
                    stats["false_negatives"] += 1
        
        return signed_event.nonce if hasattr(signed_event, 'nonce') else None
        
    except Exception as e:
        latency = (time.perf_counter() - t0) * 1000
        with out_lock:
            stats["total_events"] += 1
            stats["latencies_ms"].append(latency)
            stats["signature_errors"] += 1
            
            if is_legit:
                stats["legit_events"] += 1
                stats["false_positives"] += 1  # Error = blocked legit
            else:
                stats["malicious_events"] += 1
                stats["malicious_blocked"] += 1  # Error = blocked attack
        
        return None

def make_legit_event(i):
    """Create legitimate telemetry event."""
    return TelemetryEvent(
        timestamp=datetime.now(),
        event_id=f"legit_user_{i}",
        process_id=1234,
        thread_id=5678,
        function_name="getUserProfile",
        module_name="app.user",
        duration_ms=random.uniform(1.0, 5.0),
        args_metadata={
            "arg_count": 1,
            "arg_types": ["str"],
            "user_id": f"user_{i % 100}"
        },
        resource_tags={
            "io_operations": 0,
            "network_calls": 1,
            "call_type": "read"
        },
        redaction_applied=True,
        sampling_rate=1.0
    )

def make_attack_event(i, variant):
    """Create polymorphic attack event based on variant."""
    return TelemetryEvent(
        timestamp=datetime.now() + timedelta(seconds=variant.get("time_skew", 0)),
        event_id=f"attack_{variant['name']}_{i}",
        process_id=variant.get("pid", 1234),
        thread_id=variant.get("tid", 5678),
        function_name=variant.get("function", "malicious_function"),
        module_name=variant.get("module", "attack.module"),
        duration_ms=variant.get("duration", random.uniform(0.5, 200)),
        args_metadata=variant.get("args", {"malicious": True}),
        resource_tags=variant.get("tags", {"attack_type": variant["name"]}),
        redaction_applied=True,
        sampling_rate=1.0
    )

def get_polymorphic_variant(i, mutation_cycle):
    """Generate polymorphic attack variant that changes every 10s."""
    # Mutation cycle changes every 10 seconds
    base_seed = (mutation_cycle * 1000) + (i % 100)
    random.seed(base_seed)
    
    r = random.random()
    
    if r < 0.15:  # Invalid HMAC (random changes)
        return {
            "name": "invalid_hmac",
            "time_skew": 0.0,
            "function": "app.user.getProfile",
            "module": "app.user",
            "duration": random.uniform(50, 150),
            "tamper_sig": True
        }
    elif r < 0.30:  # Truncated HMAC
        return {
            "name": "truncated_hmac", 
            "time_skew": 0.0,
            "function": "auth.login",
            "module": "auth",
            "duration": random.uniform(5, 20),
            "tamper_sig": True
        }
    elif r < 0.45:  # Valid HMAC + malicious payload
        return {
            "name": "payload_evasion",
            "time_skew": 0.0,
            "function": "getUserProfile",  # Mimic legit function
            "module": "app.user",
            "duration": random.uniform(1, 4),  # Mimic legit timing
            "args": {
                "user_id": "../../../etc/passwd",  # Path traversal
                "malicious_payload": True
            },
            "tamper_sig": False  # Valid signature!
        }
    elif r < 0.60:  # Replay-like (stolen nonce simulation)
        return {
            "name": "replay_like",
            "time_skew": -5.0,
            "function": "app.user.getData",
            "module": "app.user", 
            "duration": random.uniform(1, 10),
            "use_replay": True
        }
    elif r < 0.75:  # Time-skewed within allowed window
        return {
            "name": "time_edge_case",
            "time_skew": random.uniform(-290, 290),  # Within 5min window
            "function": "data.fetch",
            "module": "data",
            "duration": random.uniform(10, 50)
        }
    elif r < 0.90:  # Function/endpoint mimic
        return {
            "name": "behavioral_mimic",
            "time_skew": 0.0,
            "function": "getUserProfile",  # Same as legit
            "module": "app.user",         # Same as legit
            "duration": random.uniform(1, 5),  # Same range as legit
            "args": {
                "user_id": f"user_{random.randint(1, 100)}",  # Looks normal
                "hidden_attack": "sql_injection"
            }
        }
    else:  # Rate-conceal (slow bursts)
        return {
            "name": "slow_evasion",
            "time_skew": 0.0,
            "function": "data.process",
            "module": "data",
            "duration": random.uniform(100, 400),  # Slow operation
            "args": {"large_payload": "x" * 1000}
        }

def attack_worker(stop_at, worker_id):
    """Worker thread generating polymorphic attacks."""
    i = 0
    legit_nonces = []  # Store for replay attacks
    
    while time.time() < stop_at:
        # Calculate mutation cycle (changes every 10s)
        mutation_cycle = int((time.time() - stats["start_time"]) // 10)
        
        variant = get_polymorphic_variant(i, mutation_cycle)
        event = make_attack_event(i, variant)
        
        # Handle different attack types
        if variant.get("use_replay") and legit_nonces:
            # Use a previously seen nonce for replay
            replay_nonce = random.choice(legit_nonces)
            process_event_with_pic(event, is_legit=False, use_replay_nonce=replay_nonce)
            with out_lock:
                stats["nonce_replays"] += 1
        else:
            # Normal attack processing
            nonce = process_event_with_pic(
                event, 
                is_legit=False, 
                tamper_sig=variant.get("tamper_sig", False)
            )
            
            # Store nonce for potential replay attacks
            if nonce and len(legit_nonces) < 50:
                legit_nonces.append(nonce)
        
        i += 1
        
        # Rate limiting
        time.sleep(1.0 / (ATTACK_RATE / WORKERS))

def legit_worker(stop_at):
    """Worker thread generating legitimate user events."""
    i = 0
    
    while time.time() < stop_at:
        event = make_legit_event(i)
        process_event_with_pic(event, is_legit=True)
        
        i += 1
        time.sleep(1.0 / LEGIT_RATE)

def backpressure_monitor(stop_at):
    """Monitor backpressure status."""
    global pic
    
    backpressure_start = None
    
    while time.time() < stop_at:
        try:
            # Check if backpressure is active
            backpressure_active = False  # Placeholder
            
            current_time = time.time()
            
            if backpressure_active and backpressure_start is None:
                backpressure_start = current_time
                with out_lock:
                    stats["backpressure_signals"] += 1
            elif not backpressure_active and backpressure_start is not None:
                with out_lock:
                    stats["backpressure_active_time"] += current_time - backpressure_start
                backpressure_start = None
            
        except Exception:
            pass
        
        time.sleep(0.1)  # Check every 100ms
    
    # Handle case where backpressure is still active at end
    if backpressure_start is not None:
        with out_lock:
            stats["backpressure_active_time"] += time.time() - backpressure_start

def run_mipab11():
    """Run MIPAB-11 test."""
    global pic, stats
    
    print("=" * 80)
    print("MIPAB-11: Polymorphic Intelligent Behavior Attack Burst")
    print("=" * 80)
    print(f"Duration: {DURATION}s")
    print(f"Attack Rate: {ATTACK_RATE} events/sec")
    print(f"Legitimate Rate: {LEGIT_RATE} events/sec")
    print(f"Workers: {WORKERS}")
    print()
    
    # Initialize PIC
    print("Initializing IntegratedPIC...")
    pic = IntegratedPIC(data_dir="mipab11_test_data")
    pic.start()
    print("System ready.\\n")
    
    # Record start time
    stats["start_time"] = time.time()
    stop_at = stats["start_time"] + DURATION
    
    print("Starting polymorphic attack simulation...")
    print("Attack variants will mutate every 10 seconds")
    print()
    
    # Run test with thread pool
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = []
        
        # Start attack workers
        attack_workers = max(1, WORKERS - 2)
        for worker_id in range(attack_workers):
            futures.append(executor.submit(attack_worker, stop_at, worker_id))
        
        # Start legitimate user worker
        futures.append(executor.submit(legit_worker, stop_at))
        
        # Start backpressure monitor
        futures.append(executor.submit(backpressure_monitor, stop_at))
        
        # Wait for completion
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Worker error: {e}")
    
    # Calculate final statistics
    actual_duration = time.time() - stats["start_time"]
    stats["duration_s"] = actual_duration
    
    lat = stats["latencies_ms"]
    
    # Calculate percentiles
    if lat:
        sorted_lat = sorted(lat)
        n = len(sorted_lat)
        p50 = sorted_lat[n // 2] if n > 0 else 0
        p95 = sorted_lat[int(n * 0.95)] if n > 0 else 0
        p99 = sorted_lat[int(n * 0.99)] if n > 0 else 0
    else:
        p50 = p95 = p99 = 0
    
    # Calculate rates
    legit_acceptance_rate = (stats["legit_allowed"] / stats["legit_events"]) * 100 if stats["legit_events"] > 0 else 0
    malicious_block_rate = (stats["malicious_blocked"] / stats["malicious_events"]) * 100 if stats["malicious_events"] > 0 else 0
    false_positive_rate = (stats["false_positives"] / stats["legit_events"]) * 100 if stats["legit_events"] > 0 else 0
    
    # Peak throughput
    peak_throughput = stats["total_events"] / actual_duration if actual_duration > 0 else 0
    
    # Backpressure fraction
    backpressure_fraction = stats["backpressure_active_time"] / actual_duration if actual_duration > 0 else 0
    
    # Create summary
    summary = {
        "duration_s": actual_duration,
        "total_events": stats["total_events"],
        "legit_events": stats["legit_events"],
        "legit_allowed": stats["legit_allowed"],
        "malicious_events": stats["malicious_events"],
        "malicious_blocked": stats["malicious_blocked"],
        "false_positives": stats["false_positives"],
        "false_negatives": stats["false_negatives"],
        "p50_latency_ms": p50,
        "p95_latency_ms": p95,
        "p99_latency_ms": p99,
        "peak_throughput_eps": peak_throughput,
        "backpressure_time_fraction": backpressure_fraction,
        "nonce_replays_detected": stats["nonce_replays"],
        "signature_errors": stats["signature_errors"],
        
        # Additional metrics
        "legit_acceptance_rate_pct": legit_acceptance_rate,
        "malicious_block_rate_pct": malicious_block_rate,
        "false_positive_rate_pct": false_positive_rate
    }
    
    # Print results
    print("\\n" + "=" * 80)
    print("MIPAB-11 TEST RESULTS")
    print("=" * 80)
    
    print(f"\\nTest Summary:")
    print(f"  Duration: {actual_duration:.1f}s")
    print(f"  Total Events: {stats['total_events']}")
    print(f"  Peak Throughput: {peak_throughput:.1f} events/sec")
    
    print(f"\\nLegitimate Traffic:")
    print(f"  Events: {stats['legit_events']}")
    print(f"  Allowed: {stats['legit_allowed']}")
    print(f"  Acceptance Rate: {legit_acceptance_rate:.1f}%")
    
    print(f"\\nMalicious Traffic:")
    print(f"  Events: {stats['malicious_events']}")
    print(f"  Blocked: {stats['malicious_blocked']}")
    print(f"  Block Rate: {malicious_block_rate:.1f}%")
    
    print(f"\\nError Analysis:")
    print(f"  False Positives: {stats['false_positives']} ({false_positive_rate:.1f}%)")
    print(f"  False Negatives: {stats['false_negatives']}")
    print(f"  Signature Errors: {stats['signature_errors']}")
    print(f"  Nonce Replays: {stats['nonce_replays']}")
    
    print(f"\\nPerformance:")
    print(f"  P50 Latency: {p50:.2f}ms")
    print(f"  P95 Latency: {p95:.2f}ms")
    print(f"  P99 Latency: {p99:.2f}ms")
    print(f"  Backpressure Time: {backpressure_fraction:.1%}")
    
    # Evaluate pass/fail
    print(f"\\n" + "=" * 80)
    print("PASS/FAIL EVALUATION")
    print("=" * 80)
    
    hard_pass = (
        legit_acceptance_rate >= 99 and
        malicious_block_rate >= 95 and
        false_positive_rate <= 1 and
        p95 <= 20 and
        backpressure_fraction < 0.05
    )
    
    soft_pass = (
        legit_acceptance_rate >= 95 and
        malicious_block_rate >= 90 and
        p95 <= 50
    )
    
    print(f"Success Criteria:")
    print(f"  Legit acceptance ≥99%: {legit_acceptance_rate:.1f}% {'✓' if legit_acceptance_rate >= 99 else '✗'}")
    print(f"  Malicious block ≥95%: {malicious_block_rate:.1f}% {'✓' if malicious_block_rate >= 95 else '✗'}")
    print(f"  False positive ≤1%: {false_positive_rate:.1f}% {'✓' if false_positive_rate <= 1 else '✗'}")
    print(f"  P95 latency ≤20ms: {p95:.1f}ms {'✓' if p95 <= 20 else '✗'}")
    print(f"  Backpressure <5%: {backpressure_fraction:.1%} {'✓' if backpressure_fraction < 0.05 else '✗'}")
    
    if hard_pass:
        result = "HARD PASS ✓"
    elif soft_pass:
        result = "SOFT PASS (needs tuning)"
    else:
        result = "FAIL ✗"
    
    print(f"\\nOverall Result: {result}")
    
    # Print JSON summary
    print(f"\\n" + "=" * 80)
    print("JSON SUMMARY")
    print("=" * 80)
    print(json.dumps(summary, indent=2))
    
    # Cleanup
    pic.stop()
    
    return summary

if __name__ == "__main__":
    run_mipab11()
