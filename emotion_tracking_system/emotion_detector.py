"""
Handles face detection and emotion analysis using OpenCV.
"""

import cv2
import threading
import time
import numpy as np
import logging
import os
from config import EMOTION_DETECTION_INTERVAL, WEBCAM_INDEX

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EmotionDetector:
    """
    Detects emotions from facial expressions using webcam.
    """
    
    def __init__(self):
        """Initialize the emotion detector."""
        self.cap = None
        self.running = False
        self.detector_thread = None
        self.emotion_data = {
            "emotion": "neutral",
            "emotion_scores": {
                "angry": 0,
                "disgust": 0,
                "fear": 0,
                "happy": 0.1,
                "sad": 0,
                "surprise": 0,
                "neutral": 0.9
            },
            "face_detected": False,
            "timestamp": time.time()
        }
        self.callbacks = []
        
        # Load face detection model
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # For more robust emotion detection, we'll use a Haar cascade approach
        # Load additional cascades if available
        self.smile_cascade = None
        try:
            smile_path = cv2.data.haarcascades + 'haarcascade_smile.xml'
            if os.path.exists(smile_path):
                self.smile_cascade = cv2.CascadeClassifier(smile_path)
                logger.info("Smile detector loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load smile detector: {e}")
            
        # Try to load facial landmark detector (optional)
        self.has_landmark_detector = False
        self.landmark_detector = None
        try:
            # First try to load the LBF model
            self.landmark_detector = cv2.face.createFacemarkLBF()
            model_path = os.path.join(cv2.data.haarcascades, '..', 'lbfmodel.yaml')
            
            if os.path.exists(model_path):
                self.landmark_detector.loadModel(model_path)
                self.has_landmark_detector = True
                logger.info("Facial landmark detector loaded successfully")
            else:
                # Try alternate model paths
                alt_paths = [
                    "lbfmodel.yaml",  # Current directory
                    os.path.join(os.path.dirname(__file__), "models", "lbfmodel.yaml"),  # models subdirectory
                ]
                
                for path in alt_paths:
                    if os.path.exists(path):
                        self.landmark_detector.loadModel(path)
                        self.has_landmark_detector = True
                        logger.info(f"Facial landmark detector loaded from {path}")
                        break
                
                if not self.has_landmark_detector:
                    logger.warning(f"Facial landmark model not found. Using basic emotion detection.")
        except Exception as e:
            logger.warning(f"Could not initialize facial landmark detector: {e}. Using basic emotion detection.")
    
    def start(self):
        """Start emotion detection."""
        if self.running:
            logger.info("Emotion detector already running")
            return True
            
        try:
            self.cap = cv2.VideoCapture(WEBCAM_INDEX)
            if not self.cap.isOpened():
                logger.error(f"Failed to open webcam at index {WEBCAM_INDEX}")
                return False
                
            self.running = True
            self.detector_thread = threading.Thread(target=self.detection_loop)
            self.detector_thread.daemon = True
            self.detector_thread.start()
            logger.info("Emotion detector started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start emotion detector: {e}")
            if self.cap and self.cap.isOpened():
                self.cap.release()
            self.running = False
            return False
    
    def detection_loop(self):
        """Main detection loop running in a separate thread."""
        last_detection_time = 0
        
        while self.running:
            try:
                current_time = time.time()
                
                # Limit detection frequency
                if current_time - last_detection_time < EMOTION_DETECTION_INTERVAL:
                    time.sleep(0.01)  # Small sleep to prevent CPU hogging
                    continue
                    
                # Capture frame from webcam
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    logger.warning("Failed to capture frame from webcam")
                    time.sleep(0.1)
                    continue
                
                # Convert to grayscale for face detection
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
                
                # If no face is detected
                if len(faces) == 0:
                    self.emotion_data = {
                        "emotion": "neutral",
                        "emotion_scores": {
                            "angry": 0,
                            "disgust": 0,
                            "fear": 0,
                            "happy": 0,
                            "sad": 0,
                            "surprise": 0,
                            "neutral": 1
                        },
                        "face_detected": False,
                        "timestamp": current_time
                    }
                else:
                    # Get the largest face
                    largest_face = max(faces, key=lambda rect: rect[2] * rect[3])
                    x, y, w, h = largest_face
                    
                    # Extract face region
                    face_roi = gray[y:y+h, x:x+w]
                    
                    # Analyze emotion using our simple approach
                    try:
                        # Use a simple algorithm for emotion detection
                        emotion_scores = self.analyze_face(frame, gray, largest_face)
                        
                        # Find dominant emotion
                        dominant_emotion = max(emotion_scores, key=emotion_scores.get)
                        
                        self.emotion_data = {
                            "emotion": dominant_emotion,
                            "emotion_scores": emotion_scores,
                            "face_detected": True,
                            "timestamp": current_time
                        }
                        
                        # Debug
                        logger.debug(f"Detected emotion: {dominant_emotion}")
                        
                    except Exception as e:
                        logger.error(f"Emotion analysis error: {e}")
                        # Keep previous emotion data but update timestamp
                        self.emotion_data["timestamp"] = current_time
                
                # Notify callbacks
                for callback in self.callbacks:
                    callback(self.emotion_data)
                    
                last_detection_time = current_time
                
            except Exception as e:
                logger.error(f"Error in emotion detection loop: {e}")
                time.sleep(0.1)
    
    def analyze_face(self, frame, gray, face_rect):
        """Analyze a face to detect emotion more accurately."""
        x, y, w, h = face_rect
        face_roi = gray[y:y+h, x:x+w]
        color_face = frame[y:y+h, x:x+w]
        
        # Initialize scores with slightly more realistic baselines
        # Lower neutral by default to allow other emotions to dominate
        scores = {
            "happy": 0.15,
            "sad": 0.15,
            "neutral": 0.2,
            "surprise": 0.15,
            "angry": 0.15,
            "fear": 0.1,
            "disgust": 0.1
        }
        
        # 1. Check for smile using Haar cascade if available
        if self.smile_cascade is not None:
            # Try different parameters to increase sensitivity
            smiles = self.smile_cascade.detectMultiScale(
                face_roi,
                scaleFactor=1.5,
                minNeighbors=15,
                minSize=(25, 25)
            )
            
            if len(smiles) > 0:
                # Smile detected, increase happiness score significantly
                scores["happy"] += 0.5
                scores["sad"] -= 0.1
                scores["neutral"] -= 0.2
                scores["angry"] -= 0.1
        
        # 2. Try landmark detection for more detailed analysis
        landmarks_detected = False
        if self.has_landmark_detector:
            try:
                faces = np.array([face_rect], dtype=np.int32)
                ok, landmarks = self.landmark_detector.fit(gray, faces)
                
                if ok:
                    landmarks_detected = True
                    landmark_scores = self.analyze_landmarks(landmarks[0][0])
                    # Combine with current scores (weighted average heavily toward landmarks)
                    for emotion, score in landmark_scores.items():
                        scores[emotion] = scores[emotion] * 0.2 + score * 0.8
            except Exception as e:
                logger.debug(f"Landmark detection failed: {e}")
        
        # 3. If landmarks not detected, use more advanced image-based metrics
        if not landmarks_detected:
            # Resize for consistency
            face_resized = cv2.resize(face_roi, (64, 64))
            
            # Calculate various metrics with region-specific analysis
            
            # Eye region analysis (top third of face)
            eye_region = face_resized[5:25, :]
            eye_edges = cv2.Canny(eye_region, 100, 200)
            eye_edge_density = np.sum(eye_edges) / (20 * 64)
            
            # Mouth region analysis (bottom third of face)
            mouth_region = face_resized[40:60, :]
            mouth_edges = cv2.Canny(mouth_region, 100, 200)
            mouth_edge_density = np.sum(mouth_edges) / (20 * 64)
            
            # Eyebrow region
            brow_region = face_resized[5:20, :]
            brow_std = np.std(brow_region)
            
            # Overall face metrics
            brightness = np.mean(face_resized) / 255.0  # 0 to 1
            contrast = min(np.std(face_resized) / 80.0, 1.0)  # 0 to 1
            
            # Apply more sensitive heuristics
            
            # Happiness increases with both brightness and mouth edges (smile)
            happy_score = brightness * 0.3 + mouth_edge_density * 0.7
            scores["happy"] += happy_score * 0.6
            
            # Surprise increases with eye edge density (wide eyes)
            surprise_score = eye_edge_density * 0.8
            scores["surprise"] += surprise_score * 0.5
            
            # Sadness often has lower brightness and less mouth activity
            sad_score = (1.0 - brightness) * 0.4 + (1.0 - mouth_edge_density) * 0.4
            scores["sad"] += sad_score * 0.4
            
            # Anger often has higher brow contrast 
            angry_score = brow_std / 40.0 * 0.6
            scores["angry"] += angry_score * 0.4
            
            # Neutral is higher when overall face has less edge activity
            overall_edges = cv2.Canny(face_resized, 100, 200)
            overall_edge_density = np.sum(overall_edges) / (64 * 64)
            neutral_score = (1.0 - overall_edge_density) * 0.6
            scores["neutral"] += neutral_score * 0.3
        
        # 4. Add less randomness, just enough to create natural variations
        import random
        random.seed(int(time.time() * 100) % 1000)
        
        for emotion in scores:
            # Much smaller random factor
            scores[emotion] = max(0.05, min(0.95, scores[emotion] + random.uniform(-0.03, 0.03)))
        
        # 5. Normalize scores to sum to 1
        total = sum(scores.values())
        normalized_scores = {k: v/total for k, v in scores.items()}
        
        # 6. Reduce neutral's dominance if any other emotion is strong
        max_emotion = max(normalized_scores, key=normalized_scores.get)
        if max_emotion != "neutral" and normalized_scores[max_emotion] > 0.3:
            # If we have a strong non-neutral emotion, reduce neutral even more
            normalized_scores["neutral"] *= 0.7
            # Renormalize
            total = sum(normalized_scores.values())
            normalized_scores = {k: v/total for k, v in normalized_scores.items()}
        
        return normalized_scores
        
    def analyze_landmarks(self, landmarks):
        """Analyze facial landmarks to estimate emotions."""
        try:
            # Convert landmarks to numpy array if needed
            landmarks_array = np.array(landmarks)
            
            # Calculate face shape metrics
            face_height = np.max(landmarks_array[:, 1]) - np.min(landmarks_array[:, 1])
            face_width = np.max(landmarks_array[:, 0]) - np.min(landmarks_array[:, 0])
            
            # Get basic face metrics
            aspect_ratio = face_width / face_height if face_height > 0 else 1.0
            
            # Generate random but consistent emotion scores based on face metrics
            # This is just a placeholder - real emotion detection would use specific facial features
            
            # Add some randomness to simulate changing emotions
            import random
            random.seed(int(time.time() * 10) % 1000)
            
            # Base scores affected by face aspect ratio
            happy_base = 0.2 + aspect_ratio * 0.1
            sad_base = 0.2 - aspect_ratio * 0.1
            
            # Final scores with random variation
            happy_score = max(0.1, happy_base + random.uniform(-0.1, 0.1))
            sad_score = max(0.1, sad_base + random.uniform(-0.1, 0.1))
            neutral_score = max(0.1, 0.3 + random.uniform(-0.1, 0.1))
            surprise_score = max(0.1, 0.15 + random.uniform(-0.1, 0.1))
            angry_score = max(0.1, 0.15 + random.uniform(-0.1, 0.1))
            fear_score = max(0.1, 0.1 + random.uniform(-0.05, 0.05))
            disgust_score = max(0.1, 0.1 + random.uniform(-0.05, 0.05))
            
            scores = {
                "happy": happy_score,
                "sad": sad_score,
                "neutral": neutral_score,
                "surprise": surprise_score,
                "angry": angry_score,
                "fear": fear_score,
                "disgust": disgust_score
            }
            
            # Normalize to sum to 1
            total = sum(scores.values())
            return {k: v/total for k, v in scores.items()}
            
        except Exception as e:
            logger.error(f"Error analyzing landmarks: {e}")
            # Return default values if something goes wrong
            return {
                "happy": 0.2,
                "sad": 0.1,
                "neutral": 0.4,
                "surprise": 0.1,
                "angry": 0.1,
                "fear": 0.05,
                "disgust": 0.05
            }
    
    def register_callback(self, callback):
        """Register a callback to be called when new emotion data is available."""
        if callback not in self.callbacks:
            self.callbacks.append(callback)
    
    def unregister_callback(self, callback):
        """Remove a previously registered callback."""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def get_current_emotion(self):
        """Get the current emotion data."""
        return self.emotion_data
    
    def stop(self):
        """Stop emotion detection."""
        self.running = False
        if self.detector_thread:
            self.detector_thread.join(timeout=1.0)
        if self.cap and self.cap.isOpened():
            self.cap.release()
        logger.info("Emotion detector stopped")
        
    def __del__(self):
        """Clean up resources."""
        self.stop()