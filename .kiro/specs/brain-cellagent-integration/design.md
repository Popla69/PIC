# Brain-CellAgent Integration - Design Document

## Overview

This document specifies the design for integrating SentinelBrain (BrainCore) with CellAgent to enable real-time anomaly detection and automated response. The integration establishes a secure, high-performance communication channel between the in-process instrumentation layer (CellAgent) and the analysis engine (BrainCore), enabling PIC to detect and block threats in real-time.

The design prioritizes:
- **Security**: Encrypted communication, HMAC authentication, replay protection
- **Performance**: <5ms median latency, <50ms p99 under attack
- **Resilience**: Fail-open/fail-closed modes, self-throttling, graceful degradation
- **Auditability**: Cryptographic audit trails for regulatory compliance

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Monitored Application                      │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                    CellAgent                            │ │
│  │                                                          │ │
│  │  ┌──────────────┐      ┌──────────────┐               │ │
│  │  │ @monitor     │      │  Rate        │               │ │
│  │  │ Decorator    │─────▶│  Limiter     │               │ │
│  │  └──────────────┘      └──────────────┘               │ │
│  │         │                      │                        │ │
│  │         ▼                      ▼                        │ │
│  │  ┌──────────────┐      ┌──────────────┐               │ │
│  │  │ Telemetry    │      │  HMAC        │               │ │
│  │  │ Generator    │─────▶│  Signer      │               │ │
│  │  └──────────────┘      └──────────────┘               │ │
│  │                               │                         │ │
│  │                               ▼                         │ │
│  │                        ┌──────────────┐                │ │
│  │                        │  Secure      │                │ │
│  │                        │  Transport   │                │ │
│  │                        └──────────────┘                │ │
│  └────────────────────────────┬───────────────────────────┘ │
└────────────────────────────────┼──────────────────────────────┘
                                 │
                                 │ TLS 1.3 + HMAC
                                 │ (In-process or IPC)
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────┐
│                      BrainCore Service                       │
│                                                              │
│  ┌──────────────┐      ┌──────────────┐                    │
│  │  HMAC        │      │  Replay      │                    │
│  │  Verifier    │─────▶│  Detector    │                    │
│  └──────────────┘      └──────────────┘                    │
│         │                      │                            │
│         ▼                      ▼                            │
│  ┌──────────────┐      ┌──────────────┐                    │
│  │  Event       │      │  Backpressure│                    │
│  │  Queue       │◀─────│  Controller  │                    │
│  └──────────────┘      └──────────────┘                    │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────┐      ┌──────────────┐                    │
│  │  Baseline    │      │  Anomaly     │                    │
│  │  Profiler    │─────▶│  Detector    │                    │
│  └──────────────┘      └──────────────┘                    │
│                               │                             │
│                               ▼                             │
│                        ┌──────────────┐                    │
│                        │  Decision    │                    │
│                        │  Engine      │                    │
│                        └──────────────┘                    │
│                               │                             │
│                               ▼                             │
│                        ┌──────────────┐                    │
│                        │  Audit       │                    │
│                        │  Logger      │                    │
│                        └──────────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

```
1. Function Call
   ↓
2. @monitor Decorator Intercepts
   ↓
3. Rate Limiter Check
   ↓
4. Telemetry Generation
   ↓
5. HMAC Signature
   ↓
6. Secure Transport (TLS)
   ↓
7. HMAC Verification
   ↓
8. Replay Detection
   ↓
9. Event Queue
   ↓
10. Baseline/Anomaly Analysis
    ↓
11. Decision (Allow/Block)
    ↓
12. Audit Logging
    ↓
13. Decision Return
    ↓
14. Enforcement (CellAgent)
    ↓
15. Function Execution or Exception
```

## Components and Interfaces

### 1. CellAgent Enhancements

#### 1.1 BrainConnector

**Purpose**: Manages connection to BrainCore and handles communication

