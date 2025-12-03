"""Baseline profiler for statistical behavior analysis."""

import statistics
from datetime import datetime, timedelta
from typing import List, Optional
from pic.models.baseline import BaselineProfile
from pic.models.events import TelemetryEvent


class BaselineProfiler:
    """Build statistical profiles of normal behavior."""
    
    def __init__(self, min_samples: int = 20):
        """Initialize profiler.
        
        Args:
            min_samples: Minimum samples required for baseline
        """
        self.min_samples = min_samples
        self._samples: dict = {}  # function_name -> list of durations
    
    def add_sample(self, event: TelemetryEvent) -> None:
        """Add telemetry sample to profile.
        
        Args:
            event: TelemetryEvent to add
        """
        key = f"{event.module_name}.{event.function_name}"
        if key not in self._samples:
            self._samples[key] = []
        self._samples[key].append(event.duration_ms)
    
    def compute_baseline(self, function_name: str, module_name: str) -> Optional[BaselineProfile]:
        """Compute baseline profile for a function.
        
        Args:
            function_name: Function name
            module_name: Module name
            
        Returns:
            BaselineProfile if sufficient samples, None otherwise
        """
        key = f"{module_name}.{function_name}"
        samples = self._samples.get(key, [])
        
        if len(samples) < self.min_samples:
            return None
        
        # Compute statistics
        mean = statistics.mean(samples)
        std = statistics.stdev(samples) if len(samples) > 1 else 0.0
        sorted_samples = sorted(samples)
        
        return BaselineProfile(
            function_name=function_name,
            module_name=module_name,
            version=1,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            sample_count=len(samples),
            mean_duration_ms=mean,
            std_duration_ms=std,
            p50_duration_ms=sorted_samples[len(sorted_samples) // 2],
            p95_duration_ms=sorted_samples[int(len(sorted_samples) * 0.95)],
            p99_duration_ms=sorted_samples[int(len(sorted_samples) * 0.99)],
            historical_distances=[]
        )

    def get_sample_count(self, function_name: str, module_name: str) -> int:
        """Get number of samples collected for a function.
        
        Args:
            function_name: Function name
            module_name: Module name
            
        Returns:
            Number of samples collected
        """
        key = f"{module_name}.{function_name}"
        return len(self._samples.get(key, []))
