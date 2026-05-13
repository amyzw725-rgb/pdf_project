"""
Verify third-party packages for streamlit_app + process_pdfs.

  py check_imports.py              check only (exit 1 if anything missing)
  py check_imports.py --install   if missing, run pip install -r requirements.txt once, then recheck
"""

import argparse
import importlib
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_REQUIREMENTS = _ROOT / "requirements.txt"

# (import name, pip install name)
REQUIRED = [
    ("streamlit", "streamlit"),
    ("pdfplumber", "pdfplumber"),
    ("pandas", "pandas"),
    ("pytesseract", "pytesseract"),
    ("pdf2image", "pdf2image"),
    ("PIL", "pillow"),
    ("cv2", "opencv-python"),
    ("numpy", "numpy"),
    ("openpyxl", "openpyxl"),
]


def _missing_modules():
    missing = []
    for mod, pip_name in REQUIRED:
        try:
            importlib.import_module(mod)
        except ImportError:
            missing.append((mod, pip_name))
    return missing


def check_once() -> int:
    """Return 0 if OK, 1 if failed."""
    missing = _missing_modules()
    if missing:
        print("Missing or broken Python packages:", file=sys.stderr)
        for mod, pip in missing:
            print(f"  - import {mod}  ->  pip install {pip}", file=sys.stderr)
        return 1

    try:
        import process_pdfs  # noqa: F401
    except Exception as e:
        print(f"process_pdfs import failed: {e}", file=sys.stderr)
        return 1

    print("All imports OK (including process_pdfs).")
    return 0


def pip_install_requirements() -> bool:
    if not _REQUIREMENTS.is_file():
        print(f"Missing {_REQUIREMENTS.name}; cannot auto-install.", file=sys.stderr)
        return False
    cmd = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "-r",
        str(_REQUIREMENTS),
    ]
    print("Installing dependencies from requirements.txt ...")
    result = subprocess.run(cmd, cwd=str(_ROOT))
    if result.returncode != 0:
        print("pip install failed.", file=sys.stderr)
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Check PDF/Streamlit app dependencies.")
    parser.add_argument(
        "--install",
        action="store_true",
        help="If checks fail, run pip install -r requirements.txt once and verify again.",
    )
    args = parser.parse_args()

    if check_once() == 0:
        return 0

    if not args.install:
        pip_pkgs = " ".join(p for _, p in _missing_modules()) or "(see requirements.txt)"
        print("\nInstall with:", file=sys.stderr)
        print(f"  {sys.executable} -m pip install -r requirements.txt", file=sys.stderr)
        if _missing_modules():
            print(f"  {sys.executable} -m pip install {pip_pkgs}", file=sys.stderr)
        return 1

    if not pip_install_requirements():
        return 1

    print("Re-checking imports after install ...")
    if check_once() != 0:
        print("Imports still failing after pip install.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
