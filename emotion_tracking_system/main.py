"""
Main entry point for the Emotion Tracking System.
"""

import logging
import time
import threading
from gaze_tracker import GazeTracker
from emotion_detector import EmotionDetector
from image_manager import ImageManager
from data_collector import DataCollector
from ui_manager import UIManager
from websocket_bridge import start_bridge_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("emotion_tracking.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main function to run the Emotion Tracking System."""
    logger.info("Starting Emotion Tracking System")
    
    try:
        # Configure logging for debugging
        logging.getLogger('gaze_tracker').setLevel(logging.DEBUG)
        logging.getLogger('emotion_detector').setLevel(logging.DEBUG)
        logging.getLogger('data_collector').setLevel(logging.DEBUG)
        
        # Initialize components
        logger.info("Initializing components...")
        
        # Initialize image manager
        image_manager = ImageManager()
        if not image_manager.load_images():
            logger.error("Failed to load images. Please check image directory.")
            return
        
        # Initialize data collector
        data_collector = DataCollector()
        
        # Initialize UI manager
        ui_manager = UIManager(image_manager, data_collector)
        
        # Initialize gaze tracker
        gaze_tracker = GazeTracker()
        
        # Register gaze tracker callback
        def gaze_callback(gaze_data):
            data_collector.add_gaze_sample(gaze_data)
            ui_manager.update_gaze_display(gaze_data)
            
            # If GazePointer provides emotion data, use it instead of our own detection
            if 'emotion' in gaze_data and 'emotion_scores' in gaze_data:
                # Only use if face is detected and emotion is not neutral (our default)
                if gaze_data.get('face_detected', True) and gaze_data.get('emotion') != 'neutral':
                    # Create emotion data in the format our system expects
                    emotion_data = {
                        'emotion': gaze_data['emotion'],
                        'emotion_scores': gaze_data['emotion_scores'],
                        'face_detected': gaze_data.get('face_detected', True),
                        'timestamp': time.time(),
                        'source': 'gazepointer'  # Mark as coming from GazePointer
                    }
                    data_collector.add_emotion_sample(emotion_data)
                    ui_manager.update_emotion_display(emotion_data)
        
        gaze_tracker.register_callback(gaze_callback)
        
        # Initialize emotion detector
        emotion_detector = EmotionDetector()
        
        # Register emotion detector callback
        def emotion_callback(emotion_data):
            data_collector.add_emotion_sample(emotion_data)
            ui_manager.update_emotion_display(emotion_data)
        
        emotion_detector.register_callback(emotion_callback)
        
        # Start WebSocket bridge in a separate thread
        logger.info("Starting WebSocket bridge...")
        bridge_thread = threading.Thread(
            target=start_bridge_server,
            args=(gaze_tracker, emotion_detector),
            daemon=True
        )
        bridge_thread.start()
        logger.info("WebSocket bridge started")
        
        # Start components
        logger.info("Starting components...")
        
        # Start gaze tracker
        gaze_tracker.connect()
        
        # Start emotion detector
        emotion_detector.start()
        
        # Give components time to initialize
        time.sleep(1)
        
        # Start UI (this will block until UI is closed)
        ui_manager.start()
        
        # Cleanup
        logger.info("Shutting down components...")
        emotion_detector.stop()
        gaze_tracker.disconnect()
        
        logger.info("Emotion Tracking System terminated")
        
    except Exception as e:
        logger.error(f"Error in main function: {e}", exc_info=True)
        return

if __name__ == "__main__":
    main()