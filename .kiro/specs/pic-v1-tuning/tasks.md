# Implementation Plan: PIC v1 Tuning & Optimization

## Overview

This implementation plan addresses the accuracy issues identified in MIPAB-11 testing by implementing adaptive tuning mechanisms. The goal is to reduce false positives from 28.3% to <5%, increase malicious block rate from 71.6% to >92%, and maintain P95 latency <10ms.

---

## Tasks

- [ ] 1. Implement Pattern Memory Cache
  - Create fast-path recognition system for known legitimate patterns
  - Use LSH for fuzzy matching with 85% threshold
  - Implement LRU eviction and TTL cleanup
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [ ] 1.1 Create PatternFingerprint data model
  - Define fingerprint structure (function, module, duration, args, resources)
  - Implement hash function for fast lookup
  - Add timestamp and hit count tracking
  - _Requirements: 1.1_

- [ ] 1.2 Implement PatternMemoryCache class
  - Initialize with TTL (1800s) and max size (10000)
  - Implement add_pattern() method
  - Implement check_match() with fuzzy matching
  - Implement evict_expired() for TTL cleanup
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ]* 1.3 Write property test for pattern cache
  - **Property 1: Pattern Cache Consistency**
  - **Validates: Requirements 1.1, 1.2**
  - Test that approved patterns are retrievable within TTL
  - Test fuzzy matching with 85% threshold
  - Test LRU eviction when capacity reached

- [ ] 1.4 Integrate pattern cache into BrainCore
  - Add cache as first check in event processing pipeline
  - Return immediate allow decision on cache hit
  - Update cache on legitimate event approval
  - _Requirements: 1.1, 1.2_

- [ ] 2. Implement Entropy Analyzer
  - Create entropy-based attack detection
  - Calculate Shannon entropy for payloads
  - Analyze timing variance patterns
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 2.1 Create EntropyAnalyzer class
  - Implement calculate_entropy() using Shannon formula
  - Implement analyze_timing() for variance calculation
  - Implement is_suspicious() combining both checks
  - Set thresholds: entropy_min=2.4, timing_variance_min=0.003
  - _Requirements: 3.1, 3.2, 3.3_

- [ ]* 2.2 Write property test for entropy detection
  - **Property 3: Entropy Detection Accuracy**
  - **Validates: Requirements 3.1, 3.2, 3.4**
  - Test that low entropy payloads are marked high-risk
  - Test that low timing variance is detected
  - Test combined entropy + timing scoring

- [ ] 2.3 Integrate entropy analyzer into decision pipeline
  - Add entropy check after signature validation
  - Increase anomaly score by 0.3 for suspicious entropy
  - Increase anomaly score by 0.2 for suspicious timing
  - _Requirements: 3.4_

- [ ] 3. Implement Multi-Layer Signature Validation
  - Create three-tier signature validation system
  - Implement hard, soft, and behavioral validation modes
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 3.1 Create ValidationResult data model
  - Define result structure (is_valid, confidence, method, reason)
  - _Requirements: 4.1_

- [ ] 3.2 Implement MultiLayerValidator class
  - Implement validate_hard() for exact HMAC matching
  - Implement validate_soft() for structural validation
  - Implement validate_behavioral() for pattern matching
  - Implement validate() with fallback logic
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [ ]* 3.3 Write property test for signature validation
  - **Property 4: Signature Validation Fallback**
  - **Validates: Requirements 4.1, 4.2, 4.3, 4.4**
  - Test fallback from hard → soft → behavioral
  - Test that all modes failing results in block
  - Test confidence scoring for each mode

- [ ] 3.4 Replace existing signature validation with multi-layer
  - Update SecurityValidator to use MultiLayerValidator
  - Configure signature modes: ["hard", "soft", "behavioral"]
  - _Requirements: 4.1, 4.2, 4.3_

- [ ] 4. Implement Adaptive Anomaly Scoring
  - Create adaptive threshold system
  - Implement soft-allow mode for borderline cases
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ] 4.1 Create ScoringContext data model
  - Define context structure (event, history, reputation, entropy, timing, validation)
  - _Requirements: 2.1_

