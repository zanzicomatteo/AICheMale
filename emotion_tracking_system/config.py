"""
Configuration settings for the emotion tracking system.
"""

# GazePointer WebSocket settings
GAZE_POINTER_HOST = "127.0.0.1"
GAZE_POINTER_PORT = 43333
GAZE_POINTER_APP_KEY = "AppKeyTrial"  # Register at http://gazeflow.epizy.com/GazeFlowAPI/register/ for a real key

# UI settings
WINDOW_TITLE = "Emotion Tracking"
WINDOW_WIDTH = 1920
WINDOW_HEIGHT = 1080
IMAGE_WIDTH = 900
IMAGE_HEIGHT = 700
DISPLAY_TIME_PER_PAIR = 10  # seconds to display each image pair

# Emotion detection settings
EMOTION_DETECTION_INTERVAL = 0.5  # seconds between emotion detections
WEBCAM_INDEX = 0  # index of webcam to use

# Paths
IMAGE_DIR = "images"
EMOTION_CATEGORIES = ["happy", "sad", "angry", "neutral", "surprise", "fear", "disgust"]

# Data collection settings
GAZE_THRESHOLD = 0.1  # minimum time (seconds) to consider a gaze fixation
RESULT_DISPLAY_TIME = 30  # seconds to display results at the end