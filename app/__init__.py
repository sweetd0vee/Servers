import os
import sys

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Optional: Import logger directly for easier access
from base_logger import logger

# Export logger so it can be imported from app package
__all__ = ['logger']