- [ ] 4.2 Implement AdaptiveAnomalyScorer class
  - Initialize with base_threshold=0.65, soft_allow_prob=0.15
  - Implement score_event() with context-aware scoring
  - Implement adjust_threshold() for micro-mutation
  - Implement get_decision() with three-tier logic
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [ ]* 4.3 Write property test for threshold monotonicity
  - **Property 2: Threshold Monotonicity**
  - **Validates: Requirements 2.1, 2.2, 2.3**
  - Test score < 0.65 → allow
  - Test 0.65 ≤ score < 0.75 → soft-allow
  - Test score ≥ 0.75 → block

- [ ] 4.4 Integrate adaptive scorer into BrainCore
  - Replace existing anomaly detection with adaptive scorer
  - Apply reputation bonuses to scores
  - Implement soft-allow logging
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [ ] 5. Implement Reputation Manager
  - Create user reputation tracking system
  - Implement reputation-based threshold adjustments
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 5.1 Implement ReputationManager class
  - Initialize with decay_interval=2400
  - Implement update_reputation() for score updates
  - Implement get_reputation() for lookups
  - Implement decay_reputations() for time-based decay
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [ ]* 5.2 Write property test for reputation monotonicity
  - **Property 6: Reputation Monotonic Increase**
  - **Validates: Requirements 6.1, 6.2**
  - Test that legitimate traffic increases reputation
  - Test that reputation caps at maximum
  - Test decay over time

- [ ] 5.3 Integrate reputation manager into BrainCore
  - Extract user_id from events
  - Update reputation after each decision
  - Apply reputation bonus (-0.1 for high reputation)
  - Start background decay thread
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [ ] 6. Implement Micro-Mutation Engine
  - Create continuous adaptation system
  - Implement threshold, pattern, and lookup mutations
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 6.1 Implement MicroMutationEngine class
  - Initialize with mutation_interval=50
  - Implement should_mutate() for interval checking
  - Implement mutate_thresholds() with ±5% adjustment
  - Implement mutate_patterns() with ±2% noise
  - Implement mutate_lookup_tables() with shuffling
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ]* 6.2 Write property test for mutation periodicity
  - **Property 5: Micro-Mutation Periodicity**
  - **Validates: Requirements 5.1**
  - Test that mutations occur every N events
  - Test that threshold adjustments stay in bounds
  - Test mutation logging

- [ ] 6.3 Integrate mutation engine into BrainCore
  - Add event counter for mutation triggering
  - Apply mutations to scorer, cache, and validator
  - Log all mutations for audit trail
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 7. Implement Enhanced Replay Protection
  - Upgrade replay detection to aggressive mode
  - Extend nonce cache TTL to 3600 seconds
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 7.1 Update SecurityValidator replay protection
  - Set replay_protection_level="aggressive"
  - Extend nonce cache TTL to 3600 seconds
  - Implement capacity-based eviction
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [ ]* 7.2 Write property test for replay protection
  - **Property 7: Replay Protection Uniqueness**
  - **Validates: Requirements 7.1, 7.2**
  - Test that reused nonces are blocked
  - Test nonce expiration after TTL
  - Test cache eviction under capacity pressure

- [ ] 8. Implement Configuration Management
  - Create tuning configuration system
  - Implement validation and hot-reload
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ] 8.1 Create TuningConfig dataclass
  - Define all tuning parameters with defaults
  - Implement validate() method
  - Implement apply() method for hot-reload
  - _Requirements: 9.1, 9.2, 9.3_

- [ ] 8.2 Create configuration file support
  - Support JSON and YAML formats
  - Load from file: config/tuning.json
  - Implement file watcher for hot-reload
  - _Requirements: 9.3, 9.4_

- [ ]* 8.3 Write property test for configuration validation
  - **Property 9: Configuration Validation**
  - **Validates: Requirements 9.1, 9.2**
  - Test that invalid parameters are rejected
  - Test that safe defaults are used on error
  - Test hot-reload without restart

