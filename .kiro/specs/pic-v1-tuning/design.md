# Design Document: PIC v1 Tuning & Optimization

## Overview

This design implements a comprehensive tuning system for PIC v1 to address accuracy issues identified in MIPAB-11 testing. The system reduces false positives from 28.3% to <5%, increases malicious block rate from 71.6% to >92%, and maintains excellent performance (P95 < 10ms).

The design follows a multi-layered approach:
1. Pattern memory for fast legitimate traffic recognition
2. Adaptive thresholds that adjust based on traffic patterns
3. Entropy-based detection for sophisticated attacks
4. Multi-layer signature validation
5. Continuous micro-mutation to prevent adversarial learning

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Incoming Event                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Pattern Memory Cache (Fast Path)                │
│  - Check if event matches known legitimate pattern           │
│  - 85% fuzzy match threshold                                 │
│  - TTL: 1800s                                                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                ┌──────┴──────┐
                │   Match?    │
                └──────┬──────┘
                       │
         ┌─────────────┴─────────────┐
         │ Yes                       │ No
         ▼                           ▼
    ┌────────┐          ┌────────────────────────────┐
    │ ALLOW  │          │  Multi-Layer Validation    │
    └────────┘          │  1. Hard Signature         │
                        │  2. Soft Signature         │
                        │  3. Behavioral Signature   │
                        └────────────┬───────────────┘
                                     │
                        ┌────────────┴────────────┐
                        │  Entropy & Timing Check │
                        │  - Shannon entropy      │
                        │  - Timing variance      │
                        └────────────┬────────────┘
                                     │
                        ┌────────────┴────────────┐
                        │  Anomaly Scoring        │
                        │  - Adaptive threshold   │
                        │  - Reputation bonus     │
                        └────────────┬────────────┘
                                     │
                        ┌────────────┴────────────┐
                        │  Decision Logic         │
                        │  - Score < 0.65: ALLOW  │
                        │  - 0.65-0.75: SOFT-ALLOW│
                        │  - Score > 0.75: BLOCK  │
                        └────────────┬────────────┘
                                     │
                        ┌────────────┴────────────┐
                        │  Micro-Mutation Engine  │
                        │  (every 50 events)      │
                        └─────────────────────────┘
```

### Component Interaction

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Pattern    │────▶│   Entropy    │────▶│   Anomaly    │
│   Memory     │     │   Analyzer   │     │   Scorer     │
└──────────────┘     └──────────────┘     └──────────────┘
                                                   │
                                                   ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Reputation  │────▶│   Decision   │────▶│   Metrics    │
│   Manager    │     │   Engine     │     │   Collector  │
└──────────────┘     └──────────────┘     └──────────────┘
                                                   │
                                                   ▼
                                          ┌──────────────┐
                                          │ Micro-Mutation│
                                          │   Engine     │
                                          └──────────────┘
```

## Components and Interfaces

### 1. Pattern Memory Cache

**Purpose**: Fast-path recognition of known legitimate patterns

**Interface**:
```python
class PatternMemoryCache:
    def __init__(self, ttl_seconds: int = 1800, max_size: int = 10000):
        """Initialize pattern cache with TTL and capacity."""
        
    def add_pattern(self, event: TelemetryEvent, signature: str) -> None:
        """Store approved legitimate pattern."""
        
    def check_match(self, event: TelemetryEvent, threshold: float = 0.85) -> Optional[str]:
        """Check if event matches cached pattern with fuzzy matching."""
        
    def evict_expired(self) -> int:
        """Remove expired patterns, return count evicted."""
        
    def get_stats(self) -> Dict[str, Any]:
        """Return cache statistics (hits, misses, size)."""
```

**Implementation Details**:
- Uses LSH (Locality-Sensitive Hashing) for fast fuzzy matching
- Stores behavioral fingerprints: (function_name, module, duration_range, arg_types)
- LRU eviction when capacity reached
- Background thread for TTL cleanup every 60 seconds

### 2. Entropy Analyzer

