import os
import sys

# Add the project root directory to Python's module search path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import app
