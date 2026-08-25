"""
desktop_app.py — SmallChip AI desktop app

A native macOS/Windows/Linux window that wraps the SmallChip AI web app.
Uses pywebview (a thin wrapper over WKWebView on macOS, WebView2 on Windows,
WebKitGTK on Linux). Auto-starts the FastAPI backend if not already running.

Usage:
    python desktop_app.py

Builds a standalone .app on macOS with:
    python setup.py py2app
"""

import os
import sys
import subprocess
import time
import socket
import webview
from pathlib import Path

APP_NAME = "SmallChip AI"
APP_VERSION = "0.2.0"
DEFAULT_PORT = 8000
DEFAULT_URL = f"http://localhost:{DEFAULT_PORT}"


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


def wait_for_server(port: int, timeout: float = 30.0) -> bool:
    """Block until the server is responding on the given port."""
    start = time.time()
    while time.time() - start < timeout:
        if is_port_in_use(port):
            return True
        time.sleep(0.5)
    return False


def start_backend(port: int) -> subprocess.Popen:
    """Start the FastAPI backend. Returns the Popen handle."""
    repo = Path(__file__).parent.resolve()
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "chipmind.api.server:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--log-level",
        "info",
    ]
    print(f"Starting backend: {' '.join(cmd)}")
    return subprocess.Popen(
        cmd,
        cwd=repo,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def main() -> None:
    port = int(os.environ.get("SMALLCHIP_PORT", DEFAULT_PORT))
    url = f"http://localhost:{port}"

    if is_port_in_use(port):
        print(f"Backend already running on port {port}, attaching.")
        backend = None
    else:
        print(f"No backend on port {port}, starting one...")
        backend = start_backend(port)
        if not wait_for_server(port, timeout=30.0):
            print("Backend failed to start within 30s.")
            if backend is not None:
                backend.terminate()
            sys.exit(1)
        print(f"Backend up on port {port}.")

    # Open the native window
    window = webview.create_window(
        title=f"{APP_NAME} v{APP_VERSION}",
        url=url,
        width=1280,
        height=820,
        min_size=(900, 600),
        resizable=True,
        fullscreen=False,
        text_select=True,
    )
    print(f"Opening {APP_NAME} window at {url}")
    webview.start(debug=False)

    # When the window closes, shut down the backend if we started it
    if backend is not None:
        print("Shutting down backend.")
        backend.terminate()
        backend.wait(timeout=5)


if __name__ == "__main__":
    main()
