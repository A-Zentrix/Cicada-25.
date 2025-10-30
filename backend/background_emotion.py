import cv2
import threading
import time
import os
from datetime import datetime
import logging

# Lazy imports - only load when needed
DeepFace = None

def load_deepface():
    """Load DeepFace only when needed"""
    global DeepFace
    if DeepFace is None:
        from deepface import DeepFace as DeepFaceModule
        DeepFace = DeepFaceModule

class BackgroundEmotionDetector:
    def __init__(self, detection_interval=5, log_file="emotion_log.txt", enabled=True):
        """
        Background emotion detection system
        
        Args:
            detection_interval (int): Time between emotion detection attempts in seconds
            log_file (str): Path to the text file where emotions will be stored
            enabled (bool): Whether the detector is enabled
        """
        self.detection_interval = detection_interval
        self.log_file = log_file
        self.enabled = enabled
        self.running = False
        self.thread = None
        self.cap = None
        self.face_cascade = None
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize face detection (lightweight operation)
        self._initialize_face_detection()
        
        # Create log file if it doesn't exist
        self._initialize_log_file()
    
    def _initialize_face_detection(self):
        """Initialize face cascade classifier"""
        try:
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            if self.face_cascade.empty():
                self.logger.error("Could not load face detection model")
                self.face_cascade = None
        except Exception as e:
            self.logger.error(f"Error initializing face detection: {e}")
            self.face_cascade = None
    
    def _initialize_log_file(self):
        """Create log file with header if it doesn't exist"""
        try:
            if not os.path.exists(self.log_file):
                with open(self.log_file, 'w') as f:
                    f.write("Current_Emotion\n")
                self.logger.info(f"Created emotion file: {self.log_file}")
        except Exception as e:
            self.logger.error(f"Error creating emotion file: {e}")
    
    def _log_emotion(self, emotion, confidence=None, face_detected=True):
        """Store current emotion (replace previous)"""
        try:
            # Only store the emotion name, replace the entire file content
            with open(self.log_file, 'w') as f:
                f.write(f"{emotion}\n")
            
            self.logger.info(f"Stored current emotion: {emotion}")
            
        except Exception as e:
            self.logger.error(f"Error storing emotion: {e}")
    
    def _detect_emotion_from_frame(self, frame):
        """Detect emotion from a single frame"""
        try:
            if self.face_cascade is None:
                return None, None, False
            
            # Convert to grayscale for face detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
            
            if len(faces) == 0:
                return None, None, False
            
            # Load DeepFace if not already loaded
            load_deepface()
            
            # Analyze emotion using DeepFace
            result = DeepFace.analyze(
                frame,
                actions=['emotion'],
                detector_backend='opencv',
                enforce_detection=False
            )
            
            if result and len(result) > 0:
                result = result[0]
                dominant_emotion = result.get('dominant_emotion', 'unknown')
                emotions = result.get('emotion', {})
                confidence = emotions.get(dominant_emotion, 0) if emotions else 0
                
                return dominant_emotion, confidence, True
            
            return None, None, True
            
        except Exception as e:
            self.logger.error(f"Error in emotion detection: {e}")
            return None, None, False
    
    def _detection_loop(self):
        """Main detection loop running in background thread"""
        self.logger.info("Background emotion detection started")
        
        try:
            # Initialize camera
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                self.logger.error("Could not open camera for background detection")
                return
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            consecutive_failures = 0
            max_consecutive_failures = 5
            
            while self.running and self.enabled:
                try:
                    ret, frame = self.cap.read()
                    if not ret:
                        consecutive_failures += 1
                        if consecutive_failures >= max_consecutive_failures:
                            self.logger.error("Too many consecutive camera read failures")
                            break
                        time.sleep(1)
                        continue
                    
                    # Reset failure counter on successful read
                    consecutive_failures = 0
                    
                    # Detect emotion
                    emotion, confidence, face_detected = self._detect_emotion_from_frame(frame)
                    
                    if emotion:
                        self._log_emotion(emotion, confidence, face_detected)
                    else:
                        # Log that no emotion was detected but face might be present
                        if face_detected:
                            self._log_emotion("unknown", 0, True)
                        else:
                            self._log_emotion("no_face", 0, False)
                    
                    # Wait for next detection
                    time.sleep(self.detection_interval)
                    
                except Exception as e:
                    self.logger.error(f"Error in detection loop: {e}")
                    time.sleep(self.detection_interval)
                    
        except Exception as e:
            self.logger.error(f"Fatal error in detection loop: {e}")
        finally:
            self._cleanup()
            self.logger.info("Background emotion detection stopped")
    
    def _cleanup(self):
        """Clean up resources"""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        try:
            cv2.destroyAllWindows()
        except:
            pass
    
    def start(self):
        """Start background emotion detection"""
        if self.running:
            self.logger.warning("Background emotion detection is already running")
            return
        
        if not self.enabled:
            self.logger.info("Background emotion detection is disabled")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._detection_loop, daemon=True)
        self.thread.start()
        self.logger.info("Background emotion detection started")
    
    def stop(self):
        """Stop background emotion detection"""
        if not self.running:
            self.logger.warning("Background emotion detection is not running")
            return
        
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        self._cleanup()
        self.logger.info("Background emotion detection stopped")
    
    def set_enabled(self, enabled):
        """Enable or disable emotion detection"""
        self.enabled = enabled
        if not enabled and self.running:
            self.stop()
        self.logger.info(f"Background emotion detection {'enabled' if enabled else 'disabled'}")
    
    def set_detection_interval(self, interval):
        """Set detection interval in seconds"""
        self.detection_interval = max(1, interval)  # Minimum 1 second
        self.logger.info(f"Detection interval set to {self.detection_interval} seconds")
    
    def get_status(self):
        """Get current status of the detector"""
        return {
            "running": self.running,
            "enabled": self.enabled,
            "detection_interval": self.detection_interval,
            "log_file": self.log_file
        }
    
    def get_current_emotion(self):
        """Get current emotion from file"""
        try:
            if not os.path.exists(self.log_file):
                return None
            
            with open(self.log_file, 'r') as f:
                lines = f.readlines()
            
            # Skip header line and get the emotion
            if len(lines) > 1:
                emotion = lines[1].strip()
                return emotion if emotion else None
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error reading current emotion: {e}")
            return None

# Global instance for easy access
emotion_detector = BackgroundEmotionDetector()
