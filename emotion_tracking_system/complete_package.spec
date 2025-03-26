# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['C:\\Users\\matteozanzico\\Desktop\\project\\emotion_tracking_system'],
    binaries=[],
    datas=[('images', 'images')],
    hiddenimports=[
        'cv2', 'cv2.cv2',
        'numpy',
        'websocket', 'websocket._app', '_websocket',
        'websockets', 'websockets.legacy', 'websockets.legacy.server', 'websockets.server',
        'PIL', 'PIL._imaging', 'PIL.Image', 'PIL.ImageTk', 'PIL.ImageDraw', 'PIL.ImageFont',
        'pandas', 'tkinter', 'asyncio', 'json', 'logging', 'threading',
        'gaze_tracker', 'emotion_detector', 'image_manager', 'data_collector', 'ui_manager', 'websocket_bridge',
        'collections', 'config'
    ],
    hookspath=['.'],
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
    [],
    exclude_binaries=True,
    name='emotion_tracker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Keep True for debugging
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='emotion_tracker',
)