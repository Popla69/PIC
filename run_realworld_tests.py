#!/usr/bin/env python3
"""Direct runner for Real-World Testing Suite

Bypasses virtual environment issues by running directly.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Suppress the venv warning
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

def main():
    """Run the real-world testing CLI."""
    try:
        from pic.realworld.cli import main as cli_main
        cli_main()
    except ImportError as e:
        print(f"Import Error: {e}")
        print("\nTrying alternative import method...")
        
        # Alternative: Run directly
        import importlib.util
        
        cli_path = Path(__file__).parent / "src" / "pic" / "realworld" / "cli.py"
        spec = importlib.util.spec_from_file_location("cli", cli_path)
        cli_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cli_module)
        cli_module.main()

if __name__ == '__main__':
    main()
