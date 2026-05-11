"""Packaged backend entry point for the Electron desktop app.

This file is intentionally separate from app.py so the existing Streamlit
application remains unchanged. PyInstaller turns this launcher into app.exe.
When Electron starts app.exe, the launcher runs the bundled Streamlit app
internally with headless localhost settings and no browser.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from streamlit.web.cli import main as streamlit_main

HOST = "127.0.0.1"
PORT = "8501"


def bundled_root() -> Path:
    """Return the PyInstaller extraction dir when frozen, else repo root."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parents[1]


def run_streamlit() -> None:
    root = bundled_root()
    app_path = root / "app.py"

    if not app_path.exists():
        raise FileNotFoundError(f"Bundled Streamlit entry file was not found: {app_path}")

    # Make bundled modules/services importable and make relative file access match
    # the normal repo execution mode without changing the existing app.py code.
    os.chdir(root)
    sys.path.insert(0, str(root))

    os.environ.setdefault("STREAMLIT_SERVER_HEADLESS", "true")
    os.environ.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")
    os.environ.setdefault("STREAMLIT_GLOBAL_DEVELOPMENT_MODE", "false")

    # This is the in-process equivalent of `streamlit run app.py`, but end users
    # never install Streamlit globally and never run this command manually.
    sys.argv = [
        "streamlit",
        "run",
        str(app_path),
        "--server.address",
        HOST,
        "--server.port",
        PORT,
        "--server.headless",
        "true",
        "--browser.gatherUsageStats",
        "false",
        "--global.developmentMode",
        "false",
    ]
    streamlit_main()


if __name__ == "__main__":
    run_streamlit()
