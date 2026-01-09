import sys
from pathlib import Path

# Ensure src/ is on PYTHONPATH in any environment (CI/local).
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from silpo.run import main

if __name__ == "__main__":
    main()