**Purpose**: Detect attacks based on payload entropy and timing patterns

**Interface**:
```python
class EntropyAnalyzer:
    def __init__(self, entropy_min: float = 2.4, timing_variance_min: float = 0.003):
        """Initialize with entropy and timing thresholds."""
        
    def calculate_entropy(self, data: Union[str, bytes, Dict]) -> float:
        """Calculate Shannon entropy of payload."""
        
    def analyze_timing(self, events: List[TelemetryEvent]) -> float:
        """Calculate timing variance from recent events."""
        
    def is_suspicious(self, event: TelemetryEvent, history: List[TelemetryEvent]) -> Tuple[bool, float]:
        """Return (is_suspicious, risk_score)."""
```

**Implementation Details**:
- Shannon entropy: H(X) = -Σ p(x) * log2(p(x))
- Timing variance: σ² = Σ(t_i - μ)² / n
- Caches recent event history (last 100 events per source)
- Returns risk score 0.0-1.0

### 3. Multi-Layer Signature Validator

**Purpose**: Validate events using multiple signature methods

**Interface**:
```python
class MultiLayerValidator:
    def __init__(self, modes: List[str] = ["hard", "soft", "behavioral"]):
        """Initialize with signature validation modes."""
        
    def validate_hard(self, event: SignedEvent) -> ValidationResult:
        """Exact HMAC signature validation."""
        
    def validate_soft(self, event: SignedEvent) -> ValidationResult:
        """Partial signature matching (shape, structure)."""
        
    def validate_behavioral(self, event: SignedEvent, history: List[TelemetryEvent]) -> ValidationResult:
        """Behavioral pattern validation."""
        
    def validate(self, event: SignedEvent, history: List[TelemetryEvent]) -> ValidationResult:
        """Try all validation modes in order."""
```

**Implementation Details**:
- Hard: Standard HMAC-SHA256 validation
- Soft: Validates signature structure, timestamp proximity, nonce format
- Behavioral: Checks if timing/entropy/patterns match historical behavior
- Falls through modes until one succeeds or all fail

### 4. Adaptive Anomaly Scorer

**Purpose**: Score events with adaptive thresholds

**Interface**:
```python
class AdaptiveAnomalyScorer:
    def __init__(self, base_threshold: float = 0.65, soft_allow_prob: float = 0.15):
        """Initialize with base threshold and soft-allow probability."""
        
    def score_event(self, event: TelemetryEvent, context: ScoringContext) -> float:
        """Calculate anomaly score 0.0-1.0."""
        
    def adjust_threshold(self, delta: float) -> None:
        """Adjust threshold by delta (for micro-mutation)."""
        
    def get_decision(self, score: float, reputation: float) -> Decision:
        """Convert score to decision (allow/soft-allow/block)."""
```

**Implementation Details**:
- Base score from statistical anomaly detection
- Adjustments: +0.3 for low entropy, +0.2 for timing anomalies
- Reputation bonus: -0.1 for high reputation users
- Soft-allow zone: 0.65-0.75 with 15% random allowance

### 5. Reputation Manager

**Purpose**: Track user reputation for adaptive thresholding

**Interface**:
```python
class ReputationManager:
    def __init__(self, decay_interval: int = 2400):
        """Initialize with reputation decay interval."""
        
    def update_reputation(self, user_id: str, is_legitimate: bool) -> float:
        """Update reputation based on event legitimacy."""
        
    def get_reputation(self, user_id: str) -> float:
        """Get current reputation score 0.0-1.0."""
        
    def decay_reputations(self) -> None:
        """Apply time-based decay to all reputations."""
```

**Implementation Details**:
- Reputation = (legitimate_count / total_count) * 0.9 + 0.1
- Decay: reputation *= 0.9 every 2400 seconds
- Sliding window: last 100 events per user
- New users start at 0.5 (neutral)

### 6. Micro-Mutation Engine

**Purpose**: Continuously adapt detection rules to prevent adversarial learning

