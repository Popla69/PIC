"""Simple in-memory caching service."""

import hashlib
from typing import Optional, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class CacheService:
    """Simple in-memory cache for analysis results."""
    
    def __init__(self, ttl_minutes: int = 60, max_size: int = 1000):
        """
        Initialize cache service.
        
        Args:
            ttl_minutes: Time to live in minutes
            max_size: Maximum number of items in cache
        """
        self.cache = {}
        self.ttl = timedelta(minutes=ttl_minutes)
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
    
    def _generate_key(self, data: bytes) -> str:
        """Generate cache key from image data."""
        return hashlib.sha256(data).hexdigest()
    
    def get(self, image_data: bytes) -> Optional[Any]:
        """Get cached result for an image."""
        key = self._generate_key(image_data)
        
        if key in self.cache:
            entry = self.cache[key]
            
            if datetime.now() - entry["timestamp"] < self.ttl:
                self.hits += 1
                logger.debug(f"Cache hit for key {key[:8]}...")
                return entry["data"]
            else:
                del self.cache[key]
                logger.debug(f"Cache expired for key {key[:8]}...")
        
        self.misses += 1
        return None
    
    def set(self, image_data: bytes, result: Any):
        """Cache a result."""
        if len(self.cache) >= self.max_size:
            self._evict_oldest()
        
        key = self._generate_key(image_data)
        self.cache[key] = {
            "data": result,
            "timestamp": datetime.now()
        }
        
        logger.debug(f"Cached result for key {key[:8]}...")
    
    def _evict_oldest(self):
        """Evict oldest entries when cache is full."""
        if not self.cache:
            return
        
        oldest_keys = sorted(
            self.cache.items(),
            key=lambda x: x[1]["timestamp"]
        )[:100]
        
        for key, _ in oldest_keys:
            del self.cache[key]
        
        logger.info(f"Evicted {len(oldest_keys)} old cache entries")
    
    def clear(self):
        """Clear all cache entries."""
        self.cache.clear()
        logger.info("Cache cleared")
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(hit_rate, 2),
            "ttl_minutes": self.ttl.total_seconds() / 60
        }


cache_service = CacheService(ttl_minutes=30, max_size=500)
