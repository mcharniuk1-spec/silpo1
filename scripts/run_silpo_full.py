import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src")

# Ensure imports from src/
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from silpo.run_full import main

if __name__ == "__main__":
    main()
