# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.building.build_main import Analysis, PYZ, EXE

block_cipher = None

# Robust project root discovery (works in GitHub Actions + local)
cwd = os.path.abspath(os.getcwd())

def find_project_dir(start: str, max_up: int = 6) -> str:
    cur = start
    for _ in range(max_up + 1):
        if os.path.isfile(os.path.join(cur, "main.py")):
            return cur
        parent = os.path.abspath(os.path.join(cur, ".."))
        if parent == cur:
            break
        cur = parent
    return os.path.abspath(os.path.join(start, ".."))

PROJECT_DIR = find_project_dir(cwd)
ASSETS_DIR = os.path.join(PROJECT_DIR, "assets")

APP_NAME = "PearsonQuotePro"
ICON_PATH = os.path.join(ASSETS_DIR, "PearsonP.ico")

# Bundle assets in two locations:
# 1) /assets (Quote Pro expects this)
# 2) /legacy_pcp/assets (PCP code expects this path when frozen)
datas = []
if os.path.isdir(ASSETS_DIR):
    datas.append((ASSETS_DIR, "assets"))
    datas.append((ASSETS_DIR, os.path.join("legacy_pcp", "assets")))

a = Analysis(
    [os.path.join(PROJECT_DIR, "main.py")],
    pathex=[PROJECT_DIR],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "PySide6.QtSvg",
        "PySide6.QtXml",
        "app",
        "app.__init__",
        "app.quote_pro_window",
    ],
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
