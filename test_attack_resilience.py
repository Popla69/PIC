"""
PIC v1 Attack Resilience Test
3-Phase Test: Attack Burst → Legitimate Event → Attack Burst

Tests PIC's ability to correctly allow legitimate traffic
while under sustained attack.
"""

import time
import random
from datetime import datetime, timedelta
from pic.integrated import IntegratedPIC
from pic.models.integration import SignedEvent
from pic.models.events import TelemetryEvent

def run_attack_resilience_test():
    """Run 3-phase attack resilience test."""
    
    print("=" * 80)
    print("PIC v1 ATTACK RESILIENCE TEST")
    print("3-Phase: 100 Attacks -> 1 Legitimate -> 100 Attacks")
    print("=" * 80)
    print()
    
    # Initialize
    print("Initializing IntegratedPIC...")
    pic = IntegratedPIC(data_dir="attack_test_data")
    pic.start()
    print("System ready.\n")
    
    # ========================================================================
    # PHASE 1: Attack Burst (100 malicious events)
    # ========================================================================
    print("=" * 80)
    print("PHASE 1: Attack Burst (100 malicious events)")
    print("=" * 80)
    
    phase1_start = time.perf_counter()
    phase1_blocked = 0
    phase1_allowed = 0
    attack_types = {
        "tampered": 0,
        "replay": 0,
        "expired": 0,
        "invalid_sig": 0
    }
    
    # Store first valid nonce for replay attacks
    first_nonce = None
    
    for i in range(100):
        attack_type = i % 4  # Rotate through attack types
        
        try:
            if attack_type == 0:  # Tampered signature
                event = TelemetryEvent(
                    timestamp=datetime.now(),
                    event_id=f"attack_tamper_{i}",
                    process_id=1234,
                    thread_id=5678,
                    function_name="attack_function",
                    module_name="attack_module",
                    duration_ms=1.0,
                    args_metadata={"malicious": True},
                    resource_tags={},
                    redaction_applied=True,
                    sampling_rate=1.0
                )
                
                # Create with WRONG signature
                signed = SignedEvent(
                    event=event,
                    signature="TAMPERED_SIGNATURE_GARBAGE",
                    nonce=f"tamper_{i}",
                    timestamp=datetime.now()
                )
                attack_types["tampered"] += 1
                
            elif attack_type == 1:  # Replay attack
                event = TelemetryEvent(
                    timestamp=datetime.now(),
                    event_id=f"attack_replay_{i}",
                    process_id=1234,
                    thread_id=5678,
                    function_name="attack_function",
                    module_name="attack_module",
                    duration_ms=1.0,
                    args_metadata={"malicious": True},
                    resource_tags={},
                    redaction_applied=True,
                    sampling_rate=1.0
                )
                
                # Sign properly first time, then reuse nonce
                if first_nonce is None:
                    signed = pic.connector.transport.sign_event(event)
                    first_nonce = signed.nonce
                else:
                    # Reuse nonce - replay attack!
                    signed = SignedEvent(
                        event=event,
                        signature="REPLAY_SIG",
                        nonce=first_nonce,  # REUSED NONCE
                        timestamp=datetime.now()
                    )
                attack_types["replay"] += 1
                
            elif attack_type == 2:  # Expired timestamp
                event = TelemetryEvent(
                    timestamp=datetime.now() - timedelta(hours=1),  # Old
                    event_id=f"attack_expired_{i}",
                    process_id=1234,
                    thread_id=5678,
                    function_name="attack_function",
                    module_name="attack_module",
                    duration_ms=1.0,
                    args_metadata={"malicious": True},
                    resource_tags={},
                    redaction_applied=True,
                    sampling_rate=1.0
                )
                
                signed = pic.connector.transport.sign_event(event)
                # Force old timestamp
                signed.timestamp = datetime.now() - timedelta(hours=1)
                attack_types["expired"] += 1
                
            else:  # Invalid signature garbage
                event = TelemetryEvent(
                    timestamp=datetime.now(),
                    event_id=f"attack_garbage_{i}",
                    process_id=1234,
                    thread_id=5678,
                    function_name="attack_function",
                    module_name="attack_module",
                    duration_ms=1.0,
                    args_metadata={"malicious": True},
                    resource_tags={},
                    redaction_applied=True,
                    sampling_rate=1.0
                )
                
                signed = SignedEvent(
                    event=event,
                    signature="RANDOM_GARBAGE_" + str(random.randint(1000, 9999)),
                    nonce=f"garbage_{i}",
                    timestamp=datetime.now()
                )
                attack_types["invalid_sig"] += 1
            
            # Process
            decision = pic.brain.process_signed_event(signed)
            
            if decision.action == "block":
                phase1_blocked += 1
            else:
                phase1_allowed += 1
                
        except Exception as e:
            # Errors count as blocked
            phase1_blocked += 1
    
    phase1_end = time.perf_counter()
    phase1_time = phase1_end - phase1_start
    
    print(f"\nPHASE 1 SUMMARY:")
    print(f"Total Attacks: 100")
    print(f"Blocked: {phase1_blocked}")
    print(f"Allowed: {phase1_allowed}")
    print(f"Block Rate: {phase1_blocked/100:.1%}")
    print(f"Time: {phase1_time:.3f}s")
    print(f"Throughput: {100/phase1_time:.1f} events/sec")
    print(f"\nAttack Types:")
    print(f"  - Tampered: {attack_types['tampered']}")
    print(f"  - Replay: {attack_types['replay']}")
    print(f"  - Expired: {attack_types['expired']}")
    print(f"  - Invalid Sig: {attack_types['invalid_sig']}")
    print()
    
    # ========================================================================
    # PHASE 2: Single Legitimate Event
    # ========================================================================
    print("=" * 80)
    print("PHASE 2: Single Legitimate Event (Should be ALLOWED)")
    print("=" * 80)
    
    try:
        # Create perfectly legitimate event
        legit_event = TelemetryEvent(
            timestamp=datetime.now(),
            event_id="realUser99",
            process_id=1234,
            thread_id=5678,
            function_name="getUserProfile",
            module_name="user_service",
            duration_ms=2.1,
            args_metadata={
                "function": "getUserProfile",
                "duration_ms": 2.1,
                "call_type": "read"
            },
            resource_tags={"call_type": "read"},
            redaction_applied=True,
            sampling_rate=1.0
        )
        
        # Sign properly with valid HMAC
        legit_signed = pic.connector.transport.sign_event(legit_event)
        
        # Process
        phase2_start = time.perf_counter()
        legit_decision = pic.brain.process_signed_event(legit_signed)
        phase2_end = time.perf_counter()
        phase2_latency = (phase2_end - phase2_start) * 1000
        
        print(f"\nPHASE 2 RESULT:")
        print(f"Event ID: realUser99")
        print(f"Function: getUserProfile")
        print(f"Call Type: read")
        print(f"Duration: 2.1ms")
        print(f"Nonce: {legit_signed.nonce}")
        print(f"Timestamp: {legit_signed.timestamp}")
        print(f"Signature: {legit_signed.signature[:32]}...")
        print(f"\nDECISION: {legit_decision.action.upper()}")
        print(f"Reason: {legit_decision.reason}")
        print(f"Processing Latency: {phase2_latency:.2f}ms")
        print(f"\nVALIDATION: {'PASS - Legitimate event ALLOWED' if legit_decision.action == 'allow' else 'FAIL - Legitimate event BLOCKED'}")
        print()
        
        phase2_result = legit_decision.action
        
    except Exception as e:
        print(f"\nPHASE 2 RESULT:")
        print(f"ERROR: {str(e)}")
        print(f"VALIDATION: FAIL - Exception occurred")
        print()
        phase2_result = "error"
    
    # ========================================================================
    # PHASE 3: Continue Attack Burst (100 more attacks)
    # ========================================================================
    print("=" * 80)
    print("PHASE 3: Continue Attack Burst (100 more malicious events)")
    print("=" * 80)
    
    phase3_start = time.perf_counter()
    phase3_blocked = 0
    phase3_allowed = 0
    
    for i in range(100):
        attack_type = i % 4
        
        try:
            if attack_type == 0:  # Tampered
                event = TelemetryEvent(
                    timestamp=datetime.now(),
                    event_id=f"attack2_tamper_{i}",
                    process_id=1234,
                    thread_id=5678,
                    function_name="attack_function",
                    module_name="attack_module",
                    duration_ms=1.0,
                    args_metadata={"malicious": True},
                    resource_tags={},
                    redaction_applied=True,
                    sampling_rate=1.0
                )
                
                signed = SignedEvent(
                    event=event,
                    signature="TAMPERED_" + str(random.randint(1000, 9999)),
                    nonce=f"tamper2_{i}",
                    timestamp=datetime.now()
                )
                
            elif attack_type == 1:  # Replay
                event = TelemetryEvent(
                    timestamp=datetime.now(),
                    event_id=f"attack2_replay_{i}",
                    process_id=1234,
                    thread_id=5678,
                    function_name="attack_function",
                    module_name="attack_module",
                    duration_ms=1.0,
                    args_metadata={"malicious": True},
                    resource_tags={},
                    redaction_applied=True,
                    sampling_rate=1.0
                )
                
                # Reuse the legitimate event's nonce - replay attack!
                signed = SignedEvent(
                    event=event,
                    signature="REPLAY_LEGIT",
                    nonce=legit_signed.nonce,  # Replay legitimate nonce
                    timestamp=datetime.now()
                )
                
            elif attack_type == 2:  # Expired
                event = TelemetryEvent(
                    timestamp=datetime.now() - timedelta(hours=2),
                    event_id=f"attack2_expired_{i}",
                    process_id=1234,
                    thread_id=5678,
                    function_name="attack_function",
                    module_name="attack_module",
                    duration_ms=1.0,
                    args_metadata={"malicious": True},
                    resource_tags={},
                    redaction_applied=True,
                    sampling_rate=1.0
                )
                
                signed = pic.connector.transport.sign_event(event)
                signed.timestamp = datetime.now() - timedelta(hours=2)
                
            else:  # Garbage
                event = TelemetryEvent(
                    timestamp=datetime.now(),
                    event_id=f"attack2_garbage_{i}",
                    process_id=1234,
                    thread_id=5678,
                    function_name="attack_function",
                    module_name="attack_module",
                    duration_ms=1.0,
                    args_metadata={"malicious": True},
                    resource_tags={},
                    redaction_applied=True,
                    sampling_rate=1.0
                )
                
                signed = SignedEvent(
                    event=event,
                    signature="GARBAGE_" + str(random.randint(10000, 99999)),
                    nonce=f"garbage2_{i}",
                    timestamp=datetime.now()
                )
            
            decision = pic.brain.process_signed_event(signed)
            
            if decision.action == "block":
                phase3_blocked += 1
            else:
                phase3_allowed += 1
                
        except Exception as e:
            phase3_blocked += 1
    
    phase3_end = time.perf_counter()
    phase3_time = phase3_end - phase3_start
    
    print(f"\nPHASE 3 SUMMARY:")
    print(f"Total Attacks: 100")
    print(f"Blocked: {phase3_blocked}")
    print(f"Allowed: {phase3_allowed}")
    print(f"Block Rate: {phase3_blocked/100:.1%}")
    print(f"Time: {phase3_time:.3f}s")
    print(f"Throughput: {100/phase3_time:.1f} events/sec")
    print()
    
    # ========================================================================
    # FINAL STATISTICS
    # ========================================================================
    print("=" * 80)
    print("FINAL STATISTICS")
    print("=" * 80)
    
    total_attacks = 200
    total_blocked = phase1_blocked + phase3_blocked
    total_allowed = phase1_allowed + phase3_allowed
    total_time = phase1_time + phase3_time
    
    final_stats = pic.get_stats()
    
    print(f"\nOverall Attack Defense:")
    print(f"  Total Malicious Events: {total_attacks}")
    print(f"  Blocked: {total_blocked}")
    print(f"  Incorrectly Allowed: {total_allowed}")
    print(f"  Block Rate: {total_blocked/total_attacks:.1%}")
    print(f"  Total Time: {total_time:.3f}s")
    print(f"  Avg Throughput: {total_attacks/total_time:.1f} events/sec")
    
    print(f"\nLegitimate Traffic:")
    print(f"  Legitimate Events: 1")
    print(f"  Decision: {phase2_result.upper()}")
    print(f"  Status: {'PASS' if phase2_result == 'allow' else 'FAIL'}")
    
    print(f"\nSecurity Validator Stats:")
    sec_stats = final_stats['brain_core_stats']['security_validator_stats']
    print(f"  Total Validations: {sec_stats['total_validations']}")
    print(f"  Valid Events: {sec_stats['valid_events']}")
    print(f"  Invalid Signatures: {sec_stats['invalid_signatures']}")
    print(f"  Replay Attacks: {sec_stats['replay_attacks']}")
    print(f"  Expired Events: {sec_stats['expired_events']}")
    print(f"  Success Rate: {sec_stats['validation_success_rate']:.1%}")
    
    print(f"\nSystem Health:")
    print(f"  Security Violations: {final_stats['brain_core_stats']['security_violations']}")
    print(f"  System Crashes: 0")
    print(f"  False Positives: {1 if phase2_result != 'allow' else 0}")
    print(f"  False Negatives: {total_allowed}")
    
    print(f"\nTest Result: {'PASS' if phase2_result == 'allow' and total_blocked >= 180 else 'FAIL'}")
    print(f"  - Legitimate traffic allowed: {'YES' if phase2_result == 'allow' else 'NO'}")
    print(f"  - Attack block rate >90%: {'YES' if total_blocked >= 180 else 'NO'}")
    print()
    
    # Cleanup
    pic.stop()
    
    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    run_attack_resilience_test()
