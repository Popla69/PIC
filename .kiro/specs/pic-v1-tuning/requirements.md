# Requirements Document: PIC v1 Tuning & Optimization

## Introduction

Based on MIPAB-11 test results, PIC v1 requires tuning to address high false positive rates (28.3%), low malicious block rates (71.6%), and improve overall accuracy while maintaining excellent performance characteristics. This feature implements adaptive tuning mechanisms to achieve production-grade accuracy.

## Glossary

- **PIC**: Polymorphic Immune Core - the security system being tuned
- **False Positive (FP)**: Legitimate event incorrectly blocked
- **False Negative (FN)**: Malicious event incorrectly allowed
- **Pattern Memory Cache**: Short-term storage of approved legitimate behavior patterns
- **Micro-Mutation**: Small, frequent adjustments to detection thresholds
- **Entropy**: Measure of randomness/unpredictability in data
- **Soft-Allow Mode**: Permissive mode that logs suspicious events instead of blocking
- **Signature Modes**: Different levels of signature matching (hard/soft/behavioral)

## Requirements

### Requirement 1: Pattern Memory Cache

**User Story:** As a security operator, I want the system to remember recently approved legitimate patterns, so that recurring legitimate behavior is not repeatedly flagged as suspicious.

#### Acceptance Criteria

1. WHEN a legitimate event is approved THEN the system SHALL store its behavioral signature in the pattern memory cache
2. WHEN an incoming event matches a cached pattern THEN the system SHALL allow it without full analysis
3. WHEN a cached pattern exceeds its TTL (1800 seconds) THEN the system SHALL remove it from the cache
4. WHEN the cache reaches capacity THEN the system SHALL evict the least recently used patterns
5. WHEN pattern matching occurs THEN the system SHALL use fuzzy matching with 85% similarity threshold

### Requirement 2: Adaptive Anomaly Thresholds

**User Story:** As a security operator, I want the system to use appropriate sensitivity levels for different traffic types, so that legitimate users are not blocked while attacks are still detected.

#### Acceptance Criteria

1. WHEN evaluating legitimate-like traffic THEN the system SHALL use an anomaly threshold of 0.65
2. WHEN the anomaly score is between 0.65 and 0.75 THEN the system SHALL apply soft-allow mode
3. WHEN the anomaly score exceeds 0.75 THEN the system SHALL block the event
4. WHEN soft-allow mode is active THEN the system SHALL log the event for review but allow it to proceed
5. WHEN soft-allow probability is configured THEN the system SHALL randomly allow 15% of borderline events for adaptive learning

### Requirement 3: Entropy-Based Attack Detection

**User Story:** As a security operator, I want the system to detect attacks based on payload entropy and timing patterns, so that sophisticated evasion attempts are identified.

#### Acceptance Criteria

1. WHEN analyzing an event payload THEN the system SHALL calculate Shannon entropy
2. WHEN payload entropy is below 2.4 bits THEN the system SHALL mark the event as high-risk
3. WHEN timing variance is below 0.003 seconds THEN the system SHALL mark the event as high-risk
4. WHEN both entropy and timing indicators are suspicious THEN the system SHALL increase the anomaly score by 0.3
5. WHEN entropy checks are performed THEN the system SHALL complete within 1 millisecond

### Requirement 4: Multi-Layer Signature Validation

**User Story:** As a security operator, I want the system to use multiple signature validation methods, so that attacks cannot bypass detection by exploiting a single validation layer.

#### Acceptance Criteria

1. WHEN validating an event THEN the system SHALL attempt hard signature matching first
2. WHEN hard signature matching fails THEN the system SHALL attempt soft signature matching
3. WHEN soft signature matching fails THEN the system SHALL attempt behavioral signature matching
4. WHEN all signature modes fail THEN the system SHALL block the event
5. WHEN behavioral signature matching is used THEN the system SHALL consider timing, entropy, and call patterns

### Requirement 5: Micro-Mutation Engine

**User Story:** As a security operator, I want the system to continuously adapt its detection rules, so that attackers cannot learn and bypass static thresholds.

#### Acceptance Criteria

1. WHEN 50 events have been processed THEN the system SHALL trigger micro-mutation
2. WHEN micro-mutation occurs THEN the system SHALL adjust anomaly thresholds by ±5%
3. WHEN micro-mutation occurs THEN the system SHALL add random noise to pattern matching scores
4. WHEN micro-mutation occurs THEN the system SHALL shuffle pattern lookup table ordering
5. WHEN micro-mutation completes THEN the system SHALL log the new threshold values

### Requirement 6: Reputation-Based Allowlisting

**User Story:** As a security operator, I want the system to build reputation scores for legitimate users, so that trusted users experience fewer false positives.

#### Acceptance Criteria

1. WHEN a user consistently sends legitimate traffic THEN the system SHALL increase their reputation score
2. WHEN a user's reputation score exceeds 0.8 THEN the system SHALL apply relaxed thresholds
3. WHEN a user sends suspicious traffic THEN the system SHALL decrease their reputation score
4. WHEN a reputation score decays THEN the system SHALL reduce it by 10% every 2400 seconds
5. WHEN reputation is evaluated THEN the system SHALL consider the last 100 events from that user

### Requirement 7: Enhanced Replay Protection

**User Story:** As a security operator, I want aggressive replay attack detection, so that stolen credentials and nonces cannot be reused.

#### Acceptance Criteria

1. WHEN a nonce is used THEN the system SHALL store it in the replay protection cache
2. WHEN a nonce is reused THEN the system SHALL immediately block the event
3. WHEN replay protection is set to aggressive mode THEN the system SHALL maintain nonces for 3600 seconds
4. WHEN the replay cache reaches capacity THEN the system SHALL evict the oldest nonces
5. WHEN a replay attack is detected THEN the system SHALL log the source and increment attack counters

### Requirement 8: Performance Optimization

**User Story:** As a security operator, I want the system to maintain low latency under load, so that legitimate traffic is not delayed.

#### Acceptance Criteria

1. WHEN the classifier queue size is 128 THEN the system SHALL handle burst traffic without backpressure
2. WHEN P95 latency exceeds 15ms THEN the system SHALL activate performance mode
3. WHEN performance mode is active THEN the system SHALL skip optional analysis steps
4. WHEN queue utilization exceeds 80% THEN the system SHALL log a warning
5. WHEN processing events THEN the system SHALL maintain P95 latency below 10ms

### Requirement 9: Configuration Management

**User Story:** As a security operator, I want to easily adjust tuning parameters, so that the system can be optimized for different deployment environments.

#### Acceptance Criteria

1. WHEN configuration is loaded THEN the system SHALL validate all tuning parameters
2. WHEN invalid parameters are detected THEN the system SHALL use safe defaults and log warnings
3. WHEN configuration is updated THEN the system SHALL apply changes without restart
4. WHEN tuning parameters are changed THEN the system SHALL log the old and new values
5. WHEN configuration is requested THEN the system SHALL return current active parameters

### Requirement 10: Monitoring and Metrics

**User Story:** As a security operator, I want detailed metrics on system accuracy, so that I can evaluate tuning effectiveness.

#### Acceptance Criteria

1. WHEN events are processed THEN the system SHALL track false positive and false negative rates
2. WHEN 1000 events have been processed THEN the system SHALL calculate and log accuracy metrics
3. WHEN accuracy metrics are calculated THEN the system SHALL include precision, recall, and F1 score
4. WHEN metrics are exported THEN the system SHALL include latency percentiles (P50, P95, P99)
5. WHEN tuning is applied THEN the system SHALL compare before/after metrics
