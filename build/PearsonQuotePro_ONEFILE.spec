# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

SPEC_FILE = Path(globals().get('__file__', 'build/PearsonQuotePro_ONEFILE.spec')).resolve()
SPEC_DIR = SPEC_FILE.parent
PROJECT_ROOT = SPEC_DIR.parent
MAIN_SCRIPT = PROJECT_ROOT / 'main.py'

if not MAIN_SCRIPT.exists():
    # Fallback for environments that evaluate spec from a different base path.
    MAIN_SCRIPT = Path.cwd() / 'main.py'

if not MAIN_SCRIPT.exists():
    raise FileNotFoundError(f'main.py not found for build: {MAIN_SCRIPT}')

a = Analysis(
    [str(MAIN_SCRIPT)],
    pathex=[str(PROJECT_ROOT), str(Path.cwd())],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='PearsonQuotePro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
