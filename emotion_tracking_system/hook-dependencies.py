# hook-dependencies.py
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_dynamic_libs

# Add all PIL modules
hiddenimports = collect_submodules('PIL')

# Add OpenCV
hiddenimports += ['cv2', 'cv2.cv2']

# Add all numpy modules
hiddenimports += collect_submodules('numpy')

# Add websocket
hiddenimports += ['websocket', '_websocket']

# Add pandas
hiddenimports += collect_submodules('pandas')

# Add our project modules
hiddenimports += [
    'gaze_tracker',
    'emotion_detector',
    'image_manager',
    'data_collector',
    'ui_manager',
    'websocket_bridge'
]

# Collect binaries
binaries = collect_dynamic_libs('cv2')
binaries += collect_dynamic_libs('PIL')

# Collect data files
datas = collect_data_files('PIL')
datas += [('images', 'images')]