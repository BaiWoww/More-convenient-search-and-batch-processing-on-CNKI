# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for CNKI Desktop

import os
import sys
from pathlib import Path

block_cipher = None

# 获取 playwright driver 路径
try:
    import playwright
    pw_path = os.path.dirname(playwright.__file__)
except ImportError:
    pw_path = None

datas = []
if pw_path and os.path.exists(pw_path):
    datas.append((pw_path, 'playwright'))

# 图标路径 (如果有)
icon_path = 'assets/icon.ico' if os.path.exists('assets/icon.ico') else None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'playwright',
        'playwright.sync_api',
        'playwright._impl',
        'playwright._impl._driver',
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtWidgets',
        'PySide6.QtGui',
        'bs4',
        'bs4.builder._lxml',
        'lxml',
        'lxml.etree',
        'lxml._elementpath',
        'openpyxl',
        'openpyxl.cell',
        'openpyxl.styles',
        'docx',
        'docx.document',
        'docx.oxml',
        'core',
        'core.config',
        'core.api',
        'core.download',
        'core.citation',
        'core.exporter',
        'cnki_desktop',
        'cnki_desktop.app',
        'cnki_desktop.search_panel',
        'cnki_desktop.results_table',
        'cnki_desktop.export_panel',
        'cnki_desktop.status_panel',
        'cnki_desktop.styles',
        'cnki_desktop.browser_setup',
        'cnki_desktop.workers',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'PIL',
        'cv2',
    ],
    win_no_console=False,  # True for release, False for debugging
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CNKI_Desktop',
    icon=icon_path,
    console=False,
    windows=[{
        'name': 'CNKI论文检索助手',
    }],
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CNKI_Desktop',
)
