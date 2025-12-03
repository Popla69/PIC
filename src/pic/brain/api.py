"""BrainAPI - HTTP endpoints for telemetry and metrics."""

import json
from flask import Flask, request, jsonify, Response
from pic.brain.core import BrainCore
from pic.models.events import TelemetryEvent


class BrainAPI:
    """HTTP API for SentinelBrain."""
    
    def __init__(self, brain_core: BrainCore, host: str = "127.0.0.1", port: int = 8443):
        """Initialize API.
        
        Args:
            brain_core: BrainCore instance
            host: Listen address
            port: Listen port
        """
        self.brain_core = brain_core
        self.app = Flask(__name__)
        self.host = host
        self.port = port
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Set up API routes."""
        
        @self.app.route("/health", methods=["GET"])
        def health():
            """Health check endpoint."""
            return jsonify({"status": "healthy", "service": "pic-brain"}), 200
        
        @self.app.route("/metrics", methods=["GET"])
        def metrics():
            """Prometheus-format metrics endpoint."""
            stats = self.brain_core.get_stats()
            
            # Generate Prometheus format
            prometheus_metrics = []
            prometheus_metrics.append(f"# HELP pic_events_processed_total Total events processed")
            prometheus_metrics.append(f"# TYPE pic_events_processed_total counter")
            prometheus_metrics.append(f"pic_events_processed_total {stats['events_processed']}")
            
            prometheus_metrics.append(f"# HELP pic_actions_executed_total Total actions executed")
            prometheus_metrics.append(f"# TYPE pic_actions_executed_total counter")
            prometheus_metrics.append(f"pic_actions_executed_total {stats['effector_stats']['actions_executed']}")
            
            prometheus_metrics.append(f"# HELP pic_trace_store_size Current trace store size")
            prometheus_metrics.append(f"# TYPE pic_trace_store_size gauge")
            prometheus_metrics.append(f"pic_trace_store_size {stats['trace_store_size']}")
            
            return Response("\n".join(prometheus_metrics), mimetype="text/plain"), 200
        
        @self.app.route("/status", methods=["GET"])
        def status():
            """System status endpoint."""
            stats = self.brain_core.get_stats()
            return jsonify({
                "status": "running",
                "events_processed": stats["events_processed"],
                "trace_store_size": stats["trace_store_size"],
                "effector_actions": stats["effector_stats"]["actions_executed"]
            }), 200
        
        @self.app.route("/version", methods=["GET"])
        def version():
            """Version information endpoint."""
            return jsonify({
                "version": "1.0.0",
                "name": "PIC v1 (Popla Immune Core)",
                "api_version": "v1"
            }), 200
        
        @self.app.route("/api/v1/telemetry", methods=["POST"])
        def telemetry():
            """Receive telemetry events endpoint."""
            try:
                data = request.json
                if not data:
                    return jsonify({"error": "No data provided"}), 400
                
                events = data.get("events", [])
                if not events:
                    return jsonify({"error": "No events in batch"}), 400
                
                processed = 0
                for event_data in events:
                    try:
                        # Parse event
                        if isinstance(event_data, str):
                            event = TelemetryEvent.from_json(event_data)
                        elif isinstance(event_data, dict):
                            event = TelemetryEvent.from_json(json.dumps(event_data))
                        else:
                            continue
                        
                        # Process event
                        self.brain_core.process_event(event)
                        processed += 1
                    except Exception as e:
                        # Log error but continue processing
                        print(f"Error processing event: {e}")
                        continue
                
                return jsonify({
                    "received": len(events),
                    "processed": processed
                }), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 500
    
    def start(self):
        """Start API server."""
        self.app.run(host=self.host, port=self.port)
