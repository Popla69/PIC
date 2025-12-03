"""StateStore - SQLite storage for baselines and detectors."""

import sqlite3
import json
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from pic.models.baseline import BaselineProfile
from pic.models.detector import Detector


class StateStore:
    """Persistent storage for baseline profiles and detectors using SQLite.
    
    Features:
    - WAL (Write-Ahead Logging) mode for better concurrency
    - Baseline profile versioning
    - Detector TTL management
    - Atomic transactions
    """
    
    def __init__(self, db_path: str):
        """Initialize StateStore with database path.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.conn: Optional[sqlite3.Connection] = None
        self._connect()
        self._init_schema()
    
    def _connect(self) -> None:
        """Establish database connection with WAL mode."""
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        # Enable WAL mode for better concurrency
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.commit()
    
    def _init_schema(self) -> None:
        """Initialize database schema."""
        if self.conn is None:
            raise RuntimeError("Database connection not established")
        
        # Baselines table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS baselines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                function_name TEXT NOT NULL,
                module_name TEXT NOT NULL,
                version INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                sample_count INTEGER NOT NULL,
                mean_duration_ms REAL NOT NULL,
                std_duration_ms REAL NOT NULL,
                p50_duration_ms REAL NOT NULL,
                p95_duration_ms REAL NOT NULL,
                p99_duration_ms REAL NOT NULL,
                profile_json TEXT NOT NULL,
                UNIQUE(function_name, module_name, version)
            )
        """)
        
        # Detectors table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS detectors (
                id TEXT PRIMARY KEY,
                function_name TEXT NOT NULL,
                threshold REAL NOT NULL,
                signature_hash TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL,
                expires_at TEXT,
                is_active INTEGER NOT NULL DEFAULT 1
            )
        """)
        
        # Create indexes for performance
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_baselines_function 
            ON baselines(function_name, module_name)
        """)
        
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_detectors_function 
            ON detectors(function_name, is_active)
        """)
        
        self.conn.commit()
    
    def store_baseline(self, baseline: BaselineProfile) -> None:
        """Store or update baseline profile.
        
        Args:
            baseline: BaselineProfile to store
        """
        if self.conn is None:
            raise RuntimeError("Database connection not established")
        
        profile_json = json.dumps({
            "historical_distances": baseline.historical_distances
        })
        
        self.conn.execute("""
            INSERT OR REPLACE INTO baselines (
                function_name, module_name, version, created_at, updated_at,
                sample_count, mean_duration_ms, std_duration_ms,
                p50_duration_ms, p95_duration_ms, p99_duration_ms, profile_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            baseline.function_name,
            baseline.module_name,
            baseline.version,
            baseline.created_at.isoformat(),
            baseline.updated_at.isoformat(),
            baseline.sample_count,
            baseline.mean_duration_ms,
            baseline.std_duration_ms,
            baseline.p50_duration_ms,
            baseline.p95_duration_ms,
            baseline.p99_duration_ms,
            profile_json
        ))
        
        self.conn.commit()
    
    def get_baseline(self, function_name: str, module_name: str) -> Optional[BaselineProfile]:
        """Retrieve latest baseline profile for a function.
        
        Args:
            function_name: Name of the function
            module_name: Module containing the function
            
        Returns:
            BaselineProfile if found, None otherwise
        """
        if self.conn is None:
            raise RuntimeError("Database connection not established")
        
        cursor = self.conn.execute("""
            SELECT * FROM baselines
            WHERE function_name = ? AND module_name = ?
            ORDER BY version DESC
            LIMIT 1
        """, (function_name, module_name))
        
        row = cursor.fetchone()
        if row is None:
            return None
        
        profile_data = json.loads(row["profile_json"])
        
        return BaselineProfile(
            function_name=row["function_name"],
            module_name=row["module_name"],
            version=row["version"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            sample_count=row["sample_count"],
            mean_duration_ms=row["mean_duration_ms"],
            std_duration_ms=row["std_duration_ms"],
            p50_duration_ms=row["p50_duration_ms"],
            p95_duration_ms=row["p95_duration_ms"],
            p99_duration_ms=row["p99_duration_ms"],
            historical_distances=profile_data["historical_distances"]
        )
    
    def store_detector(self, detector: Detector) -> None:
        """Store detector.
        
        Args:
            detector: Detector to store
        """
        if self.conn is None:
            raise RuntimeError("Database connection not established")
        
        expires_at = detector.expires_at.isoformat() if detector.expires_at else None
        
        self.conn.execute("""
            INSERT OR REPLACE INTO detectors (
                id, function_name, threshold, signature_hash,
                created_at, expires_at, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            detector.id,
            detector.function_name,
            detector.threshold,
            detector.signature_hash,
            detector.created_at.isoformat(),
            expires_at,
            1 if detector.is_active else 0
        ))
        
        self.conn.commit()
    
    def get_active_detectors(self, function_name: str) -> List[Detector]:
        """Get active detectors for a function.
        
        Args:
            function_name: Name of the function
            
        Returns:
            List of active Detector instances
        """
        if self.conn is None:
            raise RuntimeError("Database connection not established")
        
        cursor = self.conn.execute("""
            SELECT * FROM detectors
            WHERE function_name = ? AND is_active = 1
        """, (function_name,))
        
        detectors = []
        for row in cursor.fetchall():
            expires_at = None
            if row["expires_at"]:
                expires_at = datetime.fromisoformat(row["expires_at"])
            
            detector = Detector(
                id=row["id"],
                function_name=row["function_name"],
                threshold=row["threshold"],
                signature_hash=row["signature_hash"],
                created_at=datetime.fromisoformat(row["created_at"]),
                expires_at=expires_at,
                is_active=bool(row["is_active"])
            )
            detectors.append(detector)
        
        return detectors
    
    def expire_old_detectors(self) -> int:
        """Expire detectors past their TTL.
        
        Returns:
            Number of detectors expired
        """
        if self.conn is None:
            raise RuntimeError("Database connection not established")
        
        now = datetime.now().isoformat()
        
        cursor = self.conn.execute("""
            UPDATE detectors
            SET is_active = 0
            WHERE expires_at IS NOT NULL AND expires_at <= ? AND is_active = 1
        """, (now,))
        
        self.conn.commit()
        return cursor.rowcount
    
    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def __enter__(self) -> "StateStore":
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()