```python
class BrainConnector:
    """Manages secure connection to BrainCore."""
    
    def __init__(
        self,
        brain_core: BrainCore,
        crypto_core: CryptoCore,
        config: PICConfig
    ):
        self.brain_core = brain_core
        self.crypto = crypto_core
        self.fail_mode = config.get("cellagent.fail_mode", "open")  # "open" or "closed"
        self.timeout_ms = config.get("cellagent.brain_timeout_ms", 10)
        self.retry_attempts = config.get("cellagent.retry_attempts", 3)
        self.retry_backoff_ms = config.get("cellagent.retry_backoff_ms", 100)
        
    def send_event(self, event: TelemetryEvent) -> Decision:
        """Send event to BrainCore and get decision."""
        
    def is_available(self) -> bool:
        """Check if BrainCore is available."""
        
    def handle_failure(self, error: Exception) -> Decision:
        """Handle BrainCore failure based on fail mode."""
```

#### 1.2 RateLimiter

**Purpose**: Prevents telemetry floods and implements self-throttling

```python
class RateLimiter:
    """Rate limiting and self-throttling for CellAgent."""
    
    def __init__(self, config: PICConfig):
        self.global_limit = config.get("cellagent.global_rate_limit", 10000)  # events/sec
        self.per_function_limit = config.get("cellagent.per_function_limit", 1000)
        self.throttle_threshold = config.get("cellagent.throttle_threshold", 0.8)
        self.window_seconds = config.get("cellagent.rate_window_seconds", 1)
        
        self._global_counter = 0
        self._function_counters: Dict[str, int] = {}
        self._window_start = time.time()
        self._throttled_functions: Set[str] = set()
        
    def check_rate(self, function_name: str) -> bool:
        """Check if event should be allowed based on rate limits."""
        
    def should_throttle(self) -> bool:
        """Check if system should enter throttling mode."""
        
    def get_adjusted_sampling_rate(self, base_rate: float) -> float:
        """Get adjusted sampling rate based on current load."""
```

#### 1.3 SecureTransport

**Purpose**: Handles HMAC signing and secure transmission

```python
class SecureTransport:
    """Secure transport layer for telemetry."""
    
    def __init__(self, crypto_core: CryptoCore):
        self.crypto = crypto_core
        self._nonce_cache: Set[str] = set()  # For replay detection
        self._nonce_cache_size = 10000
        
    def sign_event(self, event: TelemetryEvent) -> SignedEvent:
        """Sign event with HMAC and add nonce."""
        
    def verify_decision(self, decision: SignedDecision) -> Decision:
        """Verify decision signature from BrainCore."""
```

### 2. BrainCore Enhancements

#### 2.1 EventQueue

**Purpose**: Bounded queue with backpressure support

```python
class EventQueue:
    """Bounded queue for incoming telemetry events."""
    
    def __init__(self, config: PICConfig):
        self.max_size = config.get("brain.queue_size", 100000)
        self.backpressure_threshold = config.get("brain.backpressure_threshold", 0.8)
        self.drop_policy = config.get("brain.drop_policy", "oldest")  # "oldest" or "lowest_priority"
        
        self._queue: deque = deque(maxlen=self.max_size)
        self._lock = threading.Lock()
        
    def enqueue(self, event: TelemetryEvent) -> bool:
        """Add event to queue, returns False if backpressure should be applied."""
        
    def dequeue(self) -> Optional[TelemetryEvent]:
        """Remove and return next event from queue."""
        
    def should_apply_backpressure(self) -> bool:
        """Check if backpressure should be signaled to CellAgent."""
```

#### 2.2 SecurityValidator

**Purpose**: HMAC verification and replay detection

```python
class SecurityValidator:
    """Validates security properties of incoming events."""
    
    def __init__(self, crypto_core: CryptoCore):
        self.crypto = crypto_core
        self._seen_nonces: Set[str] = set()
        self._nonce_expiry_seconds = 300  # 5 minutes
        self._nonce_cleanup_interval = 60
        
    def verify_event(self, signed_event: SignedEvent) -> TelemetryEvent:
        """Verify HMAC signature and check for replay attacks."""
        
    def is_replay_attack(self, nonce: str, timestamp: datetime) -> bool:
        """Check if event is a replay attack."""
        
    def cleanup_old_nonces(self) -> None:
        """Remove expired nonces from cache."""
```

