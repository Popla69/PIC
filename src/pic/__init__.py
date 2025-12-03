"""
PIC v1 (Popla Immune Core)
A defensive cybersecurity system for Python applications.
"""

__version__ = "1.0.0"
__author__ = "PIC Development Team"

from pic.cellagent import CellAgent
from pic.config import PICConfig

__all__ = ["CellAgent", "PICConfig", "__version__"]
