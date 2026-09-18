import os
import sys

# Add project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import init_db
try:
    init_db()
except Exception as ex:
    pass

from server import app