#### 2.3 BackpressureController

**Purpose**: Manages backpressure signaling to CellAgent

```python
class BackpressureController:
    """Controls backpressure signaling."""
    
    def __init__(self, event_queue: EventQueue):
        self.queue = event_queue
        self._backpressure_active = False
        
    def check_and_signal(self) -> BackpressureSignal:
        """Check queue state and return backpressure signal."""
        
    def get_recommended_rate(self) -> float:
        """Get recommended sampling rate for CellAgent."""
```

### 3. Integration Layer

#### 3.1 IntegratedPIC

**Purpose**: Unified initialization and lifecycle management

```python
class IntegratedPIC:
    """Integrated PIC system with CellAgent and BrainCore."""
    
    def __init__(self, config: Optional[PICConfig] = None):
        self.config = config or PICConfig.load()
        
        # Initialize crypto
        self.crypto = CryptoCore()
        
        # Initialize storage
        self.state_store = StateStore(self.config)
        self.audit_store = AuditStore(self.config, self.crypto)
        self.trace_store = TraceStore(self.config)
        
        # Initialize BrainCore
        self.brain = BrainCore(
            state_store=self.state_store,
            audit_store=self.audit_store,
            trace_store=self.trace_store,
            crypto_core=self.crypto
        )
        
        # Initialize CellAgent with Brain connection
        self.agent = CellAgent(config=self.config)
        self.agent.set_brain_connector(
            BrainConnector(self.brain, self.crypto, self.config)
        )
        
    def start(self) -> None:
        """Start all components."""
        
    def stop(self) -> None:
        """Stop all components gracefully."""
        
    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics."""
```

## Data Models

### SignedEvent

```python
@dataclass
class SignedEvent:
    """Telemetry event with HMAC signature."""
    event: TelemetryEvent
    signature: str  # HMAC-SHA256
    nonce: str  # UUID for replay protection
    timestamp: datetime  # Signature timestamp
```

### SignedDecision

```python
@dataclass
class SignedDecision:
    """Decision with HMAC signature."""
    decision: Decision
    signature: str  # HMAC-SHA256
    timestamp: datetime
```

### BackpressureSignal

```python
@dataclass
class BackpressureSignal:
    """Backpressure signal from BrainCore to CellAgent."""
    active: bool
    recommended_rate: float  # Recommended sampling rate (0.0-1.0)
    queue_utilization: float  # Current queue fill percentage
    reason: str  # Human-readable reason
```

### RateLimitStatus

