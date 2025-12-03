# PIC v1 (Popla Immune Core) - Design Document

## Overview

PIC v1 is a defensive cybersecurity system that provides behavioral anomaly detection and automated response for Python applications. The system operates through in-process instrumentation (CellAgent) that collects behavioral telemetry, a local analysis service (SentinelBrain) that detects anomalies and generates detection candidates, an isolated testing environment (Sandbox Runner) that validates candidates before deployment, and a safe remediation engine (Effector) that executes defensive actions.

The architecture follows a defense-in-depth approach with multiple safety layers:
1. **Baseline Learning**: Automatic profiling of normal behavior without manual configuration
2. **Sandbox Validation**: All detection candidates tested against benign scenarios before activation
3. **Human-in-Loop**: Manual approval required for promoting detection candidates to production
4. **Fail-Safe Defaults**: System defaults to observe-only mode on errors or uncertainty
5. **Immutable Audit**: All decisions logged cryptographically for forensic analysis

Target deployment environments include developer workstations, containerized applications, and cloud VMs running Python 3.9+.

### v1 MVP Scope

To ensure v1 is implementable within reasonable timeframe, the following scope is defined:

**Essential Components (v1.0)**:
1. **CellAgent**: Decorator-based instrumentation with telemetry sampling
2. **Baseline Profiler**: Basic statistical profiling (mean, std dev, percentiles)
3. **Anomaly Detector**: Percentile-based detection with feature normalization
4. **Effector**: Allow/block actions only (no quarantine in v1)
5. **StateStore**: SQLite for baselines and detectors
6. **AuditStore**: Append-only HMAC-signed logs
7. **BrainCore**: Simple event processing pipeline
8. **PICConfig**: Centralized configuration management
9. **TelemetryTransport**: Batch transmission with retry logic
10. **Metrics API**: Basic /health, /metrics, /status endpoints

**Deferred to v1.1+**:
- Statistical validator sandbox (use simple threshold validation)
- Multi-signal fusion with weights (use single signal: timing)
- Token bucket rate limiter (use simple counter)
- Detector promotion workflows (manual promotion via CLI)
- Rollback and state snapshots (manual rollback)
- Encryption at rest (add in v1.1)
- Quarantine action (only allow/block in v1)
- Web Admin Console (CLI only for v1)
- Watchdog process (manual restart for v1)

**Module Responsibilities Clarified**:
- **StateStore**: Baselines + detectors only
- **AuditStore**: Immutable logs only
- **TraceStore**: Recent telemetry buffer (last 1000 events)
- **CryptoCore**: Centralized crypto operations (HMAC, SHA-256, key management)
- **FeatureNormalizer**: Min-max scaling before anomaly detection
- **BrainAPI**: HTTP/IPC endpoints (separate from BrainCore logic)
- **BrainScheduler**: Periodic tasks (baseline retraining, cleanup)

This reduces implementation complexity by ~75% while maintaining core detection value.

### Design Principles

- **Safety First**: No automatic code modification; all mutations affect only detection thresholds
- **Minimal Overhead**: <5% median latency impact through adaptive sampling and efficient instrumentation
- **Privacy by Design**: PII redaction, data minimization, configurable retention policies
- **Fail-Safe Operation**: Graceful degradation to observe-only mode on component failures
- **Explainability**: Every decision includes traceable reasoning for human review
- **Defense Only**: No offensive capabilities; purely detection and safe remediation

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Monitored Application                        │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                        CellAgent                                │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │ │
│  │  │ Instrumentation│  │  Telemetry   │  │   Effector   │         │ │
│  │  │    Layer      │──│  Collector   │──│   Interface  │         │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘         │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                │                        ▲
                                │ mTLS                   │
                                ▼                        │
┌─────────────────────────────────────────────────────────────────────┐
│                         SentinelBrain (Local Service)                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   Baseline   │  │   Anomaly    │  │   Mutation   │              │
│  │   Profiler   │──│   Detector   │──│    Engine    │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                │                                     │
│                                ▼                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ Memory Bank  │  │   Sandbox    │  │   Effector   │              │
│  │   (SQLite)   │  │    Runner    │  │   Executor   │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Admin Console (Web UI)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ Alert Inbox  │  │  Decision    │  │ Explainability│              │
│  │              │  │  History     │  │    Traces     │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Audit Store (Immutable Logs)                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  WORM Log Entries (HMAC-SHA256 signed, encrypted at rest)    │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

**v1 Architecture Notes**:
- SentinelBrain can run as a thread in the same process or as a separate process with local IPC (no mTLS required for v1)
- Sandbox Runner simplified to statistical validator (no full process isolation)
- Admin Console optional for v1 (CLI interface sufficient)
- All components can run on single host with SQLite+WAL

### Data Flow

**Normal Operation Flow:**
1. Application executes instrumented code
2. CellAgent captures telemetry events (sampled at 1:10 ratio)
3. CellAgent redacts PII and sends events to SentinelBrain via mTLS
4. SentinelBrain updates baseline profile and computes anomaly scores
5. Low-score events: logged and allowed
6. High-score events: generate detection candidate
7. Candidate sent to Sandbox Runner for validation
8. Sandbox runs candidate against benign test scenarios
9. If sandbox passes: candidate queued for human review in Admin Console
10. Human operator reviews explainability trace and approves/rejects
11. If approved: candidate promoted to Memory Bank as active detector
12. Future matching events trigger Effector actions (allow/quarantine/block)

**Failure Flow:**
1. Component failure detected (CellAgent crash, SentinelBrain unavailable, etc.)
2. Watchdog detects failure within 30 seconds
3. System enters fail-safe observe-only mode
4. CellAgent buffers telemetry locally with backpressure
5. Watchdog attempts component restart from trusted binary
6. On successful restart: buffered telemetry replayed
7. On persistent failure: alert sent to Admin Console
8. Manual intervention required for recovery

**Override Flow:**
1. Operator identifies false positive in Admin Console
2. Operator selects "Rollback Detector" action
3. System creates snapshot of current state
4. Detector removed from Memory Bank
5. Baseline profile updated to exclude false positive pattern
6. Rollback logged to Audit Store with operator identity
7. Affected events re-evaluated with updated baseline

## Components and Interfaces

### PICConfig (Configuration Management)

**Purpose**: Centralized configuration system that loads settings from YAML files, environment variables, and CLI arguments.

**Configuration Sources** (priority order):
1. CLI arguments (highest priority)
2. Environment variables (PIC_* prefix)
3. YAML config file (default: /etc/pic/config.yaml)
4. Built-in defaults (lowest priority)

**Configuration Schema**:
```yaml
cellagent:
  sampling_rate: 0.1
  buffer_size: 10000
  batch_size: 100
  batch_interval_sec: 5
  cpu_threshold: 0.02

baseline:
  window_hours: 72
  min_samples: 50
  retrain_interval_hours: 6

anomaly:
  threshold_percentile: 95
  candidate_score_threshold: 80

effector:
  default_action: allow
  fail_safe_mode: allow

storage:
  state_db_path: /var/lib/pic/state.db
  audit_log_path: /var/lib/pic/audit.log
  trace_buffer_size: 1000

api:
  listen_address: 127.0.0.1
  listen_port: 8443
  metrics_enabled: true
```

**Interface**:
```python
class PICConfig:
    @classmethod
    def load(cls, config_path: Optional[str] = None) -> 'PICConfig':
        """Load configuration from file, env vars, and defaults"""
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key"""
        
    def reload(self) -> None:
        """Reload configuration from sources"""
```

### CellAgent (In-Process Instrumentation)

**Purpose**: Lightweight instrumentation layer embedded in the monitored Python application to collect behavioral telemetry with minimal performance impact.

**Instrumentation Methods** (v1):
1. **Decorator-based**: `@pic.monitor` decorator for explicit function instrumentation (recommended for v1)
2. **Import Hook**: Automatic instrumentation via `sys.meta_path` hook for specified modules (optional)

**Note**: Bytecode/AST transformation deferred to v2 due to complexity with decorators, async functions, and generators

**Telemetry Event Schema** (JSON):
```json
{
  "timestamp": "2025-12-01T10:30:45.123Z",
  "event_id": "uuid-v4",
  "process_id": 12345,
  "thread_id": 67890,
  "function_name": "process_payment",
  "module_name": "app.payments",
  "args_metadata": {
    "arg_count": 3,
    "arg_types": ["str", "float", "dict"],
    "arg_hashes": ["sha256:abc...", "sha256:def...", "sha256:ghi..."]
  },
  "duration_ms": 45.2,
  "resource_tags": {
    "io_operations": 2,
    "network_calls": 1,
    "file_access": 0
  },
  "redaction_applied": true,
  "sampling_rate": 0.1
}
```

**PII Redaction Rules**:
- Email addresses: replaced with `[EMAIL_REDACTED]`
- Phone numbers: replaced with `[PHONE_REDACTED]`
- Credit card numbers: replaced with `[CC_REDACTED]`
- SSN/Tax IDs: replaced with `[ID_REDACTED]`
- IP addresses: last octet zeroed (192.168.1.0)
- All string arguments: hashed with SHA-256, only hash stored

**Performance Optimizations**:
- Adaptive sampling: starts at 1:10, adjusts based on CPU usage
- Lazy serialization: telemetry serialized only when transmitted
- Ring buffer: 10,000 event local buffer with overflow discard
- Batch transmission: events sent in batches of 100 or every 5 seconds
- CPU cap: if CellAgent CPU usage >2%, reduce sampling rate

**Configuration**:
```python
{
  "sampling_rate": 0.1,  # 1 in 10 events
  "buffer_size": 10000,
  "batch_size": 100,
  "batch_interval_sec": 5,
  "cpu_threshold": 0.02,  # 2% CPU limit
  "instrumentation_mode": "decorator",  # decorator|import_hook|bytecode
  "pii_redaction": true,
  "sentinel_endpoint": "https://localhost:8443",
  "mtls_cert": "/path/to/cert.pem",
  "mtls_key": "/path/to/key.pem"
}
```

