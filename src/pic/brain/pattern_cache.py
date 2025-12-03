"""Pattern Memory Cache for fast legitimate traffic recognition."""

import time
import hashlib
from typing import Optional, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime
from pic.models.events import TelemetryEvent


@dataclass
class PatternFingerprint:
    """Behavioral fingerprint of a legitimate event pattern."""
    function_name: str
    module_name: str
    duration_min: float
    duration_max: float
    arg_types: Tuple[str, ...]
    resource_signature: str
    timestamp: float
    hit_count: int = 0
    
    def matches(self, event: TelemetryEvent, threshold: float = 0.85) -> bool:
        """Check if event matches this pattern with fuzzy matching.
        
        Args:
            event: TelemetryEvent to check
            threshold: Similarity threshold (0.0-1.0)
            
        Returns:
            True if event matches pattern
        """
        score = 0.0
        total_weight = 0.0
        
        # Function name match (weight: 0.3)
        if event.function_name == self.function_name:
            score += 0.3
        total_weight += 0.3
        
        # Module name match (weight: 0.2)
        if event.module_name == self.module_name:
            score += 0.2
        total_weight += 0.2
        
        # Duration range match (weight: 0.3)
        if self.duration_min <= event.duration_ms <= self.duration_max:
            score += 0.3
        elif self.duration_min * 0.8 <= event.duration_ms <= self.duration_max * 1.2:
            # Allow 20% tolerance
            score += 0.15
        total_weight += 0.3
        
        # Arg types match (weight: 0.2)
        event_arg_types = tuple(event.args_metadata.get("arg_types", []))
        if event_arg_types == self.arg_types:
            score += 0.2
        elif len(event_arg_types) == len(self.arg_types):
            # Partial match if same length
            score += 0.1
        total_weight += 0.2
        
        similarity = score / total_weight if total_weight > 0 else 0.0
        return similarity >= threshold
    
    def to_key(self) -> str:
        """Generate cache key for this pattern."""
        return f"{self.function_name}:{self.module_name}"


class PatternMemoryCache:
    """Fast-path cache for known legitimate patterns."""
    
    def __init__(self, ttl_seconds: int = 1800, max_size: int = 10000):
        """Initialize pattern cache.
        
        Args:
            ttl_seconds: Time-to-live for cached patterns (default: 30 minutes)
            max_size: Maximum number of patterns to cache
        """
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self._cache: Dict[str, PatternFingerprint] = {}
        self._access_times: Dict[str, float] = {}
        
        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
    
    def add_pattern(self, event: TelemetryEvent) -> None:
        """Store approved legitimate pattern.
        
        Args:
            event: TelemetryEvent to cache as legitimate
        """
        # Create fingerprint
        fingerprint = self._create_fingerprint(event)
        key = fingerprint.to_key()
        
        # Check if pattern already exists
        if key in self._cache:
            # Update hit count and timestamp
            self._cache[key].hit_count += 1
            self._cache[key].timestamp = time.time()
            self._access_times[key] = time.time()
        else:
            # Add new pattern
            if len(self._cache) >= self.max_size:
                self._evict_lru()
            
            self._cache[key] = fingerprint
            self._access_times[key] = time.time()
    
    def check_match(self, event: TelemetryEvent, threshold: float = 0.85) -> bool:
        """Check if event matches any cached pattern.
        
        Args:
            event: TelemetryEvent to check
            threshold: Similarity threshold (0.0-1.0)
            
        Returns:
            True if event matches a cached pattern
        """
        # Quick lookup by key
        key = f"{event.function_name}:{event.module_name}"
        
        if key in self._cache:
            pattern = self._cache[key]
            
            # Check if pattern is expired
            if time.time() - pattern.timestamp > self.ttl_seconds:
                del self._cache[key]
                del self._access_times[key]
                self._misses += 1
                return False
            
            # Check if pattern matches
            if pattern.matches(event, threshold):
                self._hits += 1
                self._access_times[key] = time.time()
                pattern.hit_count += 1
                return True
        
        self._misses += 1
        return False
    
    def _create_fingerprint(self, event: TelemetryEvent) -> PatternFingerprint:
        """Create behavioral fingerprint from event.
        
        Args:
            event: TelemetryEvent to fingerprint
            
        Returns:
            PatternFingerprint
        """
        # Extract arg types
        arg_types = tuple(event.args_metadata.get("arg_types", []))
        
        # Create resource signature (hash of resource tags)
        resource_str = str(sorted(event.resource_tags.items()))
        resource_sig = hashlib.md5(resource_str.encode()).hexdigest()[:8]
        
        # Duration range with 10% tolerance
        duration_min = event.duration_ms * 0.9
        duration_max = event.duration_ms * 1.1
        
        return PatternFingerprint(
            function_name=event.function_name,
            module_name=event.module_name,
            duration_min=duration_min,
            duration_max=duration_max,
            arg_types=arg_types,
            resource_signature=resource_sig,
            timestamp=time.time(),
            hit_count=1
        )
    
    def _evict_lru(self) -> None:
        """Evict least recently used pattern."""
        if not self._access_times:
            return
        
        # Find LRU key
        lru_key = min(self._access_times.items(), key=lambda x: x[1])[0]
        
        # Remove from cache
        del self._cache[lru_key]
        del self._access_times[lru_key]
        self._evictions += 1
    
    def evict_expired(self) -> int:
        """Remove expired patterns.
        
        Returns:
            Number of patterns evicted
        """
        current_time = time.time()
        expired_keys = [
            key for key, pattern in self._cache.items()
            if current_time - pattern.timestamp > self.ttl_seconds
        ]
        
        for key in expired_keys:
            del self._cache[key]
            del self._access_times[key]
        
        evicted_count = len(expired_keys)
        self._evictions += evicted_count
        return evicted_count
    
    def get_stats(self) -> Dict[str, any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0.0
        
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate_pct": hit_rate,
            "evictions": self._evictions,
            "ttl_seconds": self.ttl_seconds
        }
    
    def clear(self) -> None:
        """Clear all cached patterns."""
        self._cache.clear()
        self._access_times.clear()
