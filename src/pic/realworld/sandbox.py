"""Sandbox Manager for Test Isolation

Provides isolated environments for running real-world tests safely.
"""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
from contextlib import contextmanager
import logging

from pic.realworld.safety import SafetyController


class SandboxManager:
    """Manages isolated sandbox environments for testing.
    
    Creates temporary, isolated directories for test execution with
    automatic cleanup and safety enforcement.
    """
    
    def __init__(self, base_path: Optional[Path] = None, safety_controller: Optional[SafetyController] = None):
        """Initialize sandbox manager.
        
        Args:
            base_path: Base directory for sandboxes (default: system temp)
            safety_controller: Safety controller for enforcement
        """
        self.base_path = Path(base_path) if base_path else Path(tempfile.gettempdir()) / "pic_realworld_tests"
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        self.safety_controller = safety_controller or SafetyController(self.base_path)
        self.logger = logging.getLogger(__name__)
        
        self.active_sandboxes: Dict[str, Path] = {}
        
        self.logger.info(f"SandboxManager initialized at {self.base_path}")
    
    def create_sandbox(self, name: str) -> Path:
        """Create a new isolated sandbox directory.
        
        Args:
            name: Name for the sandbox
            
        Returns:
            Path to the sandbox directory
        """
        sandbox_path = self.base_path / name
        sandbox_path.mkdir(parents=True, exist_ok=True)
        
        # Create standard subdirectories
        (sandbox_path / "data").mkdir(exist_ok=True)
        (sandbox_path / "logs").mkdir(exist_ok=True)
        (sandbox_path / "temp").mkdir(exist_ok=True)
        
        self.active_sandboxes[name] = sandbox_path
        self.logger.info(f"Created sandbox: {name} at {sandbox_path}")
        
        return sandbox_path
    
    def get_sandbox(self, name: str) -> Optional[Path]:
        """Get path to an existing sandbox.
        
        Args:
            name: Name of the sandbox
            
        Returns:
            Path to sandbox or None if not found
        """
        return self.active_sandboxes.get(name)
    
    def cleanup_sandbox(self, name: str) -> None:
        """Clean up and remove a sandbox.
        
        Args:
            name: Name of the sandbox to clean up
        """
        sandbox_path = self.active_sandboxes.get(name)
        if not sandbox_path:
            self.logger.warning(f"Sandbox not found: {name}")
            return
        
        try:
            if sandbox_path.exists():
                shutil.rmtree(sandbox_path)
                self.logger.info(f"Cleaned up sandbox: {name}")
            
            del self.active_sandboxes[name]
            
        except Exception as e:
            self.logger.error(f"Error cleaning up sandbox {name}: {e}")
    
    def cleanup_all_sandboxes(self) -> None:
        """Clean up all active sandboxes."""
        sandbox_names = list(self.active_sandboxes.keys())
        for name in sandbox_names:
            self.cleanup_sandbox(name)
        
        self.logger.info("All sandboxes cleaned up")
    
    @contextmanager
    def temporary_sandbox(self, name: str):
        """Context manager for temporary sandbox that auto-cleans.
        
        Args:
            name: Name for the sandbox
            
        Yields:
            Path to the sandbox directory
        """
        sandbox_path = self.create_sandbox(name)
        try:
            yield sandbox_path
        finally:
            self.cleanup_sandbox(name)
    
    def validate_path(self, path: Path) -> bool:
        """Validate that a path is within a sandbox.
        
        Args:
            path: Path to validate
            
        Returns:
            True if path is within a sandbox, False otherwise
        """
        resolved_path = Path(path).resolve()
        
        # Check if path is within any active sandbox
        for sandbox_path in self.active_sandboxes.values():
            if str(resolved_path).startswith(str(sandbox_path)):
                return True
        
        # Also check if within base path
        if str(resolved_path).startswith(str(self.base_path)):
            return True
        
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get sandbox statistics.
        
        Returns:
            Dictionary with sandbox stats
        """
        total_size = 0
        file_count = 0
        
        for sandbox_path in self.active_sandboxes.values():
            if sandbox_path.exists():
                for item in sandbox_path.rglob("*"):
                    if item.is_file():
                        file_count += 1
                        total_size += item.stat().st_size
        
        return {
            "active_sandboxes": len(self.active_sandboxes),
            "total_files": file_count,
            "total_size_bytes": total_size,
            "base_path": str(self.base_path)
        }