**Interface**:
```python
class CellAgent:
    def __init__(self, config: Dict[str, Any]):
        """Initialize agent with configuration"""
        
    def instrument(self, target: Union[Callable, str]) -> None:
        """Instrument function or module"""
        
    def start(self) -> None:
        """Start telemetry collection"""
        
    def stop(self) -> None:
        """Stop collection and flush buffers"""
        
    def get_stats(self) -> Dict[str, Any]:
        """Return performance statistics"""
```

### TelemetryTransport (Outbound Communication)

**Purpose**: Reliable batch transmission of telemetry events with retry logic and failure handling.

**Features**:
- Batch accumulation (100 events or 5 seconds)
- Exponential backoff retry (max 5 retries)
- Overflow policy: discard oldest events
- Connection pooling for efficiency

**Retry Logic**:
```
Attempt 1: immediate
Attempt 2: wait 1 second
Attempt 3: wait 2 seconds
Attempt 4: wait 4 seconds
Attempt 5: wait 8 seconds
After 5 failures: discard batch, log error
```

**Interface**:
```python
class TelemetryTransport:
    def __init__(self, endpoint: str, config: PICConfig):
        """Initialize transport with endpoint and config"""
        
    def send_batch(self, events: List[TelemetryEvent]) -> bool:
        """Send batch with retry logic, return success status"""
        
    def get_stats(self) -> Dict[str, Any]:
        """Return transmission statistics"""
```

### FeatureNormalizer (Data Preprocessing)

**Purpose**: Normalize raw telemetry features before anomaly detection to ensure stable statistical comparisons.

**Normalization Methods**:
- **Min-Max Scaling**: Scale to [0, 1] range
- **Outlier Handling**: Cap values at 99th percentile
- **Missing Value Filling**: Use median for missing values

**Algorithm**:
```
For each feature f in [duration_ms, io_ops, net_calls]:
  1. Compute min, max, median, p99 from baseline
  2. Fill missing values with median
  3. Cap outliers at p99
  4. Scale: normalized = (value - min) / (max - min)
  5. Return normalized feature vector
```

**Interface**:
```python
class FeatureNormalizer:
    def __init__(self, baseline: BaselineProfile):
        """Initialize with baseline statistics"""
        
    def normalize(self, event: TelemetryEvent) -> np.ndarray:
        """Normalize event features to [0, 1] range"""
        
    def update_baseline(self, baseline: BaselineProfile) -> None:
        """Update normalization parameters from new baseline"""
```

### CryptoCore (Cryptographic Operations)

**Purpose**: Centralized cryptographic operations for signing, hashing, and key management.

**Operations**:
- HMAC-SHA256 signing for audit logs
- SHA-256 hashing for signatures and PII
- Key generation and rotation
- Signature verification

**Interface**:
```python
class CryptoCore:
    def __init__(self, key_path: str):
        """Initialize with key storage path"""
        
    def hmac_sign(self, data: bytes) -> str:
        """Generate HMAC-SHA256 signature"""
        
    def sha256_hash(self, data: bytes) -> str:
        """Generate SHA-256 hash"""
        
    def verify_signature(self, data: bytes, signature: str) -> bool:
        """Verify HMAC signature"""
        
    def rotate_key(self) -> None:
        """Rotate signing key (keep old key for verification)"""
```

### BrainCore (Analysis Pipeline)

**Purpose**: Core event processing pipeline that orchestrates baseline profiling, anomaly detection, and action decisions.

**Event Processing Pipeline**:
```
1. Receive telemetry event from CellAgent
2. Store in TraceStore (recent buffer)
3. Retrieve baseline from StateStore
4. If baseline insufficient: add to training, allow event
5. Normalize features using FeatureNormalizer
6. Compute anomaly score using AnomalyDetector
7. If score > threshold: create detection candidate
8. Execute action via Effector (allow or block)
9. Log decision to AuditStore
10. Return decision to CellAgent
```

**Interface**:
```python
class BrainCore:
    def __init__(self, config: PICConfig):
        """Initialize with configuration"""
        
    def process_event(self, event: TelemetryEvent) -> Decision:
        """Process single event through pipeline"""
        
    def get_stats(self) -> Dict[str, Any]:
        """Return processing statistics"""
```

### BrainAPI (HTTP/IPC Endpoints)

**Purpose**: HTTP API for CellAgent communication and metrics export.

**Endpoints**:
- `POST /api/v1/telemetry`: Receive telemetry batch
- `GET /health`: Health check (returns 200 if healthy)
- `GET /metrics`: Prometheus metrics
- `GET /status`: System status and statistics
- `GET /version`: Version information

**Interface**:
```python
class BrainAPI:
    def __init__(self, brain_core: BrainCore, config: PICConfig):
        """Initialize API with brain core and config"""
        
    def start(self) -> None:
        """Start HTTP server"""
        
    def stop(self) -> None:
        """Stop HTTP server"""
```

### BrainScheduler (Periodic Tasks)

**Purpose**: Execute periodic maintenance tasks (baseline retraining, cleanup, expiration).

**Scheduled Tasks**:
- Baseline retraining: every 6 hours
- Detector expiration check: every 1 hour
- Trace buffer cleanup: every 1 hour
- Metrics aggregation: every 5 minutes

**Interface**:
```python
class BrainScheduler:
    def __init__(self, brain_core: BrainCore, config: PICConfig):
        """Initialize scheduler with brain core"""
        
    def start(self) -> None:
        """Start background scheduler thread"""
        
    def stop(self) -> None:
        """Stop scheduler and wait for completion"""
```

### Baseline Profiler

**Purpose**: Build statistical profiles of normal behavior for each monitored function.

**Profiling Logic**:
- Collects telemetry for minimum 24 hours OR 50 traces per function
- Computes statistical profile: mean, std dev, min, max, percentiles for duration
- Uses sliding window: 72-hour window, recomputed every 6 hours
- Stores profiles in StateStore with version timestamps

**Anomaly Detection Algorithm**:
```
For each incoming telemetry event E:
  1. Retrieve baseline profile P for E.function_name
  2. If P does not exist: add E to baseline training set, allow event
  3. If P exists but insufficient samples (<50): add E to training, allow event
  4. Compute feature vector V from E: [duration, io_ops, net_calls, ...]
  5. Compute L2 distance: D = ||V - P.mean||₂
  6. Compute percentile rank: R = percentile(D, P.historical_distances)
  7. If R > 95th percentile: flag as anomaly (adaptive threshold)
  8. Compute anomaly score: S = R  # 0-100 scale (percentile-based)
  9. If S > 80: generate detection candidate
  10. If S > 95: immediate quarantine + human review
```

**Note**: v1 uses percentile-based thresholds instead of z-scores to handle non-Gaussian distributions and multi-modal timing patterns common in real workloads

**Note**: v1 uses single-signal detection (timing only). Multi-signal fusion deferred to v1.1

**Configuration**:
```python
{
  "baseline_window_hours": 72,
  "baseline_min_samples": 50,
  "baseline_retrain_interval_hours": 6,
  "anomaly_threshold_zscore": 3.0,
  "candidate_score_threshold": 80,
  "immediate_quarantine_threshold": 95,
  "signal_weights": {
    "timing": 0.3,
    "io": 0.3,
    "network": 0.2,
    "syscalls": 0.2
  },
  "memory_bank_path": "/var/lib/pic/memory.db",
  "sandbox_timeout_sec": 2,
  "sandbox_concurrency": 10
}
```

**Interface**:
```python
class SentinelBrain:
    def __init__(self, config: Dict[str, Any]):
        """Initialize with configuration"""
        
    def process_telemetry(self, event: TelemetryEvent) -> Decision:
        """Process single telemetry event, return decision"""
        
    def generate_candidate(self, anomaly: Anomaly) -> DetectionCandidate:
        """Generate detection candidate from anomaly"""
        
    def validate_candidate(self, candidate: DetectionCandidate) -> ValidationResult:
        """Run candidate through sandbox validation"""
        
    def promote_candidate(self, candidate_id: str, operator: str) -> bool:
        """Promote validated candidate to active detector"""
        
    def rollback_detector(self, detector_id: str, operator: str) -> bool:
        """Rollback detector and update baseline"""
```

### SimpleValidator (Threshold Validation)

**Purpose**: Simple validation of detection candidates against recent benign telemetry (v1 simplified version).

**Validation Logic** (v1):
```
For each detection candidate C:
  1. Load recent benign telemetry from TraceStore (last 100 events)
  2. For each benign event E:
     a. Normalize features
     b. Compute anomaly score using candidate threshold
     c. If score > threshold: increment FP counter
  3. Compute FP rate: FP_count / total_events
  4. If FP_rate > 0.05 (5%): FAIL validation
  5. If FP_rate <= 0.05: PASS validation
  6. Return ValidationResult with FP_rate
```

**Note**: v1 uses simple threshold validation. Full sandbox with process isolation deferred to v1.1

**Interface**:
```python
class SimpleValidator:
    def __init__(self, trace_store: TraceStore):
        """Initialize with trace store"""
        
    def validate_candidate(self, candidate: DetectionCandidate) -> ValidationResult:
        """Validate candidate against recent benign traces"""
```

### Effector

**Purpose**: Execute safe remediation actions (allow, quarantine, block) based on detection decisions.

**Action Semantics** (v1 simplified):
- **Allow**: Event proceeds normally, logged for audit
- **Block**: Event prevented, safe stub value returned, exception raised with safe message

**Note**: Quarantine action deferred to v1.1 for simplicity

**Safe Stub Values**:
- Functions returning bool: return False
- Functions returning int/float: return 0
- Functions returning str: return ""
- Functions returning list/dict: return empty collection
- Functions returning None: return None
- Functions returning objects: raise SafeBlockException

**Rate Limiting** (v1 simplified):
```
Simple counter-based rate limiting:
  Max actions per second: 1000
  If count > max: reject action, return backpressure signal
  Reset counter every second
```

**Note**: Token bucket algorithm deferred to v1.1 for simplicity

