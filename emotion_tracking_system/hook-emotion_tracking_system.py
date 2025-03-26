# hook-emotion_tracking_system.py
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

hiddenimports = [
    'websockets', 
    'asyncio', 
    'cv2', 
    'numpy', 
    'pandas', 
    'PIL',
    'PIL.Image',
    'websockets.legacy', 
    'websockets.legacy.server',
    'encodings.idna',
    'logging.handlers',
    'threading',
    'time',
    'gaze_tracker',
    'emotion_detector',
    'image_manager',
    'data_collector',
    'ui_manager',
    'websocket_bridge'
]

# Add any data files your package needs
datas = collect_data_files('emotion_tracking_system')
datas += [('images', 'images')]