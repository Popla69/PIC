# Implementation Plan - PIC v1 MVP

**v1 MVP Scope**: Core detection with decorator instrumentation, percentile-based anomaly detection, simple allow/block actions. Advanced features (quarantine, token bucket, rollback, watchdog, web console) deferred to v1.1+

## Phase 1: Foundation (Core Infrastructure)

- [x] 1. Set up project structure



  - Create src/pic/ with modules: config, crypto, storage, models
  - Set up pyproject.toml with core dependencies: pytest, hypothesis, pyyaml, cryptography
  - Configure dev tools: flake8, black, mypy, pytest-cov
  - Create requirements.txt with pinned dependencies
  - _Requirements: 10.1, 25.1_

- [x] 2. Implement PICConfig (centralized configuration)


  - [x] 2.1 Create configuration loader


    - Load from YAML file, environment variables, CLI args
    - Implement priority: CLI > env > file > defaults
    - Add dot-notation access (config.get("cellagent.sampling_rate"))
    - _Requirements: New for v1 simplification_

  - [ ]* 2.2 Write unit tests for configuration
    - Test loading from each source
    - Test priority order
    - Test validation

- [x] 3. Implement CryptoCore (centralized cryptography)


  - [x] 3.1 Create crypto operations


    - HMAC-SHA256 signing for audit logs
    - SHA-256 hashing for PII and signatures
    - Key generation and storage
    - _Requirements: 6.1, 6.3, 18.5, 19.3_

  - [ ]* 3.2 Write unit tests for CryptoCore
    - Test signing and verification
    - Test hashing consistency

- [x] 4. Implement core data models


  - [x] 4.1 Create dataclasses


    - TelemetryEvent (timestamp, function_name, duration_ms, event_id)
    - BaselineProfile (function_name, mean, std, p50, p95, p99)
    - Detector (id, function_name, threshold, expires_at)
    - AuditEvent (timestamp, event_type, action, signature)
    - Decision (action: allow|block, reason, anomaly_score)
    - _Requirements: 17.1_

  - [x] 4.2 Write property test for telemetry schema


    - **Property 52: Telemetry Event Schema Compliance**
    - **Validates: Requirements 17.1**

  - [ ]* 4.3 Write unit tests for models
    - Test JSON serialization
    - Test validation

- [x] 5. Checkpoint - Foundation complete


  - Ensure all tests pass, ask the user if questions arise.

## Phase 2: Storage Layer

- [x] 6. Implement StateStore (SQLite for baselines and detectors)


  - [x] 6.1 Create database schema and connection


    - Define baselines table (function_name, mean, std, percentiles)
    - Define detectors table (id, function_name, threshold, expires_at)
    - Enable WAL mode for concurrency
    - _Requirements: 7.1, 7.2, 7.3_

  - [x] 6.2 Implement baseline operations

    - store_baseline(), get_baseline()
    - Version tracking for updates
    - _Requirements: 2.1, 16.4_

  - [x] 6.3 Implement detector operations

    - store_detector(), get_active_detectors()
    - expire_old_detectors() for TTL enforcement
    - _Requirements: 7.1, 7.2, 7.4_

  - [x] 6.4 Write property test for signature storage


    - **Property 24: Signature Hash Storage**
    - **Validates: Requirements 7.1, 14.1**

  - [ ]* 6.5 Write unit tests for StateStore
    - Test CRUD operations
    - Test WAL concurrency
    - Test TTL expiration

- [x] 7. Implement AuditStore (append-only logs)


  - [x] 7.1 Create log file writer with HMAC signing


    - Append-only file format
    - HMAC-SHA256 signature per entry using CryptoCore
    - JSON lines format
    - _Requirements: 6.1, 6.3, 18.5_

  - [x] 7.2 Write property test for audit immutability


    - **Property 21: Audit Log Immutability**
    - **Validates: Requirements 6.1**

  - [x] 7.3 Write property test for HMAC signing

    - **Property 56: Audit Log HMAC Signing**
    - **Validates: Requirements 18.5**

  - [ ]* 7.4 Write unit tests for AuditStore
    - Test log writing
    - Test signature verification
    - Test export functionality