**Graceful Fallback**:
- On Effector error: default to allow + log error
- On rate limit exceeded: queue action with priority
- On SentinelBrain unavailable: allow all + buffer decisions

**Configuration**:
```python
{
  "default_action": "allow",  # allow|quarantine|block
  "rate_limit_capacity": 2000,
  "rate_limit_refill_rate": 500,
  "quarantine_log_level": "INFO",
  "block_exception_type": "SafeBlockException",
  "fail_safe_mode": "allow"
}
```

**Interface**:
```python
class Effector:
    def __init__(self, config: Dict[str, Any]):
        """Initialize effector with configuration"""
        
    def execute_action(self, action: Action, context: ExecutionContext) -> ActionResult:
        """Execute remediation action"""
        
    def get_stub_value(self, return_type: Type) -> Any:
        """Get safe stub value for return type"""
        
    def check_rate_limit(self) -> bool:
        """Check if action within rate limit"""
```

### StateStore (Baseline and Detector Storage)

**Purpose**: Persistent storage for baseline profiles and detection signatures using SQLite.

**Schema** (v1 simplified):
```sql
-- Baseline profiles
CREATE TABLE baselines (
    id INTEGER PRIMARY KEY,
    function_name TEXT NOT NULL,
    module_name TEXT NOT NULL,
    version INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    sample_count INTEGER NOT NULL,
    mean_duration_ms REAL,
    std_duration_ms REAL,
    p50_duration_ms REAL,
    p95_duration_ms REAL,
    p99_duration_ms REAL,
    profile_json TEXT NOT NULL,  -- Full profile as JSON
    UNIQUE(function_name, module_name, version)
);

-- Detection signatures
CREATE TABLE detectors (
    id TEXT PRIMARY KEY,  -- UUID
    signature_hash TEXT NOT NULL UNIQUE,  -- SHA-256 of pattern
    function_name TEXT NOT NULL,
    threshold REAL NOT NULL,
    created_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP,  -- TTL (90 days default)
    is_active BOOLEAN DEFAULT 1
);
```

**Note**: Detection history moved to AuditStore, audit_log moved to separate AuditStore

**Signature Storage**:
- Store only non-identifying hashes (SHA-256)
- Include provenance metadata: source, validation results, operator
- TTL: default 90 days, configurable
- Versioning: increment version on baseline updates

**Signature Validation** (for imports):
- Verify cryptographic signature using public key
- Check expiration timestamp
- Validate provenance metadata
- Test against local benign samples before activation

**Configuration**:
```python
{
  "database_path": "/var/lib/pic/memory.db",
  "wal_mode": true,  # Write-Ahead Logging for better concurrency
  "signature_ttl_days": 90,
  "baseline_retention_versions": 10,
  "encryption_key_path": "/etc/pic/db_key",
  "backup_interval_hours": 24,
  "backup_path": "/var/lib/pic/backups/"
}
```

**Note**: v1 uses SQLite with WAL (Write-Ahead Logging) mode to prevent write locks under concurrent access

**Interface**:
```python
class StateStore:
    def __init__(self, db_path: str):
        """Initialize database connection with WAL mode"""
        
    def store_baseline(self, baseline: BaselineProfile) -> None:
        """Store or update baseline profile"""
        
    def get_baseline(self, function_name: str, module_name: str) -> Optional[BaselineProfile]:
        """Retrieve latest baseline profile"""
        
    def store_detector(self, detector: Detector) -> None:
        """Store detector"""
        
    def get_active_detectors(self, function_name: str) -> List[Detector]:
        """Get active detectors for function"""
        
    def expire_old_detectors(self) -> int:
        """Expire detectors past TTL, return count"""
```

### AuditStore (Immutable Log Storage)

**Purpose**: Append-only storage for audit logs with HMAC signing.

**Log Entry Format**:
```json
{
  "timestamp": "2025-12-01T10:30:45.123Z",
  "event_type": "detection",
  "actor": "system",
  "action": "block",
  "target": "suspicious_function",
  "result": "blocked",
  "anomaly_score": 98.5,
  "signature": "hmac-sha256:abc123...",
  "metadata": {}
}
```

**Interface**:
```python
class AuditStore:
    def __init__(self, log_path: str, crypto_core: CryptoCore):
        """Initialize with log file path and crypto core"""
        
    def log_event(self, event: AuditEvent) -> None:
        """Append signed event to log"""
        
    def verify_log_integrity(self) -> bool:
        """Verify all log entries have valid signatures"""
        
    def export_logs(self, start_time: datetime, end_time: datetime) -> List[AuditEvent]:
        """Export logs for forensic analysis"""
```

### TraceStore (Recent Telemetry Buffer)

**Purpose**: In-memory buffer of recent telemetry events for validation and analysis.

**Features**:
- Ring buffer with 1000 event capacity per function
- Automatic eviction of oldest events
- Fast lookup by function name

**Interface**:
```python
class TraceStore:
    def __init__(self, capacity_per_function: int = 1000):
        """Initialize with capacity"""
        
    def add_event(self, event: TelemetryEvent) -> None:
        """Add event to buffer (evict oldest if full)"""
        
    def get_recent_events(self, function_name: str, count: int = 100) -> List[TelemetryEvent]:
        """Get recent events for function"""
        
    def get_stats(self) -> Dict[str, Any]:
        """Return buffer statistics"""
```

### Admin Console

**Purpose**: Web-based user interface for reviewing alerts, managing detection decisions, and accessing explainability traces.

**Features**:
1. **Alert Inbox**: Queue of detection candidates awaiting human review
2. **Decision History**: Searchable log of all promotion/rejection decisions
3. **Explainability Traces**: Detailed view of event sequences, anomaly scores, detector logic
4. **Detector Management**: Enable/disable/rollback active detectors
5. **Baseline Viewer**: Visualize baseline profiles and drift over time
6. **Forensics Export**: Export audit logs and event traces for incident response

**Authentication**:
- OAuth2/OIDC/SAML integration
- Role-based access control: viewer, operator, admin
- Session timeout: 30 minutes idle, 8 hours maximum
- MFA required for admin role

**Explainability Trace Format**:
```json
{
  "detection_id": "uuid",
  "timestamp": "2025-12-01T10:30:45.123Z",
  "event_sequence": [
    {
      "event_id": "uuid",
      "function": "process_payment",
      "duration_ms": 450,
      "baseline_mean": 45,
      "baseline_std": 10,
      "z_score": 40.5,
      "anomaly_score": 99.8
    }
  ],
  "detector_id": "uuid",
  "detector_type": "anomaly",
  "action_taken": "quarantine",
  "sandbox_validation": {
    "passed": true,
    "fp_rate": 0.02,
    "test_count": 100
  },
  "recommendation": "promote",
  "deterministic_hash": "sha256:..."
}
```

**Configuration**:
```python
{
  "listen_address": "0.0.0.0",
  "listen_port": 8080,
  "tls_cert": "/etc/pic/console_cert.pem",
  "tls_key": "/etc/pic/console_key.pem",
  "auth_provider": "oidc",
  "oidc_issuer": "https://auth.example.com",
  "session_timeout_minutes": 30,
  "session_max_hours": 8,
  "require_mfa_for_admin": true
}
```

### Watchdog Process

**Purpose**: Monitor CellAgent integrity and restart on failure or tampering.

**Monitoring**:
- Check CellAgent process health every 10 seconds
- Verify binary hash against signed manifest every 60 seconds
- Monitor CPU/memory usage for anomalies
- Verify mTLS connection to SentinelBrain

**Recovery Actions**:
1. On process crash: restart from trusted binary within 30 seconds
2. On integrity violation: alert admin, attempt restore from backup
3. On resource exhaustion: reduce sampling rate, alert admin
4. On persistent failure (3 restarts in 5 minutes): enter safe mode, alert admin

**Configuration**:
```python
{
  "check_interval_sec": 10,
  "integrity_check_interval_sec": 60,
  "trusted_binary_path": "/usr/lib/pic/cellagent",
  "manifest_path": "/usr/lib/pic/cellagent.manifest",
  "max_restart_attempts": 3,
  "restart_window_sec": 300,
  "alert_endpoint": "https://admin-console:8080/api/alerts"
}
```

## Data Models

### TelemetryEvent
```python
@dataclass
class TelemetryEvent:
    timestamp: datetime
    event_id: str  # UUID
    process_id: int
    thread_id: int
    function_name: str
    module_name: str
    args_metadata: Dict[str, Any]
    duration_ms: float
    resource_tags: Dict[str, int]
    redaction_applied: bool
    sampling_rate: float
```

### BaselineProfile
```python
@dataclass
class BaselineProfile:
    function_name: str
    module_name: str
    version: int
    created_at: datetime
    updated_at: datetime
    sample_count: int
    mean_duration_ms: float
    std_duration_ms: float
    mean_io_ops: float
    std_io_ops: float
    mean_net_calls: float
    std_net_calls: float
    full_profile: Dict[str, Any]
```

### Anomaly
```python
@dataclass
class Anomaly:
    event: TelemetryEvent
    baseline: BaselineProfile
    z_score: float
    anomaly_score: float  # 0-100
    signal_scores: Dict[str, float]
    detected_at: datetime
```

### DetectionCandidate
```python
@dataclass
class DetectionCandidate:
    candidate_id: str  # UUID
    anomaly: Anomaly
    detector_type: str
    threshold: float
    created_at: datetime
    validation_status: str  # pending|passed|failed
    validation_result: Optional[ValidationResult]
```

### ValidationResult
```python
@dataclass
class ValidationResult:
    candidate_id: str
    passed: bool
    fp_rate: float
    test_count: int
    execution_traces: List[Dict[str, Any]]
    completed_at: datetime
```

### Detector
```python
@dataclass
class Detector:
    detector_id: str  # UUID
    signature_hash: str  # SHA-256
    detector_type: str
    created_at: datetime
    expires_at: Optional[datetime]
    promoted_by: str
    promoted_at: datetime
    metadata: Dict[str, Any]
    is_active: bool
```

