"""
Entry point for GitHub Actions:
  PYTHONPATH=src python -m scripts.run_silpo_full

This wrapper guarantees `src/` is importable even if PYTHONPATH is not set.
"""
import os
import sys
import traceback

HERE = os.path.dirname(__file__)
REPO_ROOT = os.path.abspath(os.path.join(HERE, ".."))
SRC_DIR = os.path.join(REPO_ROOT, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

def main():
    from silpo.run_full import main as real_main
    real_main()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[FATAL] {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)
