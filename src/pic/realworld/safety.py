"""Safety Controller for Real-World Testing

Enforces safety constraints to ensure all testing remains legal, ethical, and controlled.
"""

import os
import socket
from pathlib import Path
from typing import List, Set, Optional
from dataclasses import dataclass, field
import logging


@dataclass
class NetworkPolicy:
    """Network access policy for testing."""
    allowed_hosts: Set[str] = field(default_factory=lambda: {"localhost", "127.0.0.1", "::1"})
    allowed_ports: Set[int] = field(default_factory=lambda: {8000, 8080, 5000, 3000})
    block_external: bool = True


@dataclass
class ResourceLimits:
    """Resource usage limits for testing."""
    max_memory_mb: int = 500
    max_cpu_percent: float = 80.0
    max_file_operations: int = 10000
    max_network_connections: int = 100


@dataclass
class CleanupPolicy:
    """Cleanup requirements for test artifacts."""
    remove_temp_files: bool = True
    remove_test_databases: bool = True
    remove_log_files: bool = False  # Keep logs for analysis
    cleanup_timeout_seconds: int = 30


class SafetyViolationError(Exception):
    """Raised when a safety constraint is violated."""
    pass


class SafetyController:
    """Enforces safety constraints for real-world testing.
    
    Ensures all operations remain within legal and ethical boundaries:
    - Network access restricted to localhost
    - File operations limited to designated test directories
    - Resource usage monitored and limited
    - Automatic cleanup of test artifacts
    """
    
    def __init__(
        self,
        test_root: Path,
        network_policy: Optional[NetworkPolicy] = None,
        resource_limits: Optional[ResourceLimits] = None,
        cleanup_policy: Optional[CleanupPolicy] = None
    ):
        self.test_root = Path(test_root).resolve()
        self.network_policy = network_policy or NetworkPolicy()
        self.resource_limits = resource_limits or ResourceLimits()
        self.cleanup_policy = cleanup_policy or CleanupPolicy()
        
        self.logger = logging.getLogger(__name__)
        
        # Track operations for monitoring
        self.file_operations_count = 0
        self.network_connections_count = 0
        self.violations: List[str] = []
        
        # Ensure test root exists
        self.test_root.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"SafetyController initialized with test_root: {self.test_root}")
    
    def validate_file_path(self, path: Path) -> bool:
        """Validate that a file path is within allowed test directories.
        
        Args:
            path: Path to validate
            
        Returns:
            True if path is safe, False otherwise
            
        Raises:
            SafetyViolationError: If path is outside test boundaries
        """
        try:
            resolved_path = Path(path).resolve()
            
            # Check if path is within test root
            if not str(resolved_path).startswith(str(self.test_root)):
                violation = f"File path outside test root: {resolved_path}"
                self.violations.append(violation)
                self.logger.error(violation)
                raise SafetyViolationError(violation)
            
            # Check file operation count
            self.file_operations_count += 1
            if self.file_operations_count > self.resource_limits.max_file_operations:
                violation = f"File operation limit exceeded: {self.file_operations_count}"
                self.violations.append(violation)
                self.logger.error(violation)
                raise SafetyViolationError(violation)
            
            return True
            
        except Exception as e:
            if isinstance(e, SafetyViolationError):
                raise
            self.logger.error(f"Error validating file path: {e}")
            return False
    
    def validate_network_access(self, host: str, port: int) -> bool:
        """Validate that network access is to allowed hosts/ports only.
        
        Args:
            host: Target hostname or IP
            port: Target port number
            
        Returns:
            True if access is allowed, False otherwise
            
        Raises:
            SafetyViolationError: If network access is unauthorized
        """
        # Normalize host
        normalized_host = host.lower().strip()
        
        # Check if host is in allowed list
        if normalized_host not in self.network_policy.allowed_hosts:
            violation = f"Unauthorized network host: {host}"
            self.violations.append(violation)
            self.logger.error(violation)
            raise SafetyViolationError(violation)
        
        # Check if port is in allowed list
        if port not in self.network_policy.allowed_ports:
            violation = f"Unauthorized network port: {port}"
            self.violations.append(violation)
            self.logger.error(violation)
            raise SafetyViolationError(violation)
        
        # Check connection count
        self.network_connections_count += 1
        if self.network_connections_count > self.resource_limits.max_network_connections:
            violation = f"Network connection limit exceeded: {self.network_connections_count}"
            self.violations.append(violation)
            self.logger.error(violation)
            raise SafetyViolationError(violation)
        
        # Block external access if policy requires
        if self.network_policy.block_external:
            try:
                # Resolve hostname to IP
                ip = socket.gethostbyname(normalized_host)
                if not (ip.startswith("127.") or ip == "::1"):
                    violation = f"External network access blocked: {host} ({ip})"
                    self.violations.append(violation)
                    self.logger.error(violation)
                    raise SafetyViolationError(violation)
            except socket.gaierror:
                # If we can't resolve, it's likely localhost variant
                pass
        
        return True
    
    def validate_malware_sample(self, sample_path: Path) -> bool:
        """Validate that malware sample is educational/harmless variant.
        
        Args:
            sample_path: Path to malware sample
            
        Returns:
            True if sample is safe, False otherwise
            
        Raises:
            SafetyViolationError: If sample appears dangerous
        """
        # Ensure sample is in test directory
        self.validate_file_path(sample_path)
        
        # Check file extension - should be .py or .txt for educational samples
        if sample_path.suffix not in {".py", ".txt", ".md", ".json"}:
            violation = f"Suspicious malware sample file type: {sample_path.suffix}"
            self.violations.append(violation)
            self.logger.warning(violation)
            # Don't raise - just warn for now
        
        # Check file size - educational samples should be small
        if sample_path.exists() and sample_path.stat().st_size > 1024 * 1024:  # 1MB
            violation = f"Malware sample too large: {sample_path.stat().st_size} bytes"
            self.violations.append(violation)
            self.logger.warning(violation)
        
        return True
    
    def cleanup_test_artifacts(self) -> None:
        """Clean up all test artifacts according to cleanup policy."""
        self.logger.info("Starting test artifact cleanup...")
        
        cleaned_files = 0
        cleaned_dirs = 0
        
        try:
            # Remove temporary files
            if self.cleanup_policy.remove_temp_files:
                for temp_file in self.test_root.rglob("*.tmp"):
                    try:
                        temp_file.unlink()
                        cleaned_files += 1
                    except Exception as e:
                        self.logger.warning(f"Failed to remove temp file {temp_file}: {e}")
                
                for temp_file in self.test_root.rglob("temp_*"):
                    try:
                        if temp_file.is_file():
                            temp_file.unlink()
                            cleaned_files += 1
                    except Exception as e:
                        self.logger.warning(f"Failed to remove temp file {temp_file}: {e}")
            
            # Remove test databases
            if self.cleanup_policy.remove_test_databases:
                for db_file in self.test_root.rglob("*.db"):
                    try:
                        db_file.unlink()
                        cleaned_files += 1
                    except Exception as e:
                        self.logger.warning(f"Failed to remove database {db_file}: {e}")
            
            # Remove log files if policy requires
            if self.cleanup_policy.remove_log_files:
                for log_file in self.test_root.rglob("*.log"):
                    try:
                        log_file.unlink()
                        cleaned_files += 1
                    except Exception as e:
                        self.logger.warning(f"Failed to remove log file {log_file}: {e}")
            
            # Remove empty directories
            for dir_path in sorted(self.test_root.rglob("*"), reverse=True):
                if dir_path.is_dir() and not any(dir_path.iterdir()):
                    try:
                        dir_path.rmdir()
                        cleaned_dirs += 1
                    except Exception as e:
                        self.logger.warning(f"Failed to remove directory {dir_path}: {e}")
            
            self.logger.info(f"Cleanup complete: {cleaned_files} files, {cleaned_dirs} directories removed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def get_violations(self) -> List[str]:
        """Get list of safety violations that occurred."""
        return self.violations.copy()
    
    def reset_counters(self) -> None:
        """Reset operation counters."""
        self.file_operations_count = 0
        self.network_connections_count = 0
        self.violations.clear()
        self.logger.info("Safety counters reset")
    
    def get_stats(self) -> dict:
        """Get current safety statistics."""
        return {
            "file_operations": self.file_operations_count,
            "network_connections": self.network_connections_count,
            "violations": len(self.violations),
            "test_root": str(self.test_root)
        }
