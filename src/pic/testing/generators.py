"""Test data generators for PIC testing."""

import random
from datetime import datetime, timedelta
from typing import List
from pic.models.events import TelemetryEvent


class TestDataGenerator:
    """Generate synthetic telemetry data for testing."""
    
    def __init__(self, seed: int = 42):
        """Initialize generator with seed for reproducibility.
        
        Args:
            seed: Random seed for deterministic generation
        """
        self.seed = seed
        random.seed(seed)
    
    def generate_benign_events(
        self,
        count: int = 1000,
        function_name: str = "test_function",
        module_name: str = "test_module",
        mean_duration: float = 50.0,
        std_duration: float = 10.0
    ) -> List[TelemetryEvent]:
        """Generate benign telemetry events.
        
        Args:
            count: Number of events to generate
            function_name: Function name for events
            module_name: Module name for events
            mean_duration: Mean duration in ms
            std_duration: Standard deviation of duration
            
        Returns:
            List of benign TelemetryEvent instances
        """
        events = []
        base_time = datetime.now()
        
        for i in range(count):
            # Generate normal duration (Gaussian distribution)
            duration = max(1.0, random.gauss(mean_duration, std_duration))
            
            event = TelemetryEvent(
                timestamp=base_time + timedelta(milliseconds=i * 100),
                event_id=f"benign-{i}",
                process_id=1234,
                thread_id=5678,
                function_name=function_name,
                module_name=module_name,
                duration_ms=duration,
                args_metadata={},
                resource_tags={"type": "benign"},
                redaction_applied=False,
                sampling_rate=1.0
            )
            events.append(event)
        
        return events
    
    def generate_malicious_events(
        self,
        pattern: str = "slowloris",
        count: int = 100,
        function_name: str = "test_function",
        module_name: str = "test_module"
    ) -> List[TelemetryEvent]:
        """Generate malicious telemetry events with specific attack patterns.
        
        Args:
            pattern: Attack pattern (slowloris, spike, gradual, burst, oscillating)
            count: Number of events to generate
            function_name: Function name for events
            module_name: Module name for events
            
        Returns:
            List of malicious TelemetryEvent instances
        """
        events = []
        base_time = datetime.now()
        
        for i in range(count):
            # Generate malicious duration based on pattern
            if pattern == "slowloris":
                # Consistently slow (10x normal)
                duration = 500.0 + random.uniform(-50, 50)
            elif pattern == "spike":
                # Sudden spike (20x normal)
                duration = 1000.0 + random.uniform(-100, 100)
            elif pattern == "gradual":
                # Gradually increasing
                duration = 50.0 + (i * 5.0)
            elif pattern == "burst":
                # Periodic bursts
                duration = 500.0 if i % 10 == 0 else 50.0
            elif pattern == "oscillating":
                # Oscillating between normal and high
                duration = 500.0 if i % 2 == 0 else 50.0
            else:
                duration = 500.0
            
            event = TelemetryEvent(
                timestamp=base_time + timedelta(milliseconds=i * 100),
                event_id=f"malicious-{pattern}-{i}",
                process_id=1234,
                thread_id=5678,
                function_name=function_name,
                module_name=module_name,
                duration_ms=duration,
                args_metadata={},
                resource_tags={"type": "malicious", "pattern": pattern},
                redaction_applied=False,
                sampling_rate=1.0
            )
            events.append(event)
        
        return events
    
    def generate_mixed_dataset(
        self,
        benign_count: int = 1000,
        malicious_count: int = 100,
        function_name: str = "test_function",
        module_name: str = "test_module"
    ) -> tuple[List[TelemetryEvent], List[TelemetryEvent]]:
        """Generate mixed dataset of benign and malicious events.
        
        Args:
            benign_count: Number of benign events
            malicious_count: Number of malicious events per pattern
            function_name: Function name for events
            module_name: Module name for events
            
        Returns:
            Tuple of (benign_events, malicious_events)
        """
        benign = self.generate_benign_events(
            benign_count,
            function_name,
            module_name
        )
        
        # Generate malicious events with different patterns
        malicious = []
        patterns = ["slowloris", "spike", "gradual", "burst", "oscillating"]
        for pattern in patterns:
            malicious.extend(
                self.generate_malicious_events(
                    pattern,
                    malicious_count // len(patterns),
                    function_name,
                    module_name
                )
            )
        
        return benign, malicious
