"""
setup.py — Build standalone macOS .app bundle for SmallChip AI.

Builds with: python setup.py py2app
Output: dist/SmallChip AI.app (drag to /Applications)
"""
from setuptools import setup

APP = ["desktop_app.py"]
DATA_FILES = [
    ("web", [
        "web/index.html",
        "web/copilot.html",
        "web/landing.html",
        "web/app.js",
        "web/style.css",
        "web/landing.css",
        "web/manifest.json",
        "web/sw.js",
        "web/icon-192.png",
        "web/icon-512.png",
    ]),
]

OPTIONS = {
    "argv_emulation": False,
    "plist": {
        "CFBundleName": "SmallChip AI",
        "CFBundleDisplayName": "SmallChip AI",
        "CFBundleIdentifier": "ai.smallchip.desktop",
        "CFBundleVersion": "0.2.0",
        "CFBundleShortVersionString": "0.2.0",
        "LSMinimumSystemVersion": "11.0",
        "NSHighResolutionCapable": True,
        "CFBundleIconFile": "icon-512.png",
        "NSAppleScriptEnabled": False,
    },
    "packages": ["chipmind", "webview", "bottle", "proxy_tools", "chipmind.api", "chipmind.core", "chipmind.ml", "chipmind.algorithms"],
    "includes": ["torch", "torch_geometric"],
    "excludes": ["tkinter", "matplotlib", "scipy"],
}

setup(
    app=APP,
    name="SmallChip AI",
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
