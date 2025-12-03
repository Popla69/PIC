# Brain-CellAgent Integration Guide

## Overview

The Brain-CellAgent integration connects PIC's telemetry collection layer (CellAgent) with its anomaly detection engine (BrainCore) to enable real-time security decisions. This integration provides:

- **Real-time anomaly detection**: Events are analyzed as they occur
- **Secure communication**: HMAC signatures and replay protection
- **Automated response**: Anomalous behavior is automatically blocked
- **Performance optimization**: Rate limiting and backpressure handling
- **Enterprise security**: Audit logging and graceful degradation

## Architecture

```
┌─────────────────┐
│  Application    │
│   Functions     │
└────────┬────────┘
         │ @monitor decorator
         ▼
┌─────────────────┐
│   CellAgent     │◄──── Rate Limiter
│  (Telemetry)    │
└────────┬────────┘
         │ TelemetryEvent
         ▼
┌─────────────────┐
│ BrainConnector  │◄──── SecureTransport (HMAC)
│  (Secure Comm)  │
└────────┬────────┘
         │ SignedEvent
         ▼
┌─────────────────┐
│   BrainCore     │◄──── SecurityValidator
│  (Detection)    │
└────────┬────────┘
         │ Decision
         ▼
┌─────────────────┐
│    Effector     │
│  (Enforcement)  │
└─────────────────┘
```

## Quick Start

### Basic Usage

```python
from pic.integrated import IntegratedPIC

# Initialize integrated system
pic = IntegratedPIC(data_dir="pic_data")
pic.start()

# Monitor your functions
@pic.agent.monitor
def process_payment(amount, user_id):
    # Your application logic
    return {"status": "success"}

# Use normally - PIC works in the background
result = process_payment(100.0, "user_123")

# Cleanup
pic.stop()
```

### Context Manager

```python
with IntegratedPIC(data_dir="pic_data") as pic:
    @pic.agent.monitor
    def sensitive_operation():
        return "data"
    
    result = sensitive_operation()
```

## Components

### 1. IntegratedPIC

The main entry point that initializes and wires all components together.

**Features:**
- Automatic component initialization
- Lifecycle management (start/stop)
- Unified statistics API
- Configuration management

**Example:**
```python
pic = IntegratedPIC(
    config=custom_config,  # Optional
    data_dir="pic_data"    # Data storage directory
)
```

### 2. CellAgent

Collects telemetry from monitored functions.

**Features:**
- Decorator-based instrumentation
- Configurable sampling rates
- PII redaction
- Rate limiting
- Performance tracking

**Configuration:**
```python
config = PICConfig.load()
config.set("cellagent.sampling_rate", 0.1)  # 10% sampling
config.set("cellagent.global_rate_limit", 10000)  # events/sec
config.set("cellagent.per_function_rate_limit", 1000)
```

### 3. BrainConnector

Manages secure communication between CellAgent and BrainCore.

**Features:**
- HMAC signing of events
- Retry logic with exponential backoff
- Fail-open and fail-closed modes
- Timeout handling
- Connection health checks

**Configuration:**
```python
config.set("cellagent.fail_mode", "open")  # or "closed"
config.set("cellagent.brain_timeout_ms", 10)
config.set("cellagent.retry_attempts", 3)
config.set("cellagent.retry_backoff_ms", 100)
```

### 4. SecureTransport

Provides cryptographic security for event transmission.

**Features:**
- HMAC-SHA256 signatures
- Nonce-based replay protection
- Automatic nonce cleanup
- Signature verification

**Security Properties:**
- Events cannot be tampered with (HMAC integrity)
- Events cannot be replayed (nonce tracking)
- Events expire after 5 minutes (timestamp validation)

### 5. BrainCore

Processes events and makes security decisions.

**Features:**
- Baseline profiling
- Anomaly detection
- Security validation
- Decision making
- Audit logging

**Pipeline:**
1. Verify event signature (SecurityValidator)
2. Check for replay attacks
3. Store in trace buffer
4. Compare against baseline
5. Compute anomaly score
6. Make allow/block decision
7. Log to audit store

### 6. SecurityValidator

Validates cryptographic properties of incoming events.

**Features:**
- HMAC signature verification
- Replay attack detection
- Timestamp freshness validation
- Automatic nonce expiry

**Statistics:**
```python
stats = pic.brain.security_validator.get_stats()
# {
#   "total_validations": 1000,
#   "valid_events": 998,
#   "invalid_signatures": 1,
#   "replay_attacks": 1,
#   "nonce_cache_size": 998
# }
```

