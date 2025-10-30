import cv2
import time
import os

# Lazy imports - only load when needed
DeepFace = None

def load_deepface():
    """Load DeepFace only when needed"""
    global DeepFace
    if DeepFace is None:
        from deepface import DeepFace as DeepFaceModule
        DeepFace = DeepFaceModule

def face():
    """
    Detect emotion from camera feed using DeepFace
    Returns the dominant emotion or None if detection fails
    """
    # Load DeepFace if not already loaded
    load_deepface()
    
    cap = None
    try:
        # Load Camera
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("Error: Could not open camera. Please check camera permissions.")
            return None
        
        # Set camera properties for better performance
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        # Note: CAP_PROP_FPS is the correct property for frame rate
        
        # Load face cascade classifier
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        if face_cascade.empty():
            print("Error: Could not load face detection model")
            return None
        
        # Try to detect emotion for a few frames
        max_attempts = 5
        attempt = 0
        
        while attempt < max_attempts:
            ret, frame = cap.read()
            if not ret:
                print("Warning: Could not read frame from camera")
                attempt += 1
                time.sleep(0.1)  # Small delay to prevent blocking
                continue
            
            try:
                # Detect faces first
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                
                if len(faces) == 0:
                    print("Info: No face detected. Please position your face in the camera view.")
                    attempt += 1
                    time.sleep(0.5)  # Delay between attempts
                    continue
                
                # Analyze emotion using DeepFace with timeout
                try:
                    result = DeepFace.analyze(
                        frame,
                        actions=['emotion'],
                        detector_backend='opencv',
                        enforce_detection=False
                    )
                    
                    if result and len(result) > 0:
                        result = result[0]
                        dominant_emotion = result.get('dominant_emotion', 'unknown')
                        
                        # Draw face rectangle and emotion text on frame
                        for (x, y, w, h) in faces:
                            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        
                        font = cv2.FONT_HERSHEY_SIMPLEX
                        cv2.putText(frame, dominant_emotion, (10, 50), font, 1, (0, 255, 0), 2, cv2.LINE_AA)
                        
                        # Show the frame briefly (non-blocking)
                        try:
                            cv2.imshow('Emotion Detection', frame)
                            cv2.waitKey(500)  # Show for 0.5 seconds
                        except:
                            pass  # Ignore display errors in headless environments
                        
                        return dominant_emotion
                    
                except Exception as deepface_error:
                    print(f"Warning: DeepFace analysis failed: {str(deepface_error)}")
                    attempt += 1
                    time.sleep(0.5)
                    continue
                
            except Exception as e:
                print(f"Warning: Face analysis attempt {attempt + 1} failed: {str(e)}")
                attempt += 1
                time.sleep(0.5)
                continue
            
            attempt += 1
        
        print("Warning: Could not detect emotion after multiple attempts. Please try again.")
        return None
        
    except Exception as e:
        print(f"Error: Camera error: {str(e)}")
        return None
    
    finally:
        # Clean up
        if cap is not None:
            cap.release()
        try:
            cv2.destroyAllWindows()
        except:
            pass  # Ignore cleanup errors