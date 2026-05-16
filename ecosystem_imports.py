from pathlib import Path
import sys


ECOSYSTEM_ROOT = Path(__file__).resolve().parents[1]

if str(ECOSYSTEM_ROOT) not in sys.path:
    sys.path.insert(0, str(ECOSYSTEM_ROOT))
