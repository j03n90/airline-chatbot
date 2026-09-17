import os
import sys
from pathlib import Path

os.environ["CHECKPOINT_BACKEND"] = "memory"

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
