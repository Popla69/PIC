"""Property test for telemetry event schema compliance.

Feature: pic-v1-immune-core, Property 52: Telemetry Event Schema Compliance
Validates: Requirements 17.1
"""

from datetime import datetime
from hypothesis import given, strategies as st

from pic.models.events import TelemetryEvent


@given(
    timestamp=st.datetimes(),
    event_id=st.uuids().map(str),
    process_id=st.integers(min_value=1, max_value=65535),
    thread_id=st.integers(min_value=1, max_value=65535),
    function_name=st.text(min_size=1, max_size=100),
    module_name=st.text(min_size=1, max_size=100),
    duration_ms=st.floats(min_value=0.0, max_value=10000.0),
    sampling_rate=st.floats(min_value=0.0, max_value=1.0),
)
def test_telemetry_event_schema_compliance(
    timestamp, event_id, process_id, thread_id,
    function_name, module_name, duration_ms, sampling_rate
):
    """
    Property 52: Telemetry Event Schema Compliance
    
    For any generated telemetry event, the JSON shall contain all required fields:
    timestamp, process_id, thread_id, function_name, args_metadata, duration_ms,
    resource_tags, redaction_hashes
    """
    # Create event
    event = TelemetryEvent(
        timestamp=timestamp,
        event_id=event_id,
        process_id=process_id,
        thread_id=thread_id,
        function_name=function_name,
        module_name=module_name,
        duration_ms=duration_ms,
        args_metadata={"arg_count": 0, "arg_types": [], "arg_hashes": []},
        resource_tags={"io_operations": 0, "network_calls": 0, "file_access": 0},
        redaction_applied=False,
        sampling_rate=sampling_rate,
    )
    
    # Serialize to JSON
    json_str = event.to_json()
    
    # Verify all required fields are present
    assert "timestamp" in json_str
    assert "event_id" in json_str
    assert "process_id" in json_str
    assert "thread_id" in json_str
    assert "function_name" in json_str
    assert "module_name" in json_str
    assert "duration_ms" in json_str
    assert "args_metadata" in json_str
    assert "resource_tags" in json_str
    assert "redaction_applied" in json_str
    assert "sampling_rate" in json_str
    
    # Verify round-trip serialization
    deserialized = TelemetryEvent.from_json(json_str)
    assert deserialized.event_id == event_id
    assert deserialized.function_name == function_name
    assert deserialized.process_id == process_id