### Action
```python
@dataclass
class Action:
    action_type: str  # allow|quarantine|block
    detector_id: str
    event: TelemetryEvent
    reason: str
    timestamp: datetime
```

### AuditEvent
```python
@dataclass
class AuditEvent:
    timestamp: datetime
    event_type: str
    actor: str
    action: str
    target: Optional[str]
    result: str
    signature: str  # HMAC-SHA256
    metadata: Dict[str, Any]
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Instrumentation Overhead Bound

*For any* Python application with baseline latency L, when instrumented with CellAgent, the median latency shall not exceed L * 1.05 (5% overhead)
**Validates: Requirements 1.1**

### Property 2: Sampling Rate Accuracy

*For any* configured sampling rate R and sequence of N events (N ≥ 1000), the actual number of sampled events shall be within ±10% of N * R
**Validates: Requirements 1.2, 17.2**

### Property 3: Graceful Instrumentation Failure

*For any* instrumentation error during function wrapping, the monitored application shall continue execution without raising exceptions to the application code
**Validates: Requirements 1.4**

### Property 4: PII Redaction Completeness

*For any* telemetry event containing PII patterns (email, phone, credit card, SSN, IP address), all PII shall be replaced with redaction tokens or hashes before transmission
**Validates: Requirements 1.5, 6.2**

### Property 5: Baseline Profile Convergence

*For any* function with at least 50 telemetry samples, the SentinelBrain shall compute a baseline profile containing mean and standard deviation for duration, I/O operations, and network calls
**Validates: Requirements 2.1, 16.4**

### Property 6: Anomaly Score Monotonicity

*For any* two events E1 and E2 where L2_distance(E1, baseline) < L2_distance(E2, baseline), the anomaly score for E1 shall be less than or equal to the anomaly score for E2
**Validates: Requirements 2.2**

### Property 7: Candidate Generation Threshold

*For any* telemetry event with anomaly score S ≥ 80, the SentinelBrain shall generate a detection candidate
**Validates: Requirements 2.3**

### Property 8: Signal Fusion Weighted Average

*For any* event with multiple behavioral signals, the fused anomaly score shall equal the weighted average of individual signal scores using configured weights
**Validates: Requirements 2.5, 13.1**

### Property 9: Sandbox Isolation Enforcement

*For any* detection candidate executed in the Sandbox Runner, the sandbox process shall enforce resource limits (CPU ≤ 10%, memory ≤ 256MB, I/O ≤ 10MB/s)
**Validates: Requirements 3.2**

### Property 10: Sandbox Verdict Structure

*For any* completed sandbox validation, the ValidationResult shall contain fields: candidate_id, passed (boolean), fp_rate (float), test_count (int), and execution_traces (list)
**Validates: Requirements 3.3**

### Property 11: Promotion Eligibility Rule

*For any* detection candidate with sandbox validation fp_rate ≤ 0.05, the candidate shall be marked as eligible for promotion
**Validates: Requirements 3.5**

### Property 12: Explainability Trace Completeness

*For any* detection candidate presented for review, the explainability trace shall include event_sequence, anomaly_scores, detector_id, action_taken, and sandbox_validation results
**Validates: Requirements 4.2**

### Property 13: Promotion State Transition

*For any* detection candidate approved by an operator, the candidate shall transition to active detector status in the Memory Bank
**Validates: Requirements 4.3**

### Property 14: Rejection Archival

*For any* detection candidate rejected by an operator, the candidate shall be archived with rejection_metadata including operator identity and timestamp
**Validates: Requirements 4.4**

### Property 15: Rollback State Restoration

*For any* detector rollback operation, the system state after rollback shall match the snapshot taken before the detector was promoted (round-trip property)
**Validates: Requirements 4.5, 24.4**

### Property 16: Effector Action Validity

*For any* detection alert, the Effector shall execute exactly one action from the set {allow, quarantine, block}
**Validates: Requirements 5.1**

### Property 17: Quarantine Observability

*For any* quarantined event, the system shall generate audit log entries with enhanced detail level while allowing the event to proceed
**Validates: Requirements 5.2**

### Property 18: Block Stub Type Safety

*For any* blocked function with return type T, the Effector shall return a safe stub value of type T (empty for collections, zero for numbers, False for booleans)
**Validates: Requirements 5.3**

### Property 19: Effector Fail-Safe Default

*For any* error during Effector remediation, the system shall default to allow action and log the error
**Validates: Requirements 5.4**

### Property 20: Token Bucket Rate Limit

*For any* sequence of N action requests in time interval T, the number of executed actions shall not exceed min(N, bucket_capacity + T * refill_rate)
**Validates: Requirements 5.5, 17.5**

### Property 21: Audit Log Immutability

*For any* detection or remediation decision, an audit log entry shall be created that cannot be modified or deleted (append-only)
**Validates: Requirements 6.1**

### Property 22: Audit Log Encryption

*For any* audit log file written to disk, the file contents shall be encrypted using AES-256 or equivalent
**Validates: Requirements 6.3**

### Property 23: Forensic Export Signature

*For any* exported audit log, the export shall include HMAC-SHA256 signatures for integrity verification
**Validates: Requirements 6.5, 20.3**

### Property 24: Signature Hash Storage

*For any* promoted detection candidate, the Memory Bank shall store a SHA-256 hash of the threat pattern (not the raw pattern)
**Validates: Requirements 7.1, 14.1**

### Property 25: Signature Metadata Completeness

*For any* stored detector signature, the metadata shall include provenance, timestamp, expiration_ttl, and promoted_by fields
**Validates: Requirements 7.2**

### Property 26: Signature Query Correctness

*For any* signature hash query, the Memory Bank shall return all matching detector entries with version information
**Validates: Requirements 7.3**

### Property 27: External Signature Validation

*For any* imported external signature without valid cryptographic signature, the Memory Bank shall reject the import
**Validates: Requirements 7.5**

### Property 28: Watchdog Detection Latency

*For any* CellAgent process crash, the watchdog shall detect the failure and initiate restart within 30 seconds
**Validates: Requirements 8.1**

### Property 29: Agent State Recovery Round-Trip

*For any* CellAgent restart, the restored state shall match the last checkpoint state (round-trip property)
**Validates: Requirements 8.2**

### Property 30: Telemetry Buffering Under Disconnection

*For any* period when SentinelBrain is unavailable, the CellAgent shall buffer telemetry events locally with backpressure when buffer exceeds capacity
**Validates: Requirements 8.3**

### Property 31: Circuit Breaker Activation

*For any* resource exhaustion condition in Sandbox Runner, the circuit breaker shall activate and reject new sandbox requests until resources recover
**Validates: Requirements 8.4**

### Property 32: Fail-Safe Observe Mode

*For any* Admin Console disconnection, the system shall continue operation in observe-only mode (all actions default to allow with logging)
**Validates: Requirements 8.5**

### Property 33: Binary Integrity Detection

*For any* modification to the CellAgent binary file, the watchdog shall detect the integrity violation via SHA-256 hash mismatch
**Validates: Requirements 9.1, 19.3**

### Property 34: Integrity Violation Response

*For any* detected integrity violation, the watchdog shall generate an alert and attempt to restore the agent from a trusted source
**Validates: Requirements 9.2**

### Property 35: Module Signature Verification

*For any* agent module loaded without valid code signature, the CellAgent shall reject the module and log the rejection
**Validates: Requirements 9.3**

### Property 36: IPC Access Control

*For any* unauthorized process attempting IPC access to CellAgent, the access shall be denied
**Validates: Requirements 9.4**

### Property 37: Vulnerable Dependency Rejection

*For any* dependency with critical CVE vulnerability, the CI pipeline shall fail the build
**Validates: Requirements 10.2, 25.4**

### Property 38: SBOM Format Compliance

*For any* CI build, the generated SBOM shall be valid CycloneDX JSON format
**Validates: Requirements 10.3, 25.2**

### Property 39: Artifact Signature Presence

*For any* published container image or pip package, the artifact shall include a cryptographic signature (Cosign for containers, GPG for packages)
**Validates: Requirements 10.4**

### Property 40: Installation Prerequisite Validation

*For any* installation attempt on a system missing prerequisites (Python < 3.9, missing capabilities), the installer shall detect and report the missing requirements
**Validates: Requirements 11.3**

### Property 41: Polymorphic Behavioral Detection

*For any* two code variants V1 and V2 with identical behavioral signatures (same I/O patterns, timing, network calls), if V1 is detected as malicious, V2 shall also be detected
**Validates: Requirements 13.2**

### Property 42: Mutation Variant Generation

*For any* detection candidate, the mutation engine shall generate at least 3 variants with threshold adjustments of ±10%
**Validates: Requirements 13.3**

### Property 43: Privacy Policy Application

*For any* configured privacy policy P and telemetry event E, the system shall apply policy P's redaction rules to E before storage
**Validates: Requirements 14.4**

### Property 44: Adaptive Sampling Under Load

*For any* period where CellAgent CPU usage exceeds 2%, the sampling rate shall decrease to maintain CPU usage below threshold
**Validates: Requirements 15.1**

### Property 45: Priority Queue Ordering

*For any* two events E1 (critical) and E2 (normal) in the SentinelBrain queue, E1 shall be processed before E2
**Validates: Requirements 15.2**

### Property 46: Backpressure Activation

*For any* resource consumption exceeding configured thresholds, the system shall activate backpressure and slow event ingestion
**Validates: Requirements 15.3**

### Property 47: Concurrent Sandbox Resource Caps

*For any* N concurrent sandbox executions, the total resource consumption shall not exceed N * per_sandbox_limit
**Validates: Requirements 15.5**

### Property 48: FPR Calculation Correctness

*For any* test dataset with B benign sessions and F flagged sessions, the computed FPR shall equal F / B
**Validates: Requirements 16.1**

### Property 49: TPR Calculation Correctness

*For any* test dataset with M malicious sessions and D detected sessions, the computed TPR shall equal D / M
**Validates: Requirements 16.2**

### Property 50: Latency Percentile Reporting

*For any* benchmark run, the latency report shall include median (P50), P95, and P99 percentiles
**Validates: Requirements 16.3**

### Property 51: Anomaly Threshold Formula

*For any* baseline profile with mean distance μ and standard deviation σ, the default anomaly threshold shall equal μ + 3σ
**Validates: Requirements 16.5**

### Property 52: Telemetry Event Schema Compliance

*For any* generated telemetry event, the JSON shall contain all required fields: timestamp, process_id, thread_id, function_name, args_metadata, duration_ms, resource_tags, redaction_hashes
**Validates: Requirements 17.1**

### Property 53: RBAC Permission Enforcement

*For any* user with role R attempting action A, the action shall succeed if and only if R has permission for A (viewer: read-only, operator: approve/reject, admin: all)
**Validates: Requirements 18.2**

### Property 54: mTLS Communication Enforcement

*For any* communication between CellAgent and SentinelBrain, the connection shall use mutual TLS with certificate validation
**Validates: Requirements 18.3**

### Property 55: Token Validation Completeness

*For any* API request with token T, the system shall validate T's signature, expiration, and scope before processing the request
**Validates: Requirements 18.4**

### Property 56: Audit Log HMAC Signing

*For any* audit log entry, the entry shall include an HMAC-SHA256 signature computed over the entry content and timestamp
**Validates: Requirements 18.5**

### Property 57: Key Rotation Backward Compatibility

*For any* signature created with key K1, after rotating to key K2, the signature shall still validate successfully using K1's public key
**Validates: Requirements 19.2**

### Property 58: Key Access Audit Logging

*For any* access to cryptographic key material, an audit log entry shall be created with principal identity and timestamp
**Validates: Requirements 19.5**

### Property 59: Alert Timing SLA

*For any* high-severity detection, an alert shall be sent to operators within 30 minutes
**Validates: Requirements 20.4**

### Property 60: Acknowledgment Audit Trail

*For any* operator acknowledgment of an alert, the Audit Store shall record the acknowledgment with timestamp and operator identity
**Validates: Requirements 20.5**

### Property 61: Synthetic Data Reproducibility

*For any* data generator with seed S, running the generator twice with seed S shall produce identical output
**Validates: Requirements 21.4**

### Property 62: Metadata Retention Policy

*For any* telemetry metadata stored at time T, the metadata shall be retained until time T + 90 days (default, configurable)
**Validates: Requirements 22.1**

### Property 63: Trace Retention Policy

*For any* execution trace stored at time T, the trace shall be retained until time T + 30 days (default, configurable)
**Validates: Requirements 22.2**

### Property 64: Local-Only Mode Network Isolation

*For any* system with local-only mode enabled, zero telemetry packets shall be transmitted over network interfaces (excluding loopback)
**Validates: Requirements 22.3**

### Property 65: Prometheus Metrics Completeness

*For any* Prometheus scrape, the metrics endpoint shall expose all required metrics: event_rate, avg_latency, fpr_estimate, detector_count, sandbox_queue_length, watchdog_status
**Validates: Requirements 23.1**

### Property 66: Performance Regression Detection

*For any* CI run with performance metrics M, if M deviates from baseline B by more than threshold T, the CI pipeline shall fail
**Validates: Requirements 23.3**

### Property 67: CSV Metrics Export Format

*For any* long-running test, the exported metrics file shall be valid CSV format with headers
**Validates: Requirements 23.5**

### Property 68: Canary Health Check FPR Bound

*For any* canary deployment, if the observed FPR exceeds 2x baseline FPR, the health check shall fail
**Validates: Requirements 24.2**

### Property 69: Canary Auto-Rollback Trigger

*For any* failed canary health check, the deployment system shall automatically initiate rollback within 5 minutes
**Validates: Requirements 24.3**


## Error Handling

### CellAgent Error Handling

**Instrumentation Errors**:
- Decorator application failure: Log error, skip instrumentation for that function, continue
- Import hook failure: Log error, fall back to non-instrumented import
- Bytecode transformation error: Log error, use original bytecode

**Telemetry Collection Errors**:
- Serialization failure: Log error, discard event, continue collection
- Buffer overflow: Apply backpressure, discard oldest events (ring buffer)
- Network transmission failure: Buffer locally, retry with exponential backoff (max 5 retries)

**PII Redaction Errors**:
- Redaction pattern failure: Log error, redact entire field as `[REDACTED_ERROR]`
- Hash computation failure: Log error, use placeholder hash

### SentinelBrain Error Handling

**Baseline Computation Errors**:
- Insufficient samples: Defer baseline creation, continue collecting
- Statistical computation failure (division by zero, etc.): Use default thresholds, log error
- Database write failure: Retry 3 times, then alert admin

**Anomaly Detection Errors**:
- Missing baseline: Allow event, add to training set
- L2 distance computation failure: Default to anomaly score 0 (allow), log error
- Candidate generation failure: Log error, continue processing

**Sandbox Validation Errors**:
- Sandbox process crash: Mark validation as failed, log crash details
- Timeout: Kill sandbox, mark as failed
- Resource limit violation: Terminate sandbox, mark as failed

### Effector Error Handling

**Action Execution Errors**:
- Unknown action type: Default to allow, log error
- Stub value generation failure: Return None, log error
- Rate limit state corruption: Reset rate limiter, log error, allow action

**Fail-Safe Behavior**:
- Any unhandled exception: Catch at top level, log, default to allow action
- SentinelBrain unavailable: Allow all actions, buffer decisions locally
- Memory Bank unavailable: Use in-memory cache, alert admin

### Memory Bank Error Handling

**Database Errors**:
- Connection failure: Retry with exponential backoff, max 10 retries
- Write failure: Retry transaction 3 times, then alert admin
- Corruption detected: Restore from latest backup, alert admin
- Disk full: Trigger log rotation, delete expired entries, alert admin

**Query Errors**:
- Malformed query: Return empty result set, log error
- Timeout: Cancel query, return partial results, log warning

### Admin Console Error Handling

**Authentication Errors**:
- Invalid credentials: Return 401, log attempt
- Expired session: Return 401, redirect to login
- MFA failure: Return 401, increment failure counter, lock after 5 failures

**API Errors**:
- Invalid request: Return 400 with error details
- Unauthorized action: Return 403, log attempt
- Internal error: Return 500, log stack trace, alert admin

### Watchdog Error Handling

**Monitoring Errors**:
- Process check failure: Retry immediately, if persistent, alert admin
- Integrity check failure: Alert admin immediately, attempt restore
- Hash computation failure: Log error, skip integrity check cycle

**Recovery Errors**:
- Restart failure: Retry up to 3 times, then enter safe mode and alert admin
- Restore from backup failure: Alert admin, require manual intervention
- Persistent failure (3 restarts in 5 minutes): Enter safe mode, alert admin

## Testing Strategy

### Unit Testing

**Framework**: pytest with pytest-cov for coverage reporting

**Scope**:
- Individual component functions and methods
- Data model validation and serialization
- Algorithm correctness (anomaly scoring, token bucket, etc.)
- Error handling paths
- Configuration parsing and validation

**Coverage Target**: ≥ 80% line coverage for core logic

**Example Unit Tests**:
```python
def test_telemetry_event_serialization():
    """Test TelemetryEvent serializes to valid JSON"""
    event = TelemetryEvent(...)
    json_str = event.to_json()
    assert json.loads(json_str)  # Valid JSON
    assert "timestamp" in json_str
    
