"""Run with Python 3, no third-party packages required."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "game/python-packages"))
from foundation.model import load_project, validate

if __name__ == "__main__":
    try:
        errors = validate(load_project(ROOT / "game"), ROOT / "game")
    except (ValueError, KeyError, TypeError, OSError) as exc:
        errors = [str(exc)]
    for error in errors:
        print("ERROR:", error)
    print("Validation:", "FAIL" if errors else "PASS")
    sys.exit(bool(errors))
