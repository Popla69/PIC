"""CLI interface for PIC."""

import sys
import argparse
from pic.config import PICConfig
from pic.crypto import CryptoCore
from pic.storage.state_store import StateStore
from pic.storage.audit_store import AuditStore
from pic.storage.trace_store import TraceStore
from pic.brain.core import BrainCore
from pic.brain.api import BrainAPI


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="PIC v1 - Popla Immune Core")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Start command
    start_parser = subparsers.add_parser("start", help="Start SentinelBrain service")
    start_parser.add_argument("--config", help="Config file path")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show system status")
    
    # Logs command
    logs_parser = subparsers.add_parser("logs", help="Export audit logs")
    logs_parser.add_argument("--start", help="Start time")
    logs_parser.add_argument("--end", help="End time")
    
    args = parser.parse_args()
    
    if args.command == "start":
        start_service(args.config)
    elif args.command == "status":
        show_status()
    elif args.command == "logs":
        export_logs(args.start, args.end)
    else:
        parser.print_help()


def start_service(config_path=None):
    """Start SentinelBrain service."""
    print("Starting PIC v1 SentinelBrain...")
    
    # Load config
    config = PICConfig.load(config_path)
    
    # Initialize components
    crypto = CryptoCore("/var/lib/pic/signing.key")
    state_store = StateStore(config.get("storage.state_db_path"))
    audit_store = AuditStore(config.get("storage.audit_log_path"), crypto)
    trace_store = TraceStore(config.get("storage.trace_buffer_size"))
    
    # Create brain
    brain = BrainCore(state_store, audit_store, trace_store, crypto)
    
    # Start API
    api = BrainAPI(
        brain,
        host=config.get("api.listen_address"),
        port=config.get("api.listen_port")
    )
    
    print(f"SentinelBrain listening on {config.get('api.listen_address')}:{config.get('api.listen_port')}")
    api.start()


def show_status():
    """Show system status."""
    print("PIC v1 Status:")
    print("  Version: 1.0.0")
    print("  Status: Running")


def export_logs(start_time=None, end_time=None):
    """Export audit logs."""
    print(f"Exporting logs from {start_time} to {end_time}")
    # TODO: Implement log export


if __name__ == "__main__":
    main()
