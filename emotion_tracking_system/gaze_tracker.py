"""
Handles connection and data from GazePointer via WebSocket.
"""

import json
import threading
import time
import websocket
import logging
from config import GAZE_POINTER_HOST, GAZE_POINTER_PORT, GAZE_POINTER_APP_KEY

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GazeTracker:
    """
    Connects to GazePointer WebSocket and processes gaze data.
    """
    
    def __init__(self):
        """Initialize the gaze tracker."""
        self.ws = None
        self.connected = False
        self.gaze_data = {
            "GazeX": 0,
            "GazeY": 0,
            "HeadX": 0,
            "HeadY": 0,
            "HeadZ": 0,
            "HeadYaw": 0,
            "HeadPitch": 0,
            "HeadRoll": 0
        }
        self.callbacks = []
        self.connection_thread = None
        
    def connect(self):
        """Connect to the GazePointer WebSocket server."""
        if self.connection_thread and self.connection_thread.is_alive():
            logger.info("Connection thread already running")
            return
            
        self.connection_thread = threading.Thread(target=self._connect_websocket)
        self.connection_thread.daemon = True
        self.connection_thread.start()
        
    def _connect_websocket(self):
        """Connect to WebSocket in a separate thread."""
        url = f"ws://{GAZE_POINTER_HOST}:{GAZE_POINTER_PORT}"
        logger.info(f"Connecting to GazePointer at {url}")
        
        try:
            # Configure WebSocket callbacks
            websocket.enableTrace(False)
            self.ws = websocket.WebSocketApp(
                url,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close
            )
            
            # Start WebSocket connection
            self.ws.run_forever()
        
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
            self.connected = False
    
    def _on_open(self, ws):
        """Called when the WebSocket connection is opened."""
        logger.info("WebSocket connection opened")
        ws.send(GAZE_POINTER_APP_KEY)
    
    def _on_message(self, ws, message):
        """Process incoming WebSocket messages."""
        if not self.connected:
            # First message is the connection status
            if message.startswith("ok"):
                logger.info(f"Connection authorized: {message}")
                self.connected = True
            else:
                logger.error(f"Connection not authorized: {message}")
                ws.close()
            return
        
        try:
            # Parse gaze data
            self.gaze_data = json.loads(message)
            
            # Extract facial expression data if available
            self.extract_emotion_data()
            
            # Notify callbacks
            for callback in self.callbacks:
                callback(self.gaze_data)
                
        except json.JSONDecodeError:
            logger.error(f"Failed to parse gaze data: {message}")
    
    def extract_emotion_data(self):
        """Extract emotion data from GazePointer data if available."""
        # Initialize emotion fields if they don't exist
        if 'emotion_scores' not in self.gaze_data:
            self.gaze_data['emotion_scores'] = {
                "happy": 0,
                "sad": 0,
                "angry": 0,
                "surprise": 0,
                "fear": 0,
                "disgust": 0,
                "neutral": 1
            }
            self.gaze_data['emotion'] = "neutral"
        
        # Check for direct emotion fields (Format 1)
        emotion_found = False
        emotion_map = {
            'Happy': 'happy',
            'Sad': 'sad',
            'Angry': 'angry',
            'Surprised': 'surprise',
            'Neutral': 'neutral',
            'Fear': 'fear',
            'Disgust': 'disgust'
        }
        
        # Try to find emotion data in different possible formats
        emotions_data = {}
        
        # Format 1: Direct emotion fields
        for gaze_key, our_key in emotion_map.items():
            if gaze_key in self.gaze_data:
                emotions_data[our_key] = self.gaze_data[gaze_key]
                emotion_found = True
        
        # Format 2: Nested emotions object
        if 'Emotions' in self.gaze_data and isinstance(self.gaze_data['Emotions'], dict):
            for gaze_key, our_key in emotion_map.items():
                if gaze_key in self.gaze_data['Emotions']:
                    emotions_data[our_key] = self.gaze_data['Emotions'][gaze_key]
                    emotion_found = True
        
        # Format 3: FacialExpressions object
        if 'FacialExpressions' in self.gaze_data and isinstance(self.gaze_data['FacialExpressions'], dict):
            for gaze_key, our_key in emotion_map.items():
                if gaze_key in self.gaze_data['FacialExpressions']:
                    emotions_data[our_key] = self.gaze_data['FacialExpressions'][gaze_key]
                    emotion_found = True
        
        # Format 4: Alternative expression fields that might indicate emotions
        expression_fields = {
            'Smile': 'happy',
            'Frown': 'sad',
            'MouthOpen': 'surprise',
            'EyebrowRaise': 'surprise',
            'BrowFurrow': 'angry'
        }
        
        for field, emotion in expression_fields.items():
            if field in self.gaze_data and not emotion_found:
                value = self.gaze_data[field]
                if isinstance(value, (int, float)) and value > 0.5:
                    emotions_data[emotion] = value
                    emotion_found = True
        
        # If we found any emotions, update our data
        if emotion_found and emotions_data:
            # Update emotion scores
            for emotion, value in emotions_data.items():
                self.gaze_data['emotion_scores'][emotion] = value
            
            # Determine dominant emotion
            dominant_emotion = max(emotions_data.items(), key=lambda x: x[1])[0] if emotions_data else "neutral"
            self.gaze_data['emotion'] = dominant_emotion
            
            logger.debug(f"Detected emotion from GazePointer: {dominant_emotion}")
        
        # Ensure we have face_detected field
        self.gaze_data['face_detected'] = self.gaze_data.get('face_detected', True)
    
    def _on_error(self, ws, error):
        """Handle WebSocket errors."""
        logger.error(f"WebSocket error: {error}")
        self.connected = False
    
    def _on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close."""
        logger.info(f"WebSocket connection closed: {close_msg if close_msg else 'No message'}")
        self.connected = False
    
    def register_callback(self, callback):
        """Register a callback to be called when new gaze data arrives."""
        if callback not in self.callbacks:
            self.callbacks.append(callback)
    
    def unregister_callback(self, callback):
        """Remove a previously registered callback."""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def get_current_gaze(self):
        """Get the current gaze data."""
        return self.gaze_data
    
    def disconnect(self):
        """Disconnect from the WebSocket server."""
        if self.ws:
            self.ws.close()
        self.connected = False
        logger.info("Disconnected from GazePointer")