**Interface**:
```python
class MicroMutationEngine:
    def __init__(self, mutation_interval: int = 50):
        """Initialize with mutation interval (events)."""
        
    def should_mutate(self, event_count: int) -> bool:
        """Check if mutation should occur."""
        
    def mutate_thresholds(self, scorer: AdaptiveAnomalyScorer) -> None:
        """Apply small random adjustments to thresholds."""
        
    def mutate_patterns(self, cache: PatternMemoryCache) -> None:
        """Add noise to pattern matching."""
        
    def mutate_lookup_tables(self, validator: MultiLayerValidator) -> None:
        """Shuffle pattern lookup ordering."""
```

**Implementation Details**:
- Threshold mutation: ±5% random adjustment
- Pattern noise: ±2% to similarity scores
- Lookup shuffle: Randomize validation order
- Logs all mutations for audit trail

### 7. Configuration Manager

**Purpose**: Manage tuning parameters with validation

**Interface**:
```python
class TuningConfig:
    anomaly_threshold: float = 0.65
    entropy_min: float = 2.4
    timing_variance_min: float = 0.003
    soft_allow_probability: float = 0.15
    signature_modes: List[str] = ["hard", "soft", "behavioral"]
    micro_mutation_interval: int = 50
    pattern_memory_cache_ttl_s: int = 1800
    classifier_queue_size: int = 128
    replay_protection_level: str = "aggressive"
    legit_reputation_decay_s: int = 2400
    
    def validate(self) -> List[str]:
        """Validate configuration, return list of errors."""
        
    def apply(self, brain: BrainCore) -> None:
        """Apply configuration to running system."""
```

## Data Models

### Pattern Fingerprint

```python
@dataclass
class PatternFingerprint:
    function_name: str
    module_name: str
    duration_range: Tuple[float, float]  # (min, max)
    arg_types: List[str]
    resource_signature: str  # Hash of resource tags
    timestamp: datetime
    hit_count: int
```

### Validation Result

```python
@dataclass
class ValidationResult:
    is_valid: bool
    confidence: float  # 0.0-1.0
    method: str  # "hard", "soft", "behavioral"
    reason: Optional[str]
```

### Scoring Context