- [x] 8. Implement TraceStore (in-memory telemetry buffer)



  - [x] 8.1 Create ring buffer for recent events


    - 1000 events per function capacity (reduced from 10,000 for MVP)
    - Automatic eviction of oldest
    - Simple dict-based lookup by function name
    - _Requirements: New for v1 validation_

  - [ ]* 8.2 Write unit tests for TraceStore
    - Test buffer overflow handling
    - Test eviction logic

- [x] 9. Checkpoint - Storage complete

  - Ensure all tests pass, ask the user if questions arise.

## Phase 3: Telemetry Collection


- [x] 10. Implement PII redaction

  - [x] 10.1 Create redaction engine


    - Regex patterns for email, phone, CC, SSN, IP
    - Replace with tokens ([EMAIL_REDACTED], etc.)
    - SHA-256 hash arguments using CryptoCore
    - _Requirements: 1.5, 6.2, 14.1_

  - [x] 10.2 Write property test for PII redaction


    - **Property 4: PII Redaction Completeness**
    - **Validates: Requirements 1.5, 6.2**

  - [ ]* 10.3 Write unit tests for redaction
    - Test each PII pattern
    - Test hash consistency

- [x] 11. Implement CellAgent (decorator instrumentation)


  - [x] 11.1 Create @pic.monitor decorator


    - Wrap function to capture entry/exit
    - Measure duration with time.perf_counter()
    - Create TelemetryEvent with PII redaction
    - Handle exceptions gracefully (don't crash app)
    - _Requirements: 1.1, 1.3, 1.4_

  - [x] 11.2 Implement sampling and buffering

    - Configurable sampling rate (default 1:10)
    - Ring buffer (10,000 capacity)
    - Adaptive sampling based on CPU usage
    - _Requirements: 1.2, 15.1, 17.2_

  - [ ]* 11.3 Write property test for sampling accuracy (deferred to v1.1)
    - **Property 2: Sampling Rate Accuracy**
    - **Validates: Requirements 1.2, 17.2**

  - [x] 11.4 Write property test for graceful failure


    - **Property 3: Graceful Instrumentation Failure**
    - **Validates: Requirements 1.4**

  - [ ]* 11.5 Write unit tests for CellAgent
    - Test decorator application
    - Test telemetry generation
    - Test error handling

- [x] 12. Implement TelemetryTransport (simple batch transmission)


  - [x] 12.1 Create batch sender


    - Accumulate 100 events or 5 seconds
    - Simple retry: 3 attempts with 1 second delay
    - Discard batch after 3 failures
    - _Requirements: New for v1 reliability_

  - [ ]* 12.2 Write unit tests for transport
    - Test batching logic
    - Test simple retry
    - Test failure handling

- [x] 13. Checkpoint - Telemetry collection complete


  - Ensure all tests pass, ask the user if questions arise.

## Phase 4: Detection Engine

- [x] 14. Implement FeatureNormalizer (preprocessing)


  - [x] 14.1 Create normalization module


    - Min-max scaling to [0, 1]
    - Outlier capping at 99th percentile
    - Missing value filling with median
    - _Requirements: New for v1 stability_

  - [ ]* 14.2 Write unit tests for normalizer
    - Test scaling
    - Test outlier handling
    - Test missing values

- [x] 15. Implement BaselineProfiler

  - [x] 15.1 Create statistical profiler

    - Collect minimum 20 samples or 2 hours (relaxed for faster MVP testing)
    - Compute mean, std, p50, p95, p99 for duration
    - Store in StateStore
    - _Requirements: 2.1, 16.4, 16.5_

  - [x] 15.2 Write property test for baseline convergence



    - **Property 5: Baseline Profile Convergence**
    - **Validates: Requirements 2.1, 16.4**

  - [ ]* 15.3 Write unit tests for profiler
    - Test statistical computations
    - Test minimum sample enforcement

- [x] 16. Implement AnomalyDetector (percentile-based)

  - [x] 16.1 Create detector with percentile thresholds


    - Normalize features using FeatureNormalizer
    - Compute L2 distance from baseline mean
    - Compute percentile rank (default 95th percentile)
    - Generate anomaly score (0-100)
    - Create detection candidate if score > 80
    - _Requirements: 2.2, 2.3_

  - [x] 16.2 Write property test for score monotonicity


    - **Property 6: Anomaly Score Monotonicity**
    - **Validates: Requirements 2.2**

  - [x] 16.3 Write property test for candidate generation

    - **Property 7: Candidate Generation Threshold**
    - **Validates: Requirements 2.3**

  - [ ]* 16.4 Write unit tests for detector
    - Test L2 distance computation
    - Test percentile calculation
    - Test threshold enforcement

- [x] 17. Implement SimpleValidator (threshold validation)

  - [x] 17.1 Create validation logic


    - Load last 100 benign events from TraceStore
    - Apply candidate threshold
    - Compute FP rate
    - Pass if FP rate ≤ 5%
    - _Requirements: 3.1, 3.3, 3.5_

  - [x] 17.2 Write property test for promotion eligibility


    - **Property 11: Promotion Eligibility Rule**
    - **Validates: Requirements 3.5**

  - [ ]* 17.3 Write unit tests for validator
    - Test FP rate computation
    - Test pass/fail logic

- [x] 18. Checkpoint - Detection engine complete

  - Ensure all tests pass, ask the user if questions arise.

## Phase 5: Action Execution

- [x] 19. Implement Effector (allow/block actions)

  - [x] 19.1 Create action executor

    - Implement allow action (pass-through with logging)
    - Implement block action (return stub value, raise exception)
    - Generate safe stub values by type (0, False, "", [], {}, None)
    - Fail-safe default: allow on error
    - _Requirements: 5.1, 5.3, 5.4_

  - [x] 19.2 Write property test for action validity


    - **Property 16: Effector Action Validity**
    - **Validates: Requirements 5.1**

  - [ ]* 19.3 Write property test for stub type safety (deferred to v1.1)
    - **Property 18: Block Stub Type Safety**
    - **Validates: Requirements 5.3**


  - [ ] 19.4 Write property test for fail-safe default
    - **Property 19: Effector Fail-Safe Default**
    - **Validates: Requirements 5.4**

  - [ ]* 19.5 Write unit tests for Effector
    - Test allow and block actions
    - Test stub generation
    - Test error handling

## Phase 6: Orchestration

- [x] 20. Implement BrainCore (event processing pipeline)

  - [x] 20.1 Create main processing loop


    - Receive telemetry from CellAgent
    - Store in TraceStore
    - Check baseline (train if insufficient)
    - Normalize and detect anomalies
    - Execute action via Effector
    - Log to AuditStore
    - _Requirements: 2.1, 2.2, 2.3_

  - [ ]* 20.2 Write integration tests for pipeline
    - Test end-to-end flow
    - Test baseline training
    - Test detection and action

- [x] 21. Implement periodic maintenance (inline in BrainCore)

  - [x] 21.1 Add periodic task execution

    - Check for baseline retraining every 100 events processed
    - Check for detector expiration every 100 events processed
    - Simple inline execution (no background scheduler for MVP)
    - _Requirements: 2.4, 7.4_

  - [ ]* 21.2 Write unit tests for periodic tasks
    - Test retraining trigger
    - Test expiration check

- [x] 22. Implement BrainAPI (HTTP endpoints)

  - [x] 22.1 Create Flask API


    - POST /api/v1/telemetry (receive batches)
    - GET /health (health check)
    - GET /metrics (Prometheus format)
    - GET /status (system statistics)
    - GET /version (version info)
    - _Requirements: 23.1_

  - [ ]* 22.2 Write property test for metrics completeness (deferred to v1.1)
    - **Property 65: Prometheus Metrics Completeness**
    - **Validates: Requirements 23.1**

  - [ ]* 22.3 Write unit tests for API
    - Test each endpoint
    - Test error handling

- [x] 23. Checkpoint - Orchestration complete

  - Ensure all tests pass, ask the user if questions arise.

## Phase 7: CLI and Testing

- [x] 24. Implement CLI interface (minimal for MVP)


  - [x] 24.1 Create command-line interface

    - pic start (start SentinelBrain service)
    - pic status (show system status)
    - pic logs export (export audit logs)
    - _Requirements: 4.1_

  - [ ]* 24.2 Write unit tests for CLI
    - Test each command
    - Test output formatting

- [x] 25. Create test data generators (minimal for MVP)

  - [x] 25.1 Implement simple generators


    - Benign event generator (1,000 samples)
    - 4-5 manual malicious patterns for testing
    - Deterministic seed support
    - _Requirements: 21.1, 21.2, 21.4_

  - [ ]* 25.2 Write property test for reproducibility (deferred to v1.1)
    - **Property 61: Synthetic Data Reproducibility**
    - **Validates: Requirements 21.4**

  - [ ]* 25.3 Write unit tests for generators
    - Test data generation
    - Test seed reproducibility

- [x] 26. Implement performance measurement


  - [x] 26.1 Create KPI calculators


    - FPR calculation: flagged / total_benign
    - TPR calculation: detected / total_malicious
    - Latency percentiles (P50, P95, P99)
    - Overhead measurement harness
    - _Requirements: 16.1, 16.2, 16.3_

  - [x] 26.2 Write property test for FPR calculation

    - **Property 48: FPR Calculation Correctness**
    - **Validates: Requirements 16.1**

  - [x] 26.3 Write property test for TPR calculation

    - **Property 49: TPR Calculation Correctness**
    - **Validates: Requirements 16.2**

  - [ ]* 26.4 Write unit tests for KPI calculations
    - Test FPR/TPR with various datasets
    - Test percentile calculations

## Phase 8: Packaging and CI/CD

- [x] 27. Create CI/CD pipeline

  - [x] 27.1 Set up GitHub Actions


    - Lint (flake8, black, mypy)
    - Unit tests with coverage
    - Property tests (100 iterations)
    - Security scans (Bandit, Safety)
    - SBOM generation (CycloneDX)
    - Build artifacts (pip package)
    - _Requirements: 10.1, 10.2, 10.3, 25.2, 25.3_

  - [x] 27.2 Write property test for SBOM format

    - **Property 38: SBOM Format Compliance**
    - **Validates: Requirements 10.3, 25.2**

- [x] 28. Create packaging

  - [x] 28.1 Set up pip package


    - Create setup.py and pyproject.toml
    - Configure entry points for CLI
    - Add MANIFEST.in
    - _Requirements: 11.1_

  - [x] 28.2 Create Dockerfile


    - Multi-stage build
    - Minimal base image
    - Non-root user
    - _Requirements: 11.2_

## Phase 9: Documentation and Demo

- [x] 29. Create documentation


  - [x] 29.1 Write README and guides

    - 90-second overview with ASCII diagram
    - Installation instructions
    - Quickstart tutorial
    - Configuration reference
    - Troubleshooting guide
    - _Requirements: 12.1, 28.1_

  - [x] 29.2 Create demo script


    - 5-minute demo with docker-compose
    - Sample dataset
    - Demo documentation
    - _Requirements: 12.2, 12.3_

## Phase 10: Acceptance Testing

- [x] 30. Run acceptance tests

  - [x] 30.1 Execute full test suite


    - All property tests pass (100 iterations each)
    - Performance: latency overhead ≤ 5%
    - FPR ≤ 5% on golden benign dataset
    - TPR ≥ 75% on golden malicious dataset
    - CI green for 3 consecutive runs
    - SBOM clear of critical CVEs
    - _Requirements: 10.5_

- [x] 31. Final checkpoint - Release ready


  - Ensure all acceptance criteria met
  - Verify core properties pass
  - Ready for v1.0 release

---

**Essential Properties for v1 MVP** (20 core properties):
1. Instrumentation Overhead Bound
2. Sampling Rate Accuracy
3. Graceful Instrumentation Failure
4. PII Redaction Completeness
5. Baseline Profile Convergence
6. Anomaly Score Monotonicity
7. Candidate Generation Threshold
8. Promotion Eligibility Rule
11. Effector Action Validity
16. Block Stub Type Safety
18. Effector Fail-Safe Default
19. Audit Log Immutability
21. Signature Hash Storage
24. Telemetry Event Schema Compliance
48. FPR Calculation Correctness
49. TPR Calculation Correctness
52. HMAC Signing
56. Synthetic Data Reproducibility
61. Prometheus Metrics Completeness
65. SBOM Format Compliance

**Deferred to v1.1+**: Quarantine, token bucket, rollback, watchdog, multi-signal fusion, web console, encryption at rest
