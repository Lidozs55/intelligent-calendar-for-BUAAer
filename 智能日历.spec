# -*- mode: python ; coding: utf-8 -*-


# 导入必要的模块
import os
import sys
import pathlib

# 获取当前目录
current_dir = pathlib.Path(__file__).parent

# 确保后端目录是当前目录
os.chdir(str(current_dir))

a = Analysis(
    ['run_app.py'],
    pathex=[str(current_dir)],
    binaries=[
        # 包含cpolar可执行文件
        (str(current_dir / 'cpolar' / 'cpolar.exe'), 'cpolar'),
        (str(current_dir / 'cpolar' / 'cpolar.exe'), '.'),
    ],
    datas=[
        # 包含前端构建文件
        (str(current_dir / 'frontend' / 'dist'), 'frontend/dist'),
        (str(current_dir / 'frontend' / 'public'), 'frontend/public'),
        # 包含配置文件
        (str(current_dir / 'backend' / 'config.py'), 'backend'),
        (str(current_dir / 'backend' / 'extensions.py'), 'backend'),
        # 包含路由和模型
        (str(current_dir / 'backend' / 'routes'), 'backend/routes'),
        (str(current_dir / 'backend' / 'models'), 'backend/models'),
        (str(current_dir / 'backend' / 'services'), 'backend/services'),
        (str(current_dir / 'backend' / 'utils'), 'backend/utils'),
        # 包含数据库初始化文件
        (str(current_dir / 'backend' / 'instance'), 'backend/instance'),
        # 包含OCR模型文件
        (str(current_dir / 'model'), 'model'),
    ],
    hiddenimports=[
        'flask_cors',
        'flask_sqlalchemy',
        'sqlalchemy',
        'requests',
        'python-dotenv',
        'openai',
        'easyocr',
        'PIL',
        'dashscope',
        'qrcode',
        'qrcode.image.svg',
        'qrcode.image.pil',
        'pysqlite3',
        'sqlite3',
    ],
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