```python
@dataclass
class ScoringContext:
    event: TelemetryEvent
    history: List[TelemetryEvent]
    reputation: float
    entropy: float
    timing_variance: float
    validation_result: ValidationResult
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Pattern Cache Consistency
*For any* legitimate event that is approved, if it is added to the pattern cache, then querying the cache with a similar event (≥85% match) should return a match within the TTL period.
**Validates: Requirements 1.1, 1.2**

### Property 2: Threshold Monotonicity
*For any* anomaly score, if score < threshold_low, the decision is allow; if threshold_low ≤ score < threshold_high, the decision is soft-allow; if score ≥ threshold_high, the decision is block.
**Validates: Requirements 2.1, 2.2, 2.3**

### Property 3: Entropy Detection Accuracy
*For any* payload with entropy below the minimum threshold, the system should mark it as high-risk and increase the anomaly score.
**Validates: Requirements 3.1, 3.2, 3.4**

### Property 4: Signature Validation Fallback
*For any* event, if hard signature validation fails, the system should attempt soft validation; if soft fails, it should attempt behavioral validation before blocking.
**Validates: Requirements 4.1, 4.2, 4.3, 4.4**

### Property 5: Micro-Mutation Periodicity
*For any* sequence of N events where N is a multiple of the mutation interval, the system should trigger exactly N/interval mutations.
**Validates: Requirements 5.1**

### Property 6: Reputation Monotonic Increase
*For any* user sending only legitimate traffic, their reputation score should monotonically increase (or stay constant) until reaching the maximum.
**Validates: Requirements 6.1, 6.2**

### Property 7: Replay Protection Uniqueness
*For any* nonce that has been used, attempting to reuse it within the protection window should result in immediate blocking.
**Validates: Requirements 7.1, 7.2**

### Property 8: Latency Bound
*For any* event processed through the tuned system, the P95 latency should not exceed 10ms under normal load.
**Validates: Requirements 8.5**

### Property 9: Configuration Validation
*For any* configuration update, if the parameters are invalid, the system should reject the update and maintain the previous valid configuration.
**Validates: Requirements 9.1, 9.2**

### Property 10: Metrics Accuracy
*For any* batch of processed events, the calculated false positive rate should equal (false_positives / legitimate_events) and the false negative rate should equal (false_negatives / malicious_events).
**Validates: Requirements 10.1, 10.2**

## Error Handling

### Pattern Cache Errors
- **Cache Full**: Evict LRU entries, log warning if eviction rate > 10%
- **Corruption**: Clear cache, rebuild from recent approved events
- **Match Timeout**: Skip cache check, proceed to full validation

### Entropy Calculation Errors
- **Invalid Data**: Return neutral entropy (4.0), log warning
- **Timeout**: Skip entropy check, proceed with other indicators
- **Overflow**: Clamp to valid range [0.0, 8.0]

### Validation Errors
- **All Modes Fail**: Block event, log detailed failure reasons
- **Timeout**: Fail-secure (block), increment timeout counter
- **Exception**: Block event, log stack trace, alert operator

### Reputation Errors
- **Unknown User**: Start with neutral reputation (0.5)
- **Corruption**: Reset user reputation to neutral
- **Decay Failure**: Log error, continue with stale reputation

### Mutation Errors
- **Invalid Adjustment**: Skip mutation, log error
- **Threshold Out of Bounds**: Clamp to valid range [0.3, 0.9]
- **Exception**: Skip mutation cycle, alert operator

## Testing Strategy

### Unit Testing
- Pattern cache: add, match, evict, TTL expiration
- Entropy analyzer: various payload types, edge cases
- Signature validator: each mode independently
- Reputation manager: score updates, decay
- Micro-mutation: threshold adjustments, randomization

### Property-Based Testing
- Use Hypothesis for Python
- Generate random events, verify properties hold
- Test with 1000+ iterations per property
- Each property test tagged with requirement reference

### Integration Testing
- Full pipeline: event → decision with all components
- Performance testing: latency under load
- Accuracy testing: known legitimate/malicious datasets
- Stress testing: high throughput, burst traffic

### Regression Testing
- Re-run MIPAB-11 with tuned system
- Compare metrics: FP rate, FN rate, latency
- Target: FP < 5%, malicious block > 92%, P95 < 10ms

## Performance Considerations

### Optimization Targets
- Pattern cache lookup: < 0.5ms (hash table + LSH)
- Entropy calculation: < 1ms (optimized Shannon entropy)
- Signature validation: < 2ms per mode
- Reputation lookup: < 0.1ms (in-memory hash map)
- Total P95 latency: < 10ms

### Memory Management
- Pattern cache: ~10MB for 10,000 patterns
- Reputation store: ~5MB for 50,000 users
- Event history: ~20MB for 100 events × 1000 users
- Total: ~35MB additional memory

### Concurrency
- Pattern cache: Read-write lock for thread safety
- Reputation manager: Per-user locks for updates
- Micro-mutation: Separate thread, non-blocking
- Metrics collection: Lock-free counters

## Deployment Strategy

### Phased Rollout
1. **Phase 1**: Deploy with conservative thresholds (0.75)
2. **Phase 2**: Enable pattern cache, monitor hit rate
3. **Phase 3**: Lower threshold to 0.65, enable soft-allow
4. **Phase 4**: Enable micro-mutation
5. **Phase 5**: Full production with all features

### Monitoring
- Dashboard: FP rate, FN rate, latency, throughput
- Alerts: FP rate > 5%, latency P95 > 15ms
- Logs: All decisions, mutations, configuration changes
- Metrics export: Prometheus format

### Rollback Plan
- Feature flags for each component
- Instant rollback to previous thresholds
- Preserve pattern cache and reputation data
- Automated rollback if FP rate > 10%
