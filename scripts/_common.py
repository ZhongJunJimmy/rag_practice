"""
Common utilities for scripts
"""
import sys
import os

def setup_path():
    """Add parent directory to Python path for importing from main package"""
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)