"""Carbon-aware sports scheduling package."""

from __future__ import annotations

from pathlib import Path

try:
    from dotenv import load_dotenv

    ROOT = Path(__file__).resolve().parent.parent
    load_dotenv(dotenv_path=ROOT / ".env", override=False)
except Exception:
    # Keep package import-safe even when python-dotenv is not installed yet.
    pass