def test_pii_redaction_email():
    """Test email addresses are redacted"""
    text = "Contact user@example.com for info"
    redacted = redact_pii(text)
    assert "[EMAIL_REDACTED]" in redacted
    assert "user@example.com" not in redacted
    
def test_token_bucket_rate_limit():
    """Test token bucket enforces rate limit"""
    bucket = TokenBucket(capacity=100, refill_rate=10)
    # Consume all tokens
    for _ in range(100):
        assert bucket.consume(1) == True
    # Next should fail
    assert bucket.consume(1) == False
```

### Property-Based Testing

**Framework**: Hypothesis (Python property-based testing library)

**Configuration**: Minimum 100 iterations per property test

**Scope**: All 69 correctness properties defined in the design document

**Property Test Structure**:
```python
from hypothesis import given, strategies as st

@given(st.integers(min_value=1, max_value=10000))
def test_property_2_sampling_rate_accuracy(event_count):
    """
    Feature: pic-v1-immune-core, Property 2: Sampling Rate Accuracy
    For any configured sampling rate R and sequence of N events (N ≥ 1000),
    the actual number of sampled events shall be within ±10% of N * R
    """
    sampling_rate = 0.1
    agent = CellAgent(config={"sampling_rate": sampling_rate})
    
    # Generate events
    events = [create_test_event(i) for i in range(event_count)]
    sampled = [e for e in events if agent.should_sample(e)]
    
    expected = event_count * sampling_rate
    tolerance = expected * 0.1
    
    assert abs(len(sampled) - expected) <= tolerance
```

**Generator Strategies**:
- Telemetry events: Generate with random but valid field values
- Baseline profiles: Generate with realistic statistical distributions
- Detection candidates: Generate with varying anomaly scores
- Configuration: Generate with valid parameter ranges

### Integration Testing

**Framework**: pytest with docker-compose for multi-component tests

**Scope**:
- End-to-end flows: telemetry collection → detection → sandbox → promotion
- Component interactions: CellAgent ↔ SentinelBrain ↔ Memory Bank
- Authentication and authorization flows
- Failure recovery scenarios

**Test Environment**: Docker containers with isolated networks

**Example Integration Tests**:
```python
def test_end_to_end_detection_flow():
    """Test complete detection flow from telemetry to promotion"""
    # Setup: Start all components
    agent = start_cellagent()
    sentinel = start_sentinelbrain()
    sandbox = start_sandbox_runner()
    
    # Generate benign baseline
    for _ in range(100):
        agent.instrument_and_call(benign_function)
    
    # Wait for baseline establishment
    wait_for_baseline(sentinel, "benign_function")
    
    # Generate anomalous event
    agent.instrument_and_call(malicious_function)
    
    # Verify candidate generated
    candidates = sentinel.get_pending_candidates()
    assert len(candidates) == 1
    
    # Verify sandbox validation
    result = sandbox.validate(candidates[0])
    assert result.passed == True
    
    # Promote candidate
    sentinel.promote_candidate(candidates[0].id, operator="test_user")
    
    # Verify detector active
    detectors = sentinel.get_active_detectors()
    assert any(d.candidate_id == candidates[0].id for d in detectors)
