# Data Engine Tests Package
import sys
from pathlib import Path

# Ensure project root is on sys.path
data_dir = Path(__file__).resolve().parent.parent
project_root = data_dir.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
