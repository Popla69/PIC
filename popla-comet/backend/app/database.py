"""Database models and connection management."""

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
import json
import logging

logger = logging.getLogger(__name__)

DATABASE_PATH = Path("data/popla_comet.db")


def init_database():
    """Initialize the database with required tables."""
    DATABASE_PATH.parent.mkdir(exist_ok=True)
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analysis_results (
            id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            status TEXT NOT NULL,
            image_size INTEGER,
            processing_time REAL,
            description TEXT,
            confidence REAL,
            tags TEXT,
            objects_detected TEXT,
            error TEXT,
            user_id TEXT,
            metadata TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE,
            email TEXT,
            created_at TEXT NOT NULL,
            last_active TEXT,
            total_analyses INTEGER DEFAULT 0
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL,
            event_data TEXT,
            user_id TEXT
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_analysis_timestamp 
        ON analysis_results(timestamp)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_analysis_user 
        ON analysis_results(user_id)
    """)
    
    conn.commit()
    conn.close()
    
    logger.info("Database initialized successfully")


@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        conn.close()


class AnalysisRepository:
    """Repository for analysis results."""
    
    @staticmethod
    def save_result(
        analysis_id: str,
        status: str,
        processing_time: float,
        description: Optional[str] = None,
        confidence: Optional[float] = None,
        tags: Optional[List[str]] = None,
        objects_detected: Optional[List[str]] = None,
        error: Optional[str] = None,
        user_id: Optional[str] = None,
        image_size: Optional[int] = None
    ):
        """Save analysis result to database."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO analysis_results (
                    id, timestamp, status, image_size, processing_time,
                    description, confidence, tags, objects_detected, error, user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                analysis_id,
                datetime.now().isoformat(),
                status,
                image_size,
                processing_time,
                description,
                confidence,
                json.dumps(tags or []),
                json.dumps(objects_detected or []),
                error,
                user_id
            ))
    
    @staticmethod
    def get_result(analysis_id: str) -> Optional[Dict]:
        """Get analysis result by ID."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM analysis_results WHERE id = ?",
                (analysis_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return {
                    "id": row["id"],
                    "timestamp": row["timestamp"],
                    "status": row["status"],
                    "processing_time": row["processing_time"],
                    "description": row["description"],
                    "confidence": row["confidence"],
                    "tags": json.loads(row["tags"]) if row["tags"] else [],
                    "objects_detected": json.loads(row["objects_detected"]) if row["objects_detected"] else [],
                    "error": row["error"]
                }
            return None
    
    @staticmethod
    def get_user_history(user_id: str, limit: int = 50) -> List[Dict]:
        """Get analysis history for a user."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM analysis_results 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (user_id, limit))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    "id": row["id"],
                    "timestamp": row["timestamp"],
                    "status": row["status"],
                    "processing_time": row["processing_time"],
                    "description": row["description"],
                    "confidence": row["confidence"],
                    "tags": json.loads(row["tags"]) if row["tags"] else [],
                    "objects_detected": json.loads(row["objects_detected"]) if row["objects_detected"] else []
                })
            
            return results
    
    @staticmethod
    def get_recent_analyses(limit: int = 100) -> List[Dict]:
        """Get recent analyses."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, timestamp, status, processing_time, user_id
                FROM analysis_results 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    "id": row["id"],
                    "timestamp": row["timestamp"],
                    "status": row["status"],
                    "processing_time": row["processing_time"],
                    "user_id": row["user_id"]
                })
            
            return results


class AnalyticsRepository:
    """Repository for analytics events."""
    
    @staticmethod
    def track_event(event_type: str, event_data: Optional[Dict] = None, user_id: Optional[str] = None):
        """Track an analytics event."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO analytics (timestamp, event_type, event_data, user_id)
                VALUES (?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                event_type,
                json.dumps(event_data or {}),
                user_id
            ))
    
    @staticmethod
    def get_statistics() -> Dict:
        """Get system statistics."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) as total FROM analysis_results")
            total_analyses = cursor.fetchone()["total"]
            
            cursor.execute("SELECT COUNT(*) as total FROM analysis_results WHERE status = 'completed'")
            successful = cursor.fetchone()["total"]
            
            cursor.execute("SELECT AVG(processing_time) as avg FROM analysis_results WHERE status = 'completed'")
            avg_time = cursor.fetchone()["avg"] or 0
            
            cursor.execute("SELECT COUNT(DISTINCT user_id) as total FROM analysis_results WHERE user_id IS NOT NULL")
            unique_users = cursor.fetchone()["total"]
            
            return {
                "total_analyses": total_analyses,
                "successful_analyses": successful,
                "failed_analyses": total_analyses - successful,
                "average_processing_time": round(avg_time, 2),
                "unique_users": unique_users
            }