```python
@dataclass
class RateLimitStatus:
    """Rate limiting status."""
    global_rate: int  # Current global events/sec
    throttled_functions: List[str]  # Functions currently throttled
    dropped_events: int  # Events dropped in current window
    throttling_active: bool
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Secure Communication

*For any* TelemetryEvent sent from CellAgent to BrainCore, the event must be signed with a valid HMAC signature that BrainCore can verify.

**Validates: Requirements 9.2, 10.2**

### Property 2: Replay Protection

*For any* nonce value, if an event with that nonce has been processed, then any subsequent event with the same nonce must be rejected.

**Validates: Requirements 9.4**

### Property 3: Fail-Safe Behavior

*For any* BrainCore failure, if fail-open mode is configured, then CellAgent must allow all traffic; if fail-closed mode is configured, then CellAgent must block all traffic.

**Validates: Requirements 4.1, 4.2**

### Property 4: Rate Limit Enforcement

*For any* function, if the function's event rate exceeds its configured limit, then CellAgent must throttle that specific function without affecting other functions.

**Validates: Requirements 14.1, 14.2**

### Property 5: Backpressure Response

*For any* backpressure signal from BrainCore, CellAgent must reduce its transmission rate to the recommended level within one sampling window.

**Validates: Requirements 12.3**

### Property 6: Decision Integrity

*For any* Decision returned by BrainCore, the decision must include a valid HMAC signature that CellAgent can verify.

**Validates: Requirements 10.2**

### Property 7: Audit Completeness

*For any* block decision enforced by CellAgent, an immutable audit record must be created with HMAC signature.

**Validates: Requirements 13.3, 13.4**

### Property 8: Performance Bounds

*For any* telemetry event under normal load, the round-trip time from CellAgent to BrainCore and back must be less than 10ms for 95% of events.

**Validates: Requirements 5.1**

### Property 9: Queue Bounded Growth

*For any* sequence of incoming events, the BrainCore event queue size must never exceed the configured maximum, with oldest events dropped when full.

**Validates: Requirements 12.1**

### Property 10: Graceful Degradation

*For any* error in the integration layer, the monitored application must continue executing without crashes.

**Validates: Requirements 8.1, 8.4**

## Error Handling

### Error Categories

1. **Communication Errors**
   - Timeout: Retry with exponential backoff
   - Connection refused: Enter fail-mode behavior
   - Network partition: Buffer and retry

2. **Security Errors**
   - Invalid signature: Reject event, log security alert
   - Replay attack: Reject event, increment attack counter
   - Key rotation failure: Use backup key, alert admin

3. **Performance Errors**
   - Queue full: Apply backpressure, drop low-priority events
   - High latency: Reduce sampling rate automatically
   - Memory pressure: Shed load, enter degraded mode

4. **Logic Errors**
   - Invalid event format: Log error, skip event
   - Unexpected exception: Catch, log, continue in fail-open

### Error Recovery Strategies

```python
class ErrorRecovery:
    """Error recovery strategies for integration."""
    
    def handle_communication_error(self, error: Exception) -> Decision:
        """Handle communication failures."""
        if isinstance(error, TimeoutError):
            return self._retry_with_backoff()
        elif isinstance(error, ConnectionError):
            return self._enter_fail_mode()
        else:
            return Decision.allow("Unknown error, fail-open")
    
    def handle_security_error(self, error: SecurityError) -> None:
        """Handle security violations."""
        self.audit_store.log_security_alert(error)
        self.metrics.increment("security_violations")
        
    def handle_performance_degradation(self) -> None:
        """Handle performance issues."""
        self.rate_limiter.enter_throttling_mode()
        self.agent.reduce_sampling_rate()
```

## Testing Strategy

### Unit Tests

1. **BrainConnector Tests**
   - Test successful event transmission
   - Test timeout handling
   - Test retry logic
   - Test fail-mode behavior

2. **RateLimiter Tests**
   - Test global rate limiting
   - Test per-function rate limiting
   - Test throttling activation
   - Test sampling rate adjustment

3. **SecurityValidator Tests**
   - Test HMAC verification
   - Test replay detection
   - Test nonce expiry
   - Test invalid signature handling

4. **EventQueue Tests**
   - Test bounded queue behavior
   - Test backpressure threshold
   - Test drop policies
   - Test concurrent access

### Property-Based Tests

1. **Property 1: Secure Communication**
   - Generate random TelemetryEvents
   - Sign with HMAC
   - Verify BrainCore accepts valid signatures
   - Verify BrainCore rejects invalid signatures

2. **Property 2: Replay Protection**
   - Generate events with duplicate nonces
   - Verify first event accepted
   - Verify duplicate rejected

3. **Property 4: Rate Limit Enforcement**
   - Generate high-rate event streams
   - Verify throttling activates
   - Verify other functions unaffected

4. **Property 8: Performance Bounds**
   - Generate normal load events
   - Measure round-trip latency
   - Verify 95th percentile < 10ms

### Integration Tests

1. **End-to-End Flow**
   - Monitor function → CellAgent → BrainCore → Decision → Enforcement
   - Verify complete flow works
   - Verify audit trail created

2. **Failure Scenarios**
   - BrainCore unavailable
   - Network partition
   - High load
   - Security attacks

3. **Performance Tests**
   - Sustained load (1000 events/sec)
   - Burst load (10000 events/sec)
   - Latency under load
   - Memory usage

## Security Considerations

### Threat Model

**Threats Mitigated:**
1. Man-in-the-middle attacks (TLS encryption)
2. Message tampering (HMAC signatures)
3. Replay attacks (nonce validation)
4. Telemetry floods (rate limiting)
5. Resource exhaustion (bounded queues)

**Threats Not Mitigated (Out of Scope):**
1. Compromised CellAgent process
2. Kernel-level attacks
3. Side-channel attacks
4. Physical access attacks

### Key Management

```python
class KeyManager:
    """Manages cryptographic keys for integration."""
    
    def __init__(self, config: PICConfig):
        self.primary_key = self._load_or_generate_key("primary")
        self.backup_key = self._load_or_generate_key("backup")
        self.rotation_interval_days = config.get("crypto.rotation_days", 90)
        
    def rotate_keys(self) -> None:
        """Rotate keys: backup becomes primary, generate new backup."""
        
    def get_active_key(self) -> bytes:
        """Get currently active key for signing."""
        
    def verify_with_any_key(self, data: bytes, signature: str) -> bool:
        """Verify signature with primary or backup key."""
