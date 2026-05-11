# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None
ROOT = Path.cwd()


def data_tree(folder_name):
    """Collect a folder only when it exists so clean checkouts still build."""
    folder = ROOT / folder_name
    if not folder.exists():
        return []
    return [(str(path), str(path.parent.relative_to(ROOT))) for path in folder.rglob('*') if path.is_file()]


streamlit_datas, streamlit_binaries, streamlit_hiddenimports = collect_all('streamlit')
pandas_datas, pandas_binaries, pandas_hiddenimports = collect_all('pandas')
playwright_datas, playwright_binaries, playwright_hiddenimports = collect_all('playwright')

hiddenimports = []
hiddenimports += streamlit_hiddenimports
hiddenimports += pandas_hiddenimports
hiddenimports += playwright_hiddenimports
hiddenimports += collect_submodules('modules')
hiddenimports += collect_submodules('services')
hiddenimports += [
    'altair',
    'openpyxl',
    'pptx',
    'requests',
    'tornado',
    'watchdog',
]

datas = []
datas += streamlit_datas
datas += pandas_datas
datas += playwright_datas
datas += [('app.py', '.')]
datas += data_tree('modules')
datas += data_tree('services')
datas += data_tree('assets')
datas += data_tree('configs')

binaries = []
binaries += streamlit_binaries
binaries += pandas_binaries
binaries += playwright_binaries


a = Analysis(
    ['electron/desktop_backend.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    name='app',
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
    icon='electron/assets/icon.ico',
)
