"""IntegratedPIC - Unified API for PIC with Brain-CellAgent integration."""

import logging
from typing import Optional
from pathlib import Path

from pic.config import PICConfig
from pic.crypto import CryptoCore
from pic.brain.core import BrainCore
from pic.cellagent.agent import CellAgent
from pic.cellagent.brain_connector import BrainConnector
from pic.storage.state_store import StateStore
from pic.storage.audit_store import AuditStore
from pic.storage.trace_store import TraceStore


class IntegratedPIC:
    """Integrated PIC system with CellAgent and BrainCore.
    
    Provides unified initialization and lifecycle management for the complete
    PIC system including telemetry collection, anomaly detection, and automated response.
    
    Example:
        >>> pic = IntegratedPIC()
        >>> pic.start()
        >>> 
        >>> @pic.agent.monitor
        >>> def process_payment(amount):
        >>>     return {"status": "success"}
        >>> 
        >>> pic.stop()
    """
    
    def __init__(
        self, 
        config: Optional[PICConfig] = None, 
        data_dir: str = "pic_data",
        # Tuning parameters
        anomaly_threshold: float = 98.0,  # FIXED: Raised from 65 to 98 (less aggressive)
        soft_allow_probability: float = 0.15,
        enable_pattern_cache: bool = True
    ):
        """Initialize IntegratedPIC with tuning parameters.
        
        Args:
            config: PICConfig instance (loads default if None)
            data_dir: Directory for storing PIC data
            anomaly_threshold: Anomaly detection threshold percentile (0-100, default: 98)
                              Higher = less aggressive (only block extreme outliers)
            soft_allow_probability: Probability of allowing borderline events (0-1, default: 0.15)
            enable_pattern_cache: Enable pattern memory cache (default: True)
        """
        self.config = config or PICConfig.load()
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing IntegratedPIC with tuning...")
        self.logger.info(f"  Anomaly threshold: {anomaly_threshold}")
        self.logger.info(f"  Soft-allow probability: {soft_allow_probability}")
        self.logger.info(f"  Pattern cache: {'enabled' if enable_pattern_cache else 'disabled'}")
        
        # Initialize crypto
        key_path = self.data_dir / "signing.key"
        self.crypto = CryptoCore(key_path=str(key_path))
        self.logger.info("✓ CryptoCore initialized")
        
        # Initialize storage
        self.state_store = StateStore(db_path=str(self.data_dir / "state.db"))
        self.audit_store = AuditStore(
            log_path=str(self.data_dir / "audit.log"),
            crypto_core=self.crypto
        )
        self.trace_store = TraceStore(
            capacity_per_function=self.config.get("trace.capacity_per_function", 1000)
        )
        self.logger.info("✓ Storage initialized")
        
        # Initialize BrainCore with tuning parameters
        self.brain = BrainCore(
            state_store=self.state_store,
            audit_store=self.audit_store,
            trace_store=self.trace_store,
            crypto_core=self.crypto,
            anomaly_threshold=anomaly_threshold,
            soft_allow_probability=soft_allow_probability,
            enable_pattern_cache=enable_pattern_cache
        )
        self.logger.info("✓ BrainCore initialized with tuning")
        
        # Initialize CellAgent
        self.agent = CellAgent(config=self.config)
        self.logger.info("✓ CellAgent initialized")
        
        # Create Brain connector
        self.connector = BrainConnector(self.brain, self.crypto, self.config)
        self.logger.info("✓ BrainConnector initialized")
        
        # Connect Agent to Brain
        self.agent.set_brain_connector(self.connector)
        self.logger.info("✓ Agent connected to Brain")
        
        self._running = False
        
        self.logger.info("IntegratedPIC initialization complete!")
    
    def start(self) -> None:
        """Start all components."""
        if self._running:
            self.logger.warning("IntegratedPIC already running")
            return
        
        self.logger.info("Starting IntegratedPIC...")
        self.agent.start()
        self._running = True
        self.logger.info("✓ IntegratedPIC started")
    
    def stop(self) -> None:
        """Stop all components gracefully."""
        if not self._running:
            self.logger.warning("IntegratedPIC not running")
            return
        
        self.logger.info("Stopping IntegratedPIC...")
        self.agent.stop()
        self._running = False
        self.logger.info("✓ IntegratedPIC stopped")
    
    def get_stats(self) -> dict:
        """Get system statistics.
        
        Returns:
            Dictionary with comprehensive statistics
        """
        return {
            "running": self._running,
            "agent_stats": self.agent.get_stats(),
            "brain_stats": self.agent.get_brain_stats(),
            "brain_core_stats": self.brain.get_stats(),
            "trace_store_events": self.trace_store._total_events
        }
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False