### 7. RateLimiter

Prevents telemetry floods and manages system load.

**Features:**
- Global rate limiting (events/sec across all functions)
- Per-function rate limiting
- Automatic self-throttling
- Sliding window algorithm
- Dynamic sampling rate adjustment

**Example:**
```python
# Rate limiter automatically throttles high-rate functions
for i in range(10000):
    fast_function()  # Some calls will be throttled

stats = pic.agent.rate_limiter.get_stats()
print(f"Throttled: {stats['total_throttled']}")
```

## Security Features

### HMAC Authentication

All events are signed with HMAC-SHA256:

```python
# Automatic in SecureTransport
signed_event = transport.sign_event(event)
# signed_event.signature = HMAC(event + nonce + timestamp)
```

### Replay Protection

Nonces prevent replay attacks:

```python
# Each event gets unique nonce
nonce = str(uuid.uuid4())

# Nonces are tracked and expire after 5 minutes
if nonce in seen_nonces:
    return False  # Replay attack detected
```

### Fail Modes

**Fail-Open (Default):**
- On error, allow traffic to continue
- Prioritizes availability
- Logs errors for investigation

**Fail-Closed:**
- On error, block traffic
- Prioritizes security
- Use for critical systems

```python
config.set("cellagent.fail_mode", "closed")
```

### Key Rotation

Keys can be rotated for enhanced security:

```python
from pic.crypto.key_manager import KeyManager

key_manager = KeyManager(
    key_dir="pic_keys",
    rotation_days=30
)

# Check if rotation is due
if key_manager.should_rotate():
    key_manager.rotate_keys()
```

## Performance Features

### Rate Limiting

Prevents system overload:

```python
# Global limit: 10,000 events/sec
# Per-function limit: 1,000 events/sec

# Automatically throttles when limits exceeded
rate_limiter = RateLimiter(
    global_limit=10000,
    per_function_limit=1000
)
```

### Backpressure Handling

Adapts to system load:

```python
# EventQueue monitors utilization
queue = EventQueue(
    max_size=10000,
    backpressure_threshold=0.8  # 80%
)

# BackpressureController adjusts sampling rate
controller = BackpressureController(queue)
signal = controller.check_and_signal()

if signal.active:
    # Reduce sampling rate
    agent.sampling_rate = signal.recommended_rate
```

### Performance Monitoring

Track latency metrics:

```python
stats = pic.agent.get_performance_stats()
# {
#   "p50_latency_ms": 2.5,
#   "p95_latency_ms": 8.3,
#   "p99_latency_ms": 15.7,
#   "sample_count": 1000
# }
```

## Error Handling

### Graceful Degradation

PIC never crashes your application:

```python
@pic.agent.monitor
def risky_function():
    raise ValueError("Something went wrong")

# Application error is raised normally
# PIC instrumentation errors are caught and logged
try:
    risky_function()
except ValueError:
    # Handle your application error
    pass
```

### Error Recovery

Automatic error tracking and recovery:

```python
from pic.brain.error_recovery import ErrorRecovery

recovery = ErrorRecovery(
    error_threshold=10,           # Errors before alert
    time_window_seconds=60,       # Time window
    degraded_mode_threshold=50    # Errors to enter degraded mode
)

# Handles different error types
recovery.handle_communication_error(error)
recovery.handle_security_error(error)
recovery.handle_performance_degradation("latency", 100, 50)

# Check system state
if recovery.is_degraded():
    print("System in degraded mode")
```

## Statistics and Monitoring

### Comprehensive Statistics

```python
stats = pic.get_stats()

# System state
print(f"Running: {stats['running']}")

# Agent statistics
agent_stats = stats['agent_stats']
print(f"Total events: {agent_stats['total_events']}")
print(f"Sampling rate: {agent_stats['sampling_rate']}")
print(f"Throttled: {agent_stats['throttle_events']}")

# Brain connector statistics
brain_stats = stats['brain_stats']
print(f"Requests: {brain_stats['total_requests']}")
print(f"Success rate: {brain_stats['success_rate']}")

# Brain core statistics
core_stats = stats['brain_core_stats']
print(f"Events processed: {core_stats['events_processed']}")
print(f"Security violations: {core_stats['security_violations']}")

# Performance metrics
perf = agent_stats['performance']
print(f"P50: {perf['p50_latency_ms']}ms")
print(f"P95: {perf['p95_latency_ms']}ms")
print(f"P99: {perf['p99_latency_ms']}ms")
```