```

### Stress Testing

**Framework**: Locust for load generation, pytest for validation

**Scenarios**:
1. **High-Throughput Telemetry**: 10,000 events/second for 1 hour
2. **Concurrent Sandbox Validation**: 50 concurrent sandbox runs
3. **Memory Leak Detection**: 24-hour continuous operation with memory monitoring
4. **Database Stress**: 1,000 concurrent queries to Memory Bank

**Metrics Collected**:
- Latency (P50, P95, P99)
- Throughput (events/second)
- Resource usage (CPU, memory, disk I/O)
- Error rates
- Queue depths

**Acceptance Criteria**:
- Latency overhead ≤ 5% under normal load
- No memory leaks (memory growth < 1% per hour)
- Error rate < 0.1%
- System remains responsive (P99 latency < 1 second)

### Security Testing

**Scope**: Defensive validation only (no offensive testing)

**Test Categories**:

1. **Integrity Verification**:
   - Tamper with CellAgent binary, verify watchdog detection
   - Modify audit logs, verify signature validation fails
   - Import unsigned signatures, verify rejection

2. **Access Control**:
   - Attempt unauthorized IPC access, verify denial
   - Attempt API access with invalid tokens, verify rejection
   - Attempt role escalation, verify prevention

3. **Data Protection**:
   - Verify PII redaction in all telemetry
   - Verify encryption at rest for audit logs
   - Verify mTLS for all network communication

4. **Denial of Service Protection**:
   - Flood with telemetry events, verify rate limiting
   - Exhaust sandbox resources, verify circuit breaker
   - Spam API endpoints, verify rate limiting

**Example Security Test**:
```python
def test_binary_tamper_detection():
    """Test watchdog detects binary modification"""
    # Start watchdog
    watchdog = start_watchdog()
    agent_path = "/usr/lib/pic/cellagent"
    
    # Record original hash
    original_hash = compute_sha256(agent_path)
    
    # Tamper with binary
    with open(agent_path, "ab") as f:
        f.write(b"TAMPERED")
    
    # Wait for integrity check cycle
    time.sleep(65)  # Integrity check every 60 seconds
    
    # Verify alert generated
    alerts = get_watchdog_alerts()
    assert any("integrity violation" in a.message for a in alerts)
    
    # Verify restore attempted
    current_hash = compute_sha256(agent_path)
    assert current_hash == original_hash
```

### Acceptance Testing

**Datasets**:
- Golden benign dataset: 10,000 labeled benign sessions
- Golden malicious dataset: 2,000 labeled mid-tier threat sessions
- Polymorphic variant dataset: 2,000 polymorphic attack sessions

**Acceptance Criteria** (Go/No-Go):
1. False Positive Rate ≤ 5% on benign dataset
2. True Positive Rate ≥ 75% on malicious dataset
3. Median latency overhead ≤ 5% under baseline load
4. Sandbox validation completes in ≤ 2 seconds average
5. Watchdog recovery time ≤ 30 seconds
6. CI pipeline green for 3 consecutive runs
7. SBOM clear of critical CVEs
8. All 69 property-based tests pass with 100 iterations

**Test Execution**:
```bash
# Run acceptance test suite
pytest tests/acceptance/ \
  --dataset-benign=data/golden_benign.json \
  --dataset-malicious=data/golden_malicious.json \
  --dataset-polymorphic=data/golden_polymorphic.json \
  --acceptance-criteria=acceptance_criteria.yaml \
  --junit-xml=acceptance_results.xml
