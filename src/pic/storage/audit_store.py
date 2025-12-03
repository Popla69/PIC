"""AuditStore - Append-only immutable log storage with HMAC signing."""

import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from pic.models.events import AuditEvent
from pic.crypto import CryptoCore


class AuditStore:
    """Append-only storage for audit logs with HMAC signing.
    
    Features:
    - Append-only (no modification or deletion)
    - HMAC-SHA256 signature for each entry
    - JSON Lines format (one JSON object per line)
    - Integrity verification
    - Forensic export capability
    """
    
    def __init__(self, log_path: str, crypto_core: CryptoCore):
        """Initialize AuditStore.
        
        Args:
            log_path: Path to audit log file
            crypto_core: CryptoCore instance for signing
        """
        self.log_path = Path(log_path)
        self.crypto_core = crypto_core
        
        # Ensure directory exists
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create file if it doesn't exist
        if not self.log_path.exists():
            self.log_path.touch(mode=0o600)  # Owner read/write only
    
    def log_event(self, event: AuditEvent) -> None:
        """Append signed event to log.
        
        Args:
            event: AuditEvent to log
        """
        # Get signable data (without signature field)
        signable_data = event.get_signable_data()
        
        # Generate signature
        signature = self.crypto_core.hmac_sign(signable_data)
        
        # Update event with signature
        event.signature = signature
        
        # Append to log file (JSON Lines format)
        with open(self.log_path, "a") as f:
            f.write(event.to_json() + "\n")
    
    def verify_log_integrity(self) -> bool:
        """Verify all log entries have valid signatures.
        
        Returns:
            True if all signatures are valid, False otherwise
        """
        if not self.log_path.exists():
            return True  # Empty log is valid
        
        with open(self.log_path, "r") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    # Parse event
                    event = AuditEvent.from_json(line)
                    
                    # Get signable data
                    signable_data = event.get_signable_data()
                    
                    # Verify signature
                    if not self.crypto_core.verify_signature(signable_data, event.signature):
                        print(f"Invalid signature at line {line_num}")
                        return False
                        
                except Exception as e:
                    print(f"Error verifying line {line_num}: {e}")
                    return False
        
        return True
    
    def export_logs(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[AuditEvent]:
        """Export logs for forensic analysis.
        
        Args:
            start_time: Start of time range (inclusive)
            end_time: End of time range (inclusive)
            
        Returns:
            List of AuditEvent instances
        """
        events = []
        
        if not self.log_path.exists():
            return events
        
        with open(self.log_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    event = AuditEvent.from_json(line)
                    
                    # Filter by time range
                    if start_time and event.timestamp < start_time:
                        continue
                    if end_time and event.timestamp > end_time:
                        continue
                    
                    events.append(event)
                    
                except Exception as e:
                    print(f"Error parsing log entry: {e}")
                    continue
        
        return events
    
    def get_event_count(self) -> int:
        """Get total number of events in log.
        
        Returns:
            Number of log entries
        """
        if not self.log_path.exists():
            return 0
        
        count = 0
        with open(self.log_path, "r") as f:
            for line in f:
                if line.strip():
                    count += 1
        
        return count
    
    def get_latest_events(self, count: int = 100) -> List[AuditEvent]:
        """Get latest N events from log.
        
        Args:
            count: Number of events to retrieve
            
        Returns:
            List of latest AuditEvent instances
        """
        if not self.log_path.exists():
            return []
        
        # Read all lines
        with open(self.log_path, "r") as f:
            lines = [line.strip() for line in f if line.strip()]
        
        # Get last N lines
        latest_lines = lines[-count:] if len(lines) > count else lines
        
        # Parse events
        events = []
        for line in latest_lines:
            try:
                event = AuditEvent.from_json(line)
                events.append(event)
            except Exception as e:
                print(f"Error parsing log entry: {e}")
                continue
        
        return events
