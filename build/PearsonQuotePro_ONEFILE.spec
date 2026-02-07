# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.building.build_main import Analysis, PYZ, EXE

block_cipher = None

# Robust project root discovery:
# GitHub Actions / PyInstaller may execute this spec with cwd at repo root OR at build/.
# We search upward from cwd to find main.py (repo root marker).
cwd = os.path.abspath(os.getcwd())

def find_project_dir(start: str, max_up: int = 4) -> str:
    cur = start
    for _ in range(max_up + 1):
        if os.path.isfile(os.path.join(cur, "main.py")):
            return cur
        parent = os.path.abspath(os.path.join(cur, ".."))
        if parent == cur:
            break
        cur = parent
    # Fallback: assume spec is in build/ and project is parent
    return os.path.abspath(os.path.join(start, ".."))

PROJECT_DIR = find_project_dir(cwd)
ASSETS_DIR = os.path.join(PROJECT_DIR, "assets")

APP_NAME = "PearsonQuotePro"
ICON_PATH = os.path.join(ASSETS_DIR, "PearsonP.ico")

# Bundle the entire assets folder into the EXE (Excel + images)
datas = []
if os.path.isdir(ASSETS_DIR):
    datas.append((ASSETS_DIR, "assets"))

a = Analysis(
    [os.path.join(PROJECT_DIR, "main.py")],
    pathex=[PROJECT_DIR],
    binaries=[],
    datas=datas,
    hiddenimports=["PySide6.QtSvg", "PySide6.QtXml"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon=ICON_PATH if os.path.exists(ICON_PATH) else None,
)