```

## Performance Optimization

### Optimization Strategies

1. **Batching**: Group multiple events for single transmission
2. **Compression**: Compress event payloads for large batches
3. **Connection Pooling**: Reuse connections to BrainCore
4. **Async Processing**: Non-blocking event transmission
5. **Caching**: Cache recent decisions for identical events

### Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Median Latency | <5ms | p50 round-trip time |
| P99 Latency (normal) | <10ms | p99 under 1000 events/sec |
| P99 Latency (attack) | <50ms | p99 under 10000 events/sec |
| Throughput | 10,000 events/sec | Sustained rate |
| Memory Overhead | <100MB | Per CellAgent instance |
| CPU Overhead | <5% | Additional CPU usage |

## Deployment Considerations

### Configuration

```yaml
# cellagent.yaml
cellagent:
  fail_mode: "open"  # or "closed"
  brain_timeout_ms: 10
  retry_attempts: 3
  retry_backoff_ms: 100
  global_rate_limit: 10000
  per_function_limit: 1000
  throttle_threshold: 0.8

# brain.yaml
brain:
  queue_size: 100000
  backpressure_threshold: 0.8
  drop_policy: "oldest"
  worker_threads: 4
  max_worker_threads: 16

# crypto.yaml
crypto:
  rotation_days: 90
  nonce_expiry_seconds: 300
  signature_algorithm: "HMAC-SHA256"
```

### Monitoring

**Key Metrics to Monitor:**
1. Event transmission rate
2. Decision latency (p50, p95, p99)
3. Queue utilization
4. Throttling events
5. Security violations
6. Error rates
7. Backpressure activations

### Rollout Strategy

**Phase 1: Observe-Only (Week 1)**
- Deploy integration in observe-only mode
- Collect metrics, no enforcement
- Validate performance and stability

**Phase 2: Gradual Enforcement (Week 2-3)**
- Enable enforcement for 10% of traffic
- Monitor false positive rate
- Adjust thresholds as needed
- Gradually increase to 100%

**Phase 3: Full Production (Week 4+)**
- 100% enforcement
- Continuous monitoring
- Regular security audits

## Future Enhancements

### v1.1 Enhancements
1. **mTLS Support**: Mutual TLS for stronger authentication
2. **Compression**: Event payload compression for bandwidth
3. **Adaptive Throttling**: ML-based throttling decisions
4. **Multi-Brain**: Support for multiple BrainCore instances

### v2.0 Enhancements
1. **Distributed Tracing**: OpenTelemetry integration
2. **Advanced Queuing**: Priority queues with QoS
3. **Smart Caching**: Decision caching with TTL
4. **Federation**: Multi-datacenter Brain federation

---

*This design provides enterprise-grade security, performance, and resilience for the Brain-CellAgent integration, enabling PIC to detect and block threats in real-time while maintaining regulatory compliance.*