## Configuration

### Complete Configuration Example

```python
from pic.config import PICConfig

config = PICConfig.load()

# CellAgent settings
config.set("cellagent.sampling_rate", 0.1)
config.set("cellagent.buffer_size", 10000)
config.set("cellagent.global_rate_limit", 10000)
config.set("cellagent.per_function_rate_limit", 1000)
config.set("cellagent.observe_only", False)

# Brain connector settings
config.set("cellagent.fail_mode", "open")
config.set("cellagent.brain_timeout_ms", 10)
config.set("cellagent.retry_attempts", 3)
config.set("cellagent.retry_backoff_ms", 100)

# Trace storage
config.set("trace.capacity_per_function", 1000)

# Use custom config
pic = IntegratedPIC(config=config)
```

## Best Practices

### 1. Start with Observe-Only Mode

```python
config.set("cellagent.observe_only", True)
pic = IntegratedPIC(config=config)

# Monitor without blocking
# Review detection accuracy
# Tune thresholds
```

### 2. Use Appropriate Sampling Rates

```python
# Development: High sampling for testing
config.set("cellagent.sampling_rate", 1.0)

# Production: Lower sampling for performance
config.set("cellagent.sampling_rate", 0.1)

# Critical systems: Moderate sampling
config.set("cellagent.sampling_rate", 0.5)
```

### 3. Monitor Performance Metrics

```python
# Regularly check performance
stats = pic.agent.get_performance_stats()

if stats['p99_latency_ms'] > 50:
    # Reduce sampling rate
    pic.agent.sampling_rate *= 0.5
```

### 4. Handle Security Violations

```python
# Monitor security stats
sec_stats = pic.brain.security_validator.get_stats()

if sec_stats['replay_attacks'] > 0:
    # Investigate potential attack
    print("Replay attacks detected!")
```

### 5. Use Fail-Closed for Critical Systems

```python
# For payment processing, authentication, etc.
config.set("cellagent.fail_mode", "closed")
```

## Troubleshooting

### High Latency

**Symptom:** P99 latency > 50ms

**Solutions:**
1. Reduce sampling rate
2. Increase rate limits
3. Check Brain timeout settings
4. Enable backpressure handling

### Events Not Being Processed

**Symptom:** `events_processed` = 0

**Solutions:**
1. Check sampling rate (may be too low)
2. Verify Brain connector is set
3. Check rate limiter stats
4. Review error logs

### Security Violations

**Symptom:** `security_violations` > 0

**Solutions:**
1. Check for replay attacks
2. Verify HMAC keys are synchronized
3. Check timestamp synchronization
4. Review nonce cache settings

### Memory Usage

**Symptom:** High memory consumption

**Solutions:**
1. Reduce buffer sizes
2. Lower nonce cache size
3. Decrease trace capacity
4. Enable more aggressive cleanup

## Advanced Topics

### Custom Decision Logic

```python
# Extend BrainCore for custom decisions
class CustomBrainCore(BrainCore):
    def process_event(self, event):
        # Custom logic
        if event.function_name == "critical_function":
            # Always allow critical functions
            return Decision.allow("Critical function")
        
        # Default processing
        return super().process_event(event)
```

### Custom Security Validation

```python
# Add custom security checks
class CustomSecurityValidator(SecurityValidator):
    def verify_event(self, signed_event):
        # Custom validation
        if not self.check_custom_property(signed_event):
            return False, "Custom check failed"
        
        # Default validation
        return super().verify_event(signed_event)
```

### Integration with External Systems

```python
# Send alerts to external monitoring
def on_security_violation(event):
    # Send to SIEM
    siem.send_alert({
        "type": "security_violation",
        "event": event.to_dict()
    })

# Hook into BrainCore
pic.brain._log_security_alert = on_security_violation
```

## Performance Benchmarks

Typical performance characteristics:

- **Median latency (P50):** < 5ms
- **P95 latency:** < 20ms
- **P99 latency:** < 50ms (under normal load)
- **Throughput:** 10,000+ events/sec
- **Memory overhead:** < 100MB
- **CPU overhead:** < 2%

## See Also

- [Architecture Overview](architecture.md)
- [Security Guide](security.md)
- [Performance Tuning](performance.md)
- [API Reference](api_reference.md)
