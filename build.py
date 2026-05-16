#!/usr/bin/env python3
"""
Build RPOFlip Desktop App into .exe (Windows) or .app (macOS)
Usage: python build.py
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
DIST_DIR = BASE_DIR / "dist"
BUILD_DIR = BASE_DIR / "build"

# ─── CLEAN PREVIOUS BUILDS ───
print("Cleaning previous builds...")
for folder in [DIST_DIR, BUILD_DIR]:
    if folder.exists():
        shutil.rmtree(folder)

# ─── BUILD COMMAND ───
print("Building executable...")
print("This may take 2-5 minutes on first run.")
print()

cmd = [
    sys.executable, "-m", "PyInstaller",
    "--name", "RPOFlip",
    "--onefile",
    "--windowed",
    "--noconfirm",
    "--clean",
    # Add data files
    "--add-data", f"app.py{os.pathsep}.",
    "--add-data", f"index.html{os.pathsep}.",
    "--add-data", f"requirements.txt{os.pathsep}.",
]

# Add pdfs folder if exists
pdfs_dir = BASE_DIR / "pdfs"
if pdfs_dir.exists():
    cmd.extend(["--add-data", f"pdfs{os.pathsep}pdfs"])

# Hidden imports
cmd.extend([
    "--hidden-import", "flask",
    "--hidden-import", "flask_cors",
    "--hidden-import", "werkzeug",
    "--hidden-import", "fitz",
    "--hidden-import", "webview",
    "--hidden-import", "webview.platforms.winforms",
])

# Icon
icon_file = BASE_DIR / "icon.ico"
if icon_file.exists():
    cmd.extend(["--icon", str(icon_file)])

cmd.append("run_app.py")

result = subprocess.run(cmd, cwd=str(BASE_DIR))

if result.returncode != 0:
    print("\nBUILD FAILED")
    sys.exit(1)

print("\nBUILD SUCCESSFUL")
print(f"Output: {DIST_DIR / 'RPOFlip.exe'}")
print()
print("To distribute, share the entire 'dist' folder.")
