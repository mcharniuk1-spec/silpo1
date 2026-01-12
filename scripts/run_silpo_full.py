"""
Entry point for: python -m scripts.run_silpo_full
This ensures PYTHONPATH=src is properly set in CI
"""
from silpo.run_full import main

if __name__ == "__main__":
    main()