- [ ] 8.4 Integrate configuration into BrainCore
  - Load configuration on startup
  - Apply configuration to all components
  - Support runtime configuration updates
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ] 9. Implement Metrics and Monitoring
  - Create comprehensive accuracy metrics
  - Implement performance monitoring
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ] 9.1 Create MetricsCollector class
  - Track FP, FN, TP, TN counters
  - Calculate precision, recall, F1 score
  - Track latency percentiles (P50, P95, P99)
  - Implement get_accuracy_metrics() method
  - _Requirements: 10.1, 10.2, 10.3, 10.4_

- [ ]* 9.2 Write property test for metrics accuracy
  - **Property 10: Metrics Accuracy**
  - **Validates: Requirements 10.1, 10.2**
  - Test FP rate calculation
  - Test FN rate calculation
  - Test precision/recall/F1 formulas

- [ ] 9.3 Integrate metrics into BrainCore
  - Update metrics on each decision
  - Log metrics every 1000 events
  - Export metrics in Prometheus format
  - _Requirements: 10.1, 10.2, 10.3, 10.4_

- [ ] 9.4 Create metrics dashboard
  - Display real-time FP/FN rates
  - Display latency percentiles
  - Display throughput and queue utilization
  - Add before/after comparison view
  - _Requirements: 10.5_

- [ ] 10. Performance Optimization
  - Optimize for P95 latency < 10ms
  - Increase queue size to 128
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 10.1 Optimize pattern cache lookup
  - Implement LSH for O(1) fuzzy matching
  - Add bloom filter for fast negative checks
  - Target: < 0.5ms lookup time
  - _Requirements: 8.5_

- [ ] 10.2 Optimize entropy calculation
  - Use lookup tables for log2 calculations
  - Implement early termination for obvious cases
  - Target: < 1ms calculation time
  - _Requirements: 8.5_

- [ ] 10.3 Increase classifier queue size
  - Update queue size from 32 to 128
  - Implement queue utilization monitoring
  - Add backpressure activation at 80% utilization
  - _Requirements: 8.1, 8.4_

- [ ]* 10.4 Write performance tests
  - **Property 8: Latency Bound**
  - **Validates: Requirements 8.5**
  - Test P95 latency < 10ms under normal load
  - Test P99 latency < 20ms under burst load
  - Test throughput > 100 events/sec

- [ ] 11. Integration and Testing
  - Integrate all components into BrainCore
  - Run comprehensive testing
  - _Requirements: All_

- [ ] 11.1 Create IntegratedTunedPIC class
  - Combine all tuning components
  - Initialize with TuningConfig
  - Implement unified event processing pipeline
  - _Requirements: All_

- [ ]* 11.2 Write integration tests
  - Test full pipeline: event → decision
  - Test component interactions
  - Test error handling and recovery
  - Test concurrent access

- [ ] 11.3 Run MIPAB-11 regression test
  - Re-run MIPAB-11 with tuned system
  - Compare metrics with baseline
  - Target: FP < 5%, malicious block > 92%, P95 < 10ms
  - _Requirements: All_

- [ ] 11.4 Create tuning documentation
  - Document all tuning parameters
  - Provide tuning guidelines for different environments
  - Include troubleshooting guide
  - Add performance tuning tips
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ] 12. Checkpoint - Verify all tests pass
  - Ensure all tests pass, ask the user if questions arise.

---

## Success Criteria

After implementation, the system should achieve:

- **False Positive Rate**: < 5% (down from 28.3%)
- **Malicious Block Rate**: > 92% (up from 71.6%)
- **Legitimate Acceptance Rate**: > 95% (up from 71.7%)
- **P95 Latency**: < 10ms (currently 7.4ms)
- **P99 Latency**: < 20ms (down from 69.8ms)
- **Throughput**: > 100 events/sec (currently ~10 events/sec)

## Implementation Notes

- All property tests should run 1000+ iterations
- Each component should be independently testable
- Use feature flags for gradual rollout
- Maintain backward compatibility with existing PIC
- Log all tuning decisions for audit trail
