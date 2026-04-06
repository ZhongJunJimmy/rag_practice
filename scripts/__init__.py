"""
Scripts package initialization
"""
import sys
import os

# Add parent directory to Python path so scripts can import from the main package
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)