"""BrainCore - Main event processing pipeline."""

import random
from datetime import datetime
from pic.models.events import TelemetryEvent, AuditEvent
from pic.models.decision import Decision
from pic.models.integration import SignedEvent
from pic.storage.state_store import StateStore
from pic.storage.audit_store import AuditStore
from pic.storage.trace_store import TraceStore
from pic.brain.profiler import BaselineProfiler
from pic.brain.detector import AnomalyDetector
from pic.brain.normalizer import FeatureNormalizer
from pic.brain.security_validator import SecurityValidator
from pic.brain.pattern_cache import PatternMemoryCache
from pic.effector.executor import Effector
from pic.crypto import CryptoCore


class BrainCore:
    """Core event processing pipeline with adaptive tuning."""
    
    def __init__(
        self,
        state_store: StateStore,
        audit_store: AuditStore,
        trace_store: TraceStore,
        crypto_core: CryptoCore,
        # Tuning parameters
        anomaly_threshold: float = 65.0,  # Lowered from 95.0
        soft_allow_probability: float = 0.15,
        enable_pattern_cache: bool = True
    ):
        """Initialize BrainCore with tuning parameters.
        
        Args:
            state_store: StateStore instance
            audit_store: AuditStore instance
            trace_store: TraceStore instance
            crypto_core: CryptoCore instance
            anomaly_threshold: Anomaly detection threshold (0-100, default: 65)
            soft_allow_probability: Probability of allowing borderline events (0-1, default: 0.15)
            enable_pattern_cache: Enable pattern memory cache (default: True)
        """
        self.state_store = state_store
        self.audit_store = audit_store
        self.trace_store = trace_store
        self.crypto_core = crypto_core
        
        # Initialize components with tuned parameters
        self.profiler = BaselineProfiler()
        self.detector = AnomalyDetector(
            threshold_percentile=anomaly_threshold,
            candidate_score_threshold=anomaly_threshold
        )
        self.normalizer = FeatureNormalizer()
        self.effector = Effector()
        self.security_validator = SecurityValidator(crypto_core)
        
        # Pattern memory cache for fast legitimate recognition
        self.pattern_cache = PatternMemoryCache() if enable_pattern_cache else None
        
        # Tuning parameters
        self.anomaly_threshold = anomaly_threshold
        self.soft_allow_probability = soft_allow_probability
        # Soft-allow zone is BELOW the main threshold (for borderline normal cases)
        self.soft_allow_threshold_low = max(anomaly_threshold - 10.0, 0.0)
        self.soft_allow_threshold_high = anomaly_threshold
        
        self._events_processed = 0
        self._maintenance_interval = 100
        self._security_violations = 0
        self._soft_allows = 0
        self._cache_hits = 0
    
    def process_signed_event(self, signed_event: SignedEvent) -> Decision:
        """Process signed telemetry event with security validation.
        
        Args:
            signed_event: SignedEvent to process
            
        Returns:
            Decision (allow or block)
        """
        # Verify signature and check for replay attacks
        is_valid, reason = self.security_validator.verify_event(signed_event)
        
        if not is_valid:
            self._security_violations += 1
            self._log_security_alert(signed_event, reason)
            return Decision.block(f"Security violation: {reason}", anomaly_score=1.0)
        
        # Process the underlying event
        return self.process_event(signed_event.event)
    
    def process_event(self, event: TelemetryEvent) -> Decision:
        """Process telemetry event through tuned pipeline.
        
        Complete pipeline:
        1. Check pattern cache (fast path for known legitimate patterns)
        2. Store in TraceStore
        3. Check baseline (train if insufficient)
        4. Normalize and detect anomalies
        5. Apply soft-allow logic for borderline cases
        6. Execute action via Effector
        7. Log to AuditStore
        8. Update pattern cache on allow decisions
        
        Args:
            event: TelemetryEvent to process
            
        Returns:
            Decision (allow or block)
        """
        # Step 1: Fast path - check pattern cache
        if self.pattern_cache and self.pattern_cache.check_match(event):
            self._cache_hits += 1
            decision = Decision.allow("Known legitimate pattern (cached)", 0.0)
            self._log_decision(event, decision, "cache_hit")
            return decision
        
        # Step 2: Store in trace buffer
        self.trace_store.add_event(event)
        
        # Step 3: Get baseline
        baseline = self.state_store.get_baseline(event.function_name, event.module_name)
        
        if baseline is None or not baseline.is_sufficient():
            # Training mode: collect samples
            self.profiler.add_sample(event)
            
            # Check if we have enough samples to compute baseline
            if self.profiler.get_sample_count(event.function_name, event.module_name) >= self.profiler.min_samples:
                # Compute and store baseline
                new_baseline = self.profiler.compute_baseline(event.function_name, event.module_name)
                if new_baseline:
                    self.state_store.store_baseline(new_baseline)
            
            decision = Decision.allow("Training mode")
            self._log_decision(event, decision, "training")
            
            # Add to pattern cache during training
            if self.pattern_cache:
                self.pattern_cache.add_pattern(event)
            
            return decision
        
        # Step 4: Normalize and detect anomalies
        score = self.detector.compute_anomaly_score(event, baseline)
        
        # Step 5: Make decision with soft-allow logic
        # Note: Higher score = more anomalous (percentile ranking)
        if score < self.soft_allow_threshold_low:
            # Clear allow - well below threshold (normal behavior)
            decision = Decision.allow("Normal behavior", score)
            
            # Add to pattern cache
            if self.pattern_cache:
                self.pattern_cache.add_pattern(event)
                
        elif score < self.soft_allow_threshold_high:
            # Soft-allow zone - borderline case (between threshold-10 and threshold)
            # Randomly allow some borderline events for adaptive learning
            if random.random() < self.soft_allow_probability:
                self._soft_allows += 1
                decision = Decision.allow(f"Soft-allow (borderline, score={score:.1f})", score)
                self._log_decision(event, decision, "soft_allow")
                
                # Add to pattern cache on soft-allow
                if self.pattern_cache:
                    self.pattern_cache.add_pattern(event)
            else:
                decision = Decision.block(f"Borderline anomaly (score={score:.1f})", score)
        else:
            # Clear block - above threshold (anomalous)
            decision = Decision.block("Anomaly detected", score)
        
        # Step 6: Execute action via Effector
        self.effector.execute_action(decision)
        
        # Step 7: Log to AuditStore
        self._log_decision(event, decision, "detection")
        
        # Periodic maintenance
        self._events_processed += 1
        if self._events_processed % self._maintenance_interval == 0:
            self._perform_maintenance()
        
        return decision
    
    def _log_decision(self, event: TelemetryEvent, decision: Decision, event_type: str) -> None:
        """Log decision to audit store.
        
        Args:
            event: TelemetryEvent that was processed
            decision: Decision that was made
            event_type: Type of event (training, detection, etc.)
        """
        audit_event = AuditEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            actor="system",
            action=decision.action,
            result="success",
            signature=""  # Will be set by AuditStore
        )
        self.audit_store.log_event(audit_event)
    
    def _log_security_alert(self, signed_event: SignedEvent, reason: str) -> None:
        """Log security violation to audit store.
        
        Args:
            signed_event: SignedEvent that failed validation
            reason: Reason for security violation
        """
        audit_event = AuditEvent(
            timestamp=datetime.now(),
            event_type="security_violation",
            actor="security_validator",
            action="block",
            result=reason,
            signature=""  # Will be set by AuditStore
        )
        self.audit_store.log_event(audit_event)
    
    def _perform_maintenance(self) -> None:
        """Perform periodic maintenance tasks.
        
        Tasks:
        - Check for baseline retraining
        - Check for detector expiration
        - Evict expired patterns from cache
        """
        # Expire old detectors
        self.state_store.expire_old_detectors()
        
        # Evict expired patterns from cache
        if self.pattern_cache:
            self.pattern_cache.evict_expired()
        
        # TODO: Add baseline retraining logic
        # This would check if baselines need updating based on drift
    
    def get_stats(self) -> dict:
        """Get processing statistics.
        
        Returns:
            Dictionary with statistics
        """
        stats = {
            "events_processed": self._events_processed,
            "security_violations": self._security_violations,
            "soft_allows": self._soft_allows,
            "cache_hits": self._cache_hits,
            "tuning": {
                "anomaly_threshold": self.anomaly_threshold,
                "soft_allow_probability": self.soft_allow_probability,
                "soft_allow_threshold_low": self.soft_allow_threshold_low,
                "soft_allow_threshold_high": self.soft_allow_threshold_high
            },
            "security_validator_stats": self.security_validator.get_stats(),
            "effector_stats": self.effector.get_stats(),
            "trace_store_size": self.trace_store._total_events
        }
        
        if self.pattern_cache:
            stats["pattern_cache_stats"] = self.pattern_cache.get_stats()
        
        return stats
