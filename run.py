"""
Indoor Wellness & Smart Shelf AI System
One-Click Application Launcher
"""

import os
import sys
import time
import webbrowser
import threading
import uvicorn

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, BASE_DIR)


def open_browser():
    """Wait for server to start, then open the dashboard in browser."""
    time.sleep(1.5)
    url = "http://localhost:8000"
    print(f"\n[+] Opening web dashboard at {url} ...")
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"[!] Could not open browser automatically: {e}")


def main():
    print("=" * 68)
    print("  INDOOR WELLNESS & SMART SHELF AI SYSTEM - SOFTWARE PLATFORM")
    print("  100% Software-Only Execution (Zero Hardware Dependency)")
    print("=" * 68)
    print("Initializing server at http://localhost:8000 ...")

    # Start browser opener in background thread
    threading.Thread(target=open_browser, daemon=True).start()

    # Launch FastAPI via Uvicorn
    uvicorn.run(
        "backend.app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    main()
