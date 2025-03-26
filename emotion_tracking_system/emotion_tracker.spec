
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# In your simplified.spec file:
a = Analysis(
    ['main.py'],
    pathex=['C:\\Users\\matteozanzico\\Desktop\\project\\emotion_tracking_system'],
    binaries=[],
    datas=[('images', 'images')],
    hiddenimports=[
        'cv2', 
        'cv2.cv2',
        'numpy',
        'websocket',
        'websocket-client',
        'PIL',
        'PIL._imaging',
        'PIL.Image',
        'PIL.ImageDraw',
        'PIL.ImageFont'
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='emotion_tracker_backend',
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
