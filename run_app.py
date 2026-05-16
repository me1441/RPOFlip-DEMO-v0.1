#!/usr/bin/env python3
"""
RPOFlip Desktop App — Flask + PyWebView
Single-window PDF viewer application
"""

import os
import sys
import threading
import time
import webview
from pathlib import Path

# ─── CONFIG ───
FLASK_PORT = 8765
WINDOW_TITLE = "RPOFlip — PDF Viewer"
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900
WINDOW_MIN_W = 900
WINDOW_MIN_H = 600

# ─── PATHS ───
BASE_DIR = Path(__file__).parent.resolve()
PDFS_DIR = BASE_DIR / "pdfs"
UPLOAD_DIR = BASE_DIR / "uploads"

# ─── FLASK APP IMPORT ───
sys.path.insert(0, str(BASE_DIR))

try:
    from app import app as flask_app
except ImportError:
    print("ERROR: app.py not found in the same folder as run_app.py")
    print(f"Expected: {BASE_DIR / 'app.py'}")
    sys.exit(1)

# ─── FLASK BACKEND THREAD ───
flask_thread = None
server_ready = threading.Event()


def start_flask():
    """Run Flask in background thread."""
    UPLOAD_DIR.mkdir(exist_ok=True)
    flask_app.config['UPLOAD_FOLDER'] = str(UPLOAD_DIR)

    try:
        flask_app.run(
            host='127.0.0.1',
            port=FLASK_PORT,
            debug=False,
            threaded=True,
            use_reloader=False
        )
    except Exception as e:
        print(f"Flask error: {e}")


def wait_for_server(timeout=10):
    """Wait until Flask server is accepting connections."""
    import socket
    start = time.time()
    while time.time() - start < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', FLASK_PORT))
            sock.close()
            if result == 0:
                return True
        except:
            pass
        time.sleep(0.2)
    return False


# ─── WINDOW API FOR JS ───
class Api:
    """Bridge between JavaScript and Python."""

    def minimize(self):
        window = webview.active_window()
        if window:
            window.minimize()

    def toggle_fullscreen(self):
        window = webview.active_window()
        if window:
            window.toggle_fullscreen()

    def get_app_version(self):
        return "1.0.0"

    def get_platform(self):
        return sys.platform


# ─── MAIN ───
if __name__ == '__main__':
    print("=" * 50)
    print("RPOFlip Desktop")
    print("=" * 50)
    print(f"Base dir: {BASE_DIR}")
    print(f"PDFs dir: {PDFS_DIR} (exists: {PDFS_DIR.exists()})")
    print(f"Starting Flask on port {FLASK_PORT}...")

    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()

    print("Waiting for server...")
    if not wait_for_server(timeout=10):
        print("ERROR: Flask server failed to start")
        sys.exit(1)

    print(f"Server ready at http://127.0.0.1:{FLASK_PORT}")
    print("Opening window...")
    print()

    api = Api()

    window = webview.create_window(
        title=WINDOW_TITLE,
        url=f'http://127.0.0.1:{FLASK_PORT}',
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        min_size=(WINDOW_MIN_W, WINDOW_MIN_H),
        resizable=True,
        text_select=True,
        confirm_close=True,
        js_api=api
    )

    webview.start(debug=False)

    print("Window closed. Exiting.")
    sys.exit(0)
