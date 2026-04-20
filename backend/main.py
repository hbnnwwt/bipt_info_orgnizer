# backend/main.py
import sys
import os

# local backend/ dir must come first so "from services" finds local services/
_backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _backend_dir)

# bipthelper paths at the END (append, not insert) so local modules still win
# Only needed for database.py import of bipthelper models
sys.path.append("E:/code/bipthelper/backend")
sys.path.append("E:/code/bipthelper")