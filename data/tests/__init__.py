# Data Engine Tests Package
import sys
from pathlib import Path

# Ensure data/engine and data/engine/semantic are on sys.path
data_dir = Path(__file__).resolve().parent.parent
engine_dir = data_dir / "engine"
if str(engine_dir) not in sys.path:
    sys.path.insert(0, str(engine_dir))
if str(data_dir) not in sys.path:
    sys.path.insert(0, str(data_dir))