```

### Continuous Integration

**Pipeline Stages**:
1. **Lint**: flake8, black, mypy
2. **Unit Tests**: pytest with coverage
3. **Property Tests**: Hypothesis tests (100 iterations)
4. **Integration Tests**: Docker-compose environment
5. **Security Scans**: Bandit, Safety, Snyk
6. **SBOM Generation**: CycloneDX
7. **Build Artifacts**: pip package, container image
8. **Sign Artifacts**: Cosign, GPG
9. **Acceptance Tests**: Full acceptance suite
10. **Performance Regression**: Compare against baseline

**GitHub Actions Workflow**:
```yaml
name: PIC v1 CI Pipeline

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Lint
        run: |
          flake8 src/ tests/
          black --check src/ tests/
          mypy src/
      
      - name: Unit Tests
        run: pytest tests/unit/ --cov=src --cov-report=xml
      
      - name: Property Tests
        run: pytest tests/property/ --hypothesis-iterations=100
      
      - name: Integration Tests
        run: |
          docker-compose -f tests/integration/docker-compose.yml up -d
          pytest tests/integration/
          docker-compose -f tests/integration/docker-compose.yml down
      
      - name: Security Scans
        run: |
          bandit -r src/
          safety check
          snyk test --severity-threshold=critical
      
      - name: Generate SBOM
        run: cyclonedx-py -o sbom.json
      
      - name: Build Artifacts
        run: |
          python setup.py sdist bdist_wheel
          docker build -t pic-v1:${{ github.sha }} .
      
      - name: Sign Artifacts
        run: |
          cosign sign pic-v1:${{ github.sha }}
          gpg --detach-sign dist/*.whl
      
      - name: Acceptance Tests
        run: pytest tests/acceptance/ --acceptance-criteria=acceptance_criteria.yaml
      
      - name: Performance Regression
        run: |
          pytest tests/performance/ --benchmark-json=benchmark.json
          python scripts/compare_benchmarks.py baseline.json benchmark.json
```

## Deployment Architecture

### Packaging

**Pip Package Structure**:
```
pic-v1/
├── setup.py
├── pyproject.toml
├── README.md
├── LICENSE
├── MANIFEST.in
├── requirements.txt
├── src/
│   └── pic/
│       ├── __init__.py
│       ├── cellagent/
│       ├── sentinelbrain/
│       ├── sandbox/
│       ├── effector/
│       ├── memory/
│       ├── console/
│       └── watchdog/
└── tests/
```

**Container Image** (Multi-stage Dockerfile):
```dockerfile
# Stage 1: Build
FROM python:3.9-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --user -r requirements.txt
COPY src/ ./src/
RUN python -m compileall src/

# Stage 2: Runtime
FROM python:3.9-slim
RUN useradd -m -u 1000 pic
COPY --from=builder /root/.local /home/pic/.local
COPY --from=builder /build/src /app/src
COPY config/ /app/config/
USER pic
WORKDIR /app
ENV PATH=/home/pic/.local/bin:$PATH
ENTRYPOINT ["python", "-m", "pic.sentinelbrain"]
```

### Deployment Modes

**1. Standalone (Developer Workstation)**:
- CellAgent embedded in application process
- SentinelBrain runs as local service (systemd/launchd)
- Admin Console accessible on localhost:8080
- SQLite Memory Bank in ~/.pic/

**2. Containerized (Docker/Kubernetes)**:
- CellAgent sidecar container
- SentinelBrain deployment with persistent volume
- Admin Console ingress with TLS
- PostgreSQL Memory Bank (optional)

**3. Cloud VM (AWS/GCP/Azure)**:
- CellAgent installed via pip
- SentinelBrain systemd service
- Admin Console behind load balancer
- RDS/Cloud SQL Memory Bank (optional)

### Configuration Management

**Configuration Files**:
- `/etc/pic/cellagent.yaml`: CellAgent configuration
- `/etc/pic/sentinelbrain.yaml`: SentinelBrain configuration
- `/etc/pic/console.yaml`: Admin Console configuration
- `/etc/pic/watchdog.yaml`: Watchdog configuration

**Environment Variables** (override config files):
- `PIC_SAMPLING_RATE`: Override sampling rate
- `PIC_SENTINEL_ENDPOINT`: SentinelBrain endpoint
- `PIC_MEMORY_BANK_PATH`: Database path
- `PIC_LOG_LEVEL`: Logging level

**Secrets Management**:
- mTLS certificates: Mounted from Kubernetes secrets or AWS Secrets Manager
- Database credentials: Retrieved from KMS/Vault
- API tokens: Generated and stored in secure keystore

### Monitoring and Observability

**Metrics** (Prometheus format):
```
# CellAgent metrics
pic_cellagent_events_total{status="sampled|dropped"}
pic_cellagent_latency_seconds{quantile="0.5|0.95|0.99"}
pic_cellagent_cpu_usage_percent
pic_cellagent_memory_bytes

# SentinelBrain metrics
pic_sentinel_baselines_total
pic_sentinel_detections_total{action="allow|quarantine|block"}
pic_sentinel_candidates_total{status="pending|promoted|rejected"}
pic_sentinel_fpr_estimate
pic_sentinel_tpr_estimate

# Sandbox metrics
pic_sandbox_validations_total{result="passed|failed|timeout"}
pic_sandbox_queue_length
pic_sandbox_duration_seconds

# Watchdog metrics
pic_watchdog_status{status="healthy|degraded|failed"}
pic_watchdog_restarts_total
pic_watchdog_integrity_checks_total{result="pass|fail"}
```

**Logging**:
- Structured JSON logs
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Log rotation: 100MB per file, keep 10 files
- Centralized logging: Fluentd/Logstash to Elasticsearch

**Tracing**:
- OpenTelemetry instrumentation
- Distributed tracing for multi-component flows
- Trace sampling: 1% of requests

### Backup and Recovery

**Backup Strategy**:
- Memory Bank: Daily full backup, hourly incremental
- Configuration: Version controlled in Git
- Audit logs: Continuous replication to S3/GCS

**Recovery Procedures**:
1. **Database Corruption**: Restore from latest backup, replay audit log
2. **Configuration Error**: Revert to previous Git commit
3. **Component Failure**: Watchdog auto-restart, manual intervention if persistent
4. **Data Loss**: Restore from backup, accept potential data loss window

### Scaling Considerations

**Horizontal Scaling**:
- CellAgent: Scales with application instances (1:1)
- SentinelBrain: Can run multiple instances with shared Memory Bank
- Sandbox Runner: Can run on dedicated worker nodes
- Admin Console: Stateless, can run multiple replicas

**Vertical Scaling**:
- Memory Bank: Increase database resources for large deployments
- SentinelBrain: Increase CPU for high-throughput anomaly detection
- Sandbox Runner: Increase memory for concurrent sandbox executions

**Performance Tuning**:
- Adjust sampling rate based on load
- Tune baseline window size for faster convergence
- Increase sandbox concurrency for high candidate volume
- Use read replicas for Memory Bank queries


## Security Considerations

### Threat Model

**Assets Protected**:
- Application logic and business data
- Configuration files and secrets
- Runtime telemetry and behavioral data
- Detection signatures and baselines
- Audit logs and forensic evidence

**Threats Defended Against** (v1 scope):
- Scripted data exfiltration attempts
- Simple polymorphic malware variants
- Injection of untrusted modules
- Rogue plugins with anomalous behavior
- Insider threats with abnormal access patterns

**Threats Out of Scope** (v1):
- Nation-state kernel exploits
- Hardware backdoors and firmware attacks
- Zero-day vulnerabilities in Python runtime
- Physical access attacks
- Advanced persistent threats with long-term stealth

**Trust Boundaries**:
- CellAgent trusts the monitored application (same process)
- SentinelBrain trusts CellAgent (mTLS authenticated)
- Admin Console trusts authenticated operators (OAuth2/OIDC)
- Memory Bank trusts SentinelBrain (local access only)
- Watchdog trusts signed binaries (cryptographic verification)

### Attack Surface Minimization

**CellAgent**:
- Minimal privileges: No root/admin required
- Restricted IPC: Only authorized processes
- No network listeners: Outbound connections only
- Code signing: All modules cryptographically signed

**SentinelBrain**:
- Local service: No public network exposure
- mTLS required: All client connections authenticated
- Input validation: All telemetry events validated against schema
- Rate limiting: Protection against event floods

**Sandbox Runner**:
- Process isolation: Separate process per sandbox
- Resource limits: cgroups enforce CPU/memory/I/O caps
- Seccomp profile: Whitelist syscalls only
- Network isolation: No network access except loopback
- Filesystem isolation: Read-only root, tmpfs for /tmp

**Admin Console**:
- Authentication required: OAuth2/OIDC/SAML
- MFA for admin role: Two-factor authentication
- HTTPS only: TLS 1.3 with strong ciphers
- CSRF protection: Token-based validation
- Rate limiting: API request throttling

**Memory Bank**:
- Local access only: No network exposure
- Encryption at rest: AES-256 for sensitive data
- Access control: File permissions restrict access
- Backup encryption: Encrypted backups

### Data Protection

**PII Handling**:
- Redaction at source: CellAgent redacts before transmission
- Hash-only storage: Only SHA-256 hashes stored, not raw data
- Configurable policies: Per-jurisdiction privacy rules
- Audit trail: All PII access logged

**Encryption**:
- In transit: mTLS for all network communication
- At rest: AES-256 for audit logs and backups
- Key management: KMS/HSM integration
- Key rotation: 90-day rotation schedule

**Data Minimization**:
- Metadata only: Store only behavioral metadata, not content
- Retention limits: 90-day default for metadata, 30-day for traces
- Automatic deletion: Expired data automatically purged
- Local-only mode: Option to prevent all network transmission

### Integrity Protection

**Binary Integrity**:
- Code signing: All binaries signed with private key
- Manifest verification: SHA-256 hashes in signed manifest
- Watchdog monitoring: Continuous integrity checks
- Automatic restore: Restore from trusted source on tampering

**Audit Log Integrity**:
- HMAC signing: Each entry signed with HMAC-SHA256
- Append-only: No modification or deletion allowed
- Timestamp verification: Monotonic timestamp enforcement
- Export signatures: Forensic exports include signatures

**Configuration Integrity**:
- Version control: All configs in Git with signed commits
- Checksum verification: Config files checksummed on load
- Rollback capability: Revert to previous known-good config

### Compliance and Governance

**Regulatory Compliance**:
- GDPR: Data minimization, right to erasure, consent management
- CCPA: Privacy policy disclosure, opt-out mechanism
- HIPAA: Encryption, access controls, audit logging (if applicable)
- SOC 2: Security controls, monitoring, incident response

**Legal Considerations**:
- Export controls: Cryptography export compliance notes
- Licensing: Dual license (Apache-2.0 / Commercial)
- Terms of service: EULA template for legal review
- Privacy policy: Template for data collection disclosure

**Audit and Accountability**:
- Immutable logs: All actions logged to append-only store
- Operator identity: All decisions attributed to operators
- Forensic export: Complete audit trail exportable
- Retention policy: Configurable retention periods

## Potential Problems and Mitigations

### Problem 1: False Positives

**Description**: Benign behavior incorrectly flagged as malicious, disrupting legitimate operations

**Probability**: Medium (expected during initial deployment)

**Impact**: High (user frustration, loss of trust)

**Mitigations**:
1. **Sandbox Validation**: All candidates tested against benign dataset before promotion (FP rate ≤ 5%)
2. **Human-in-Loop**: Manual approval required for all promotions
3. **Conservative Thresholds**: Default anomaly threshold = mean + 3σ (99.7% of normal behavior allowed)
4. **Rollback Capability**: One-click rollback to previous state with snapshot restore
5. **Baseline Training Period**: Minimum 24 hours / 50 samples before enforcement

**Test Case**:
```python
def test_false_positive_mitigation():
    """Verify benign plugin does not trigger false positive"""
    # Setup: Establish baseline with benign behavior
    agent = CellAgent()
    for _ in range(100):
        agent.instrument_and_call(benign_function)
    
    # Install benign plugin with slightly different behavior
    install_plugin("benign_plugin_v2")
    
    # Execute plugin
    result = execute_plugin("benign_plugin_v2")
    
    # Verify: Should not be blocked
    assert result.action == "allow"
    assert result.anomaly_score < 80  # Below candidate threshold
```

### Problem 2: False Negatives

**Description**: Malicious behavior not detected, allowing threats to proceed

**Probability**: Medium (polymorphic threats, novel attacks)

**Impact**: High (security breach, data loss)

**Mitigations**:
1. **Multi-Signal Fusion**: Combine timing, I/O, network, syscall signals (weighted ensemble)
2. **Ensemble Detectors**: Multiple detection algorithms (anomaly, signature, heuristic)
3. **Periodic Retraining**: Baseline updated every 6 hours with recent data
4. **Polymorphic Detection**: Behavioral similarity matching despite code differences
5. **Red-Team Exercises**: Scheduled testing with simulated attacks (quarterly)

**Test Case**:
```python
def test_polymorphic_variant_detection():
    """Verify polymorphic variant of known threat is detected"""
    # Setup: Train detector on original threat
    agent = CellAgent()
    sentinel = SentinelBrain()
    
    # Generate baseline
    for _ in range(100):
        agent.instrument_and_call(benign_function)
    
    # Detect original threat
    result1 = agent.instrument_and_call(malicious_function_v1)
    assert result1.anomaly_score > 80
    
    # Test polymorphic variant (same behavior, different code)
    result2 = agent.instrument_and_call(malicious_function_v2)
    assert result2.anomaly_score > 80  # Should also detect
```

### Problem 3: Denial of Service Against PIC

**Description**: Attacker floods PIC with events to exhaust resources

**Probability**: Medium (if PIC is known to be deployed)

**Impact**: Medium (PIC degraded, but fail-safe allows application to continue)

**Mitigations**:
1. **Token Bucket Rate Limiter**: 2000 token capacity, 500 tokens/sec refill
2. **Backpressure**: When buffer >80% full, slow event ingestion
3. **Prioritized Queue**: Critical events processed first
4. **Circuit Breaker**: Reject new requests when resources exhausted
5. **Adaptive Sampling**: Reduce sampling rate when CPU >2%

**Test Case**:
```python
def test_dos_protection():
    """Verify rate limiting protects against event flood"""
    agent = CellAgent()
    
    # Flood with 10,000 events rapidly
    start_time = time.time()
    for i in range(10000):
        agent.collect_telemetry(create_test_event(i))
    duration = time.time() - start_time
    
    # Verify: Rate limiting applied
    # Max throughput = 500 events/sec
    assert duration >= 10000 / 500  # At least 20 seconds
    
    # Verify: System remains responsive
    response_time = agent.ping()
    assert response_time < 1.0  # <1 second response
```

### Problem 4: PIC Agent Compromised

**Description**: Attacker targets PIC agent to disable security monitoring

**Probability**: Low (requires elevated privileges)

**Impact**: High (security monitoring disabled)

**Mitigations**:
1. **Binary Integrity Checks**: Watchdog verifies SHA-256 hash every 60 seconds
2. **Code Signing**: All agent modules cryptographically signed
3. **Watchdog Process**: Independent process monitors agent health
4. **Automatic Restore**: Restore from trusted source on tampering
5. **Minimal Privileges**: Agent runs with minimal required privileges
6. **Restricted IPC**: Only authorized processes can communicate

**Test Case**:
```python
def test_agent_tamper_detection():
    """Verify watchdog detects and recovers from agent tampering"""
    # Start watchdog and agent
    watchdog = start_watchdog()
    agent = start_cellagent()
    agent_path = agent.get_binary_path()
    
    # Tamper with agent binary
    with open(agent_path, "ab") as f:
        f.write(b"MALICIOUS_CODE")
    
    # Wait for integrity check (60 second cycle)
    time.sleep(65)
    
    # Verify: Tampering detected
    alerts = watchdog.get_alerts()
    assert any("integrity violation" in a.message for a in alerts)
    
    # Verify: Agent restored
    current_hash = compute_sha256(agent_path)
    expected_hash = get_trusted_hash()
    assert current_hash == expected_hash
    
    # Verify: Agent operational
    assert agent.is_healthy()
```

### Problem 5: Unsafe Automatic Code Mutation

**Description**: System automatically modifies application code, introducing bugs

**Probability**: N/A (explicitly prevented in v1)

**Impact**: Critical (application crashes, data corruption)

**Mitigations**:
1. **No Code Modification**: v1 explicitly disallows automatic code changes
2. **Detection Only**: Mutations affect only detection thresholds, not program code
3. **Sandbox + Human Approval**: All changes require sandbox validation + human approval
4. **Rollback Capability**: All changes reversible with snapshot restore

**Test Case**:
```python
def test_no_code_modification():
    """Verify system never modifies application code"""
    # Setup: Monitor application code files
    app_files = get_application_files()
    original_hashes = {f: compute_sha256(f) for f in app_files}
    
    # Run PIC for 1 hour with various detections
    agent = CellAgent()
    sentinel = SentinelBrain()
    run_for_duration(hours=1)
    
    # Verify: No application files modified
    current_hashes = {f: compute_sha256(f) for f in app_files}
    assert original_hashes == current_hashes
```

### Problem 6: Performance Overhead

**Description**: PIC instrumentation degrades application performance

**Probability**: Medium (depends on sampling rate and workload)

**Impact**: Medium (user experience degraded)

**Mitigations**:
1. **Adaptive Sampling**: Start at 1:10, adjust based on CPU usage
2. **Lazy Serialization**: Serialize only when transmitting
3. **Ring Buffer**: Discard oldest events on overflow (no blocking)
4. **Batch Transmission**: Send events in batches of 100
5. **CPU Cap**: Reduce sampling if CellAgent CPU >2%
6. **Compile-Time Options**: Bytecode instrumentation optional

**Test Case**:
```python
def test_performance_overhead():
    """Verify latency overhead ≤ 5%"""
    # Measure baseline latency (no instrumentation)
    baseline_latencies = []
    for _ in range(1000):
        start = time.time()
        execute_test_workload()
        baseline_latencies.append(time.time() - start)
    baseline_median = statistics.median(baseline_latencies)
    
    # Measure instrumented latency
    agent = CellAgent()
    instrumented_latencies = []
    for _ in range(1000):
        start = time.time()
        agent.instrument_and_call(execute_test_workload)
        instrumented_latencies.append(time.time() - start)
    instrumented_median = statistics.median(instrumented_latencies)
    
    # Verify: Overhead ≤ 5%
    overhead = (instrumented_median - baseline_median) / baseline_median
    assert overhead <= 0.05
```

### Problem 7: Data Privacy and Leakage

**Description**: PII or sensitive data leaked through telemetry

**Probability**: Low (with proper redaction)

**Impact**: Critical (regulatory violations, legal liability)

**Mitigations**:
1. **Redaction at Source**: CellAgent redacts PII before transmission
2. **Hash-Only Storage**: Only SHA-256 hashes stored, not raw data
3. **Configurable Privacy Policies**: Per-jurisdiction redaction rules
4. **Encryption**: mTLS in transit, AES-256 at rest
5. **Local-Only Mode**: Option to prevent all network transmission
6. **Audit Trail**: All data access logged

**Test Case**:
```python
def test_pii_redaction():
    """Verify PII is redacted from telemetry"""
    # Create event with PII
    event = TelemetryEvent(
        function_name="process_payment",
        args_metadata={
            "email": "user@example.com",
            "phone": "555-1234",
            "cc_number": "4111-1111-1111-1111",
            "ssn": "123-45-6789"
        }
    )
    
    # Redact PII
    agent = CellAgent()
    redacted = agent.redact_pii(event)
    
    # Verify: All PII redacted
    assert "user@example.com" not in str(redacted)
    assert "555-1234" not in str(redacted)
    assert "4111-1111-1111-1111" not in str(redacted)
    assert "123-45-6789" not in str(redacted)
    
    # Verify: Redaction tokens present
    assert "[EMAIL_REDACTED]" in str(redacted)
    assert "[PHONE_REDACTED]" in str(redacted)
    assert "[CC_REDACTED]" in str(redacted)
    assert "[ID_REDACTED]" in str(redacted)
```

### Problem 8: Dependency Supply Chain Risk

**Description**: Vulnerable or malicious dependencies introduced

**Probability**: Medium (supply chain attacks increasing)

**Impact**: High (compromised security system)

**Mitigations**:
1. **Pinned Dependencies**: requirements.txt with cryptographic hashes
2. **SBOM Generation**: CycloneDX SBOM for all builds
3. **Automated Scanning**: Dependabot + Snyk in CI pipeline
4. **Build Failure on Critical CVEs**: CI fails for critical vulnerabilities
5. **Regular Updates**: Monthly dependency review and updates

**Test Case**:
```python
def test_vulnerable_dependency_rejection():
    """Verify CI rejects builds with critical vulnerabilities"""
    # Create requirements.txt with known vulnerable package
    with open("requirements.txt", "w") as f:
        f.write("requests==2.6.0\n")  # Known CVE
    
    # Run CI pipeline
    result = run_ci_pipeline()
    
    # Verify: Build failed
    assert result.status == "failed"
    assert "critical vulnerability" in result.error_message
```

### Problem 9: Usability and Operator Error

**Description**: Operators make mistakes due to complex UI or unclear guidance

**Probability**: Medium (human error inevitable)

**Impact**: Medium (false positives, missed threats)

**Mitigations**:
1. **Clear UI**: Intuitive Admin Console with explainability traces
2. **Safety Defaults**: Conservative thresholds, fail-safe to observe
3. **Staging Deployment**: Recommend testing in staging first
4. **Audit Trails**: All decisions logged with operator identity
5. **Rollback Capability**: Easy rollback for mistakes
6. **Training Materials**: Documentation, tutorials, runbooks

**Test Case**:
```python
def test_operator_error_recovery():
    """Verify operator can recover from accidental promotion"""
    # Setup: Operator accidentally promotes bad detector
    console = AdminConsole()
    bad_detector = create_bad_detector()
    console.promote_candidate(bad_detector.id, operator="test_user")
    
    # Verify: Detector active
    assert sentinel.is_detector_active(bad_detector.id)
    
    # Operator realizes mistake and rolls back
    console.rollback_detector(bad_detector.id, operator="test_user")
    
    # Verify: Detector deactivated
    assert not sentinel.is_detector_active(bad_detector.id)
    
    # Verify: Audit trail complete
    audit_entries = audit_store.get_entries(detector_id=bad_detector.id)
    assert len(audit_entries) == 2  # Promote + rollback
    assert audit_entries[0].action == "promote"
    assert audit_entries[1].action == "rollback"
```

### Problem 10: Attacker Adaptive Countermeasures

**Description**: Attacker learns PIC's detection patterns and evades

**Probability**: Medium (sophisticated attackers)

**Impact**: High (detection evasion)

**Mitigations**:
1. **Periodic Red-Team Exercises**: Quarterly testing with evolving attacks
2. **Ensemble Learning**: Multiple detection algorithms harder to evade
3. **Anomaly Threshold Auto-Tuning**: Thresholds adapt to new patterns
4. **Community Disclosure Program**: Responsible disclosure for evasion techniques
5. **Continuous Improvement**: Regular updates based on threat intelligence

**Test Case**:
```python
def test_adaptive_retraining():
    """Verify system adapts to new attack patterns"""
    # Setup: Initial baseline
    agent = CellAgent()
    sentinel = SentinelBrain()
    establish_baseline()
    
    # Simulate adaptive attacker (gradually changing behavior)
    for iteration in range(10):
        attack_variant = generate_adaptive_attack(iteration)
        result = agent.instrument_and_call(attack_variant)
        
        # Early iterations: detected
        if iteration < 5:
            assert result.anomaly_score > 80
        
        # Trigger retraining
        if iteration == 5:
            sentinel.retrain_baselines()
        
        # Later iterations: still detected after retraining
        if iteration >= 5:
            assert result.anomaly_score > 80
```

## Roadmap

### v1.0 (Current Scope)

**Core Features**:
- In-process Python instrumentation (CellAgent)
- Local behavioral anomaly detection (SentinelBrain)
- Sandboxed candidate validation
- Human-in-loop promotion workflow
- Safe remediation actions (allow/quarantine/block)
- Local Memory Bank (SQLite)
- Web-based Admin Console
- Immutable audit logging
- Watchdog integrity monitoring

**Deployment**:
- Pip package distribution
- Container image (Docker)
- Documentation and demos
- CI/CD pipeline

**Target Users**:
- Developer workstations
- Small to medium deployments
- Research and evaluation

### v1.1 (Near-term Enhancements)

**Features**:
- PostgreSQL Memory Bank support
- Prometheus metrics export
- PagerDuty/Slack alerting
- Enhanced explainability visualizations
- Performance dashboard
- Automated canary deployment

**Improvements**:
- Reduced latency overhead (<3%)
- Faster baseline convergence
- Improved polymorphic detection

### v2.0 (Future)

**Features**:
- LD_PRELOAD instrumentation (C/C++ applications)
- Kernel-level syscall monitoring (eBPF)
- Cross-host memory bank with signed exchange
- Federated learning for detection models
- Hardware attestation (TPM integration)
- WASM agent for browser-side monitoring

**Deployment**:
- Multi-tenant SaaS offering
- Enterprise support tier
- Managed memory bank service

### v3.0 (Long-term Vision)

**Features**:
- Certified secure agent (Common Criteria EAL4+)
- Vendor partnerships (cloud providers, security vendors)
- Industry-standard signature exchange protocol
- AI-powered threat hunting
- Automated incident response orchestration

**Ecosystem**:
- Community signature marketplace
- Third-party detector plugins
- Integration with SIEM/SOAR platforms

