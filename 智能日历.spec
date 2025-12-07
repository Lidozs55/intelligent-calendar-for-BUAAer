# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['run_app.py'],
    pathex=[],
    binaries=[],
    datas=[('frontend/dist', 'frontend/dist'), ('frontend/public/sound', 'frontend/public/sound'), ('backend/config.py', 'backend'), ('backend/extensions.py', 'backend'), ('backend/models/*.py', 'backend/models'), ('backend/routes/*.py', 'backend/routes'), ('backend/services/*.py', 'backend/services'), ('backend/utils/*.py', 'backend/utils'), ('model', 'model')],
    hiddenimports=['flask_sqlalchemy', 'flask_cors', 'sqlalchemy', 'requests', 'python-dotenv', 'openai', 'easyocr', 'PIL', 'dashscope'],
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
    name='智能日历',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
