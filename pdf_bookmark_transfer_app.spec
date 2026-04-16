# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path


project_root = Path(SPECPATH)
bundle_name = "PDF Bookmark Transfer"
app_version = "0.2.2"
entry_script = str(project_root / "pdf_bookmark_transfer_app.py")

datas = []
binaries = []
hiddenimports = []

analysis = Analysis(
    [entry_script],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(analysis.pure)

exe = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name=bundle_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name=bundle_name,
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name=f"{bundle_name}.app",
        icon=None,
        bundle_identifier="com.zhair.pdfbookmarktransfer",
        info_plist={
            "CFBundleDisplayName": bundle_name,
            "CFBundleName": bundle_name,
            "CFBundleShortVersionString": app_version,
            "CFBundleVersion": "4",
            "LSMinimumSystemVersion": "10.15.0",
            "NSHighResolutionCapable": True,
        },
    )
