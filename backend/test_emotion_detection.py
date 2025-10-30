#!/usr/bin/env python3
"""
Test script for background emotion detection
This script tests the background emotion detection functionality
"""

import time
import os
from background_emotion import BackgroundEmotionDetector

def test_emotion_detection():
    """Test the background emotion detection system"""
    print("Testing Background Emotion Detection System")
    print("=" * 50)
    
    # Create a test detector with shorter interval for testing
    detector = BackgroundEmotionDetector(
        detection_interval=3,  # 3 seconds for testing
        log_file="test_emotion_log.txt",
        enabled=True
    )
    
    print(f"Created detector with interval: {detector.detection_interval} seconds")
    print(f"Log file: {detector.log_file}")
    
    try:
        # Test 1: Check initial status
        print("\n1. Testing initial status...")
        status = detector.get_status()
        print(f"   Status: {status}")
        
        # Test 2: Start detection
        print("\n2. Starting emotion detection...")
        detector.start()
        print("   Detection started")
        
        # Test 3: Wait and check status
        print("\n3. Waiting 10 seconds and checking status...")
        time.sleep(10)
        status = detector.get_status()
        print(f"   Status after 10 seconds: {status}")
        
        # Test 4: Get current emotion
        print("\n4. Getting current emotion...")
        current = detector.get_current_emotion()
        print(f"   Current emotion: {current}")
        
        # Test 5: Test interval change
        print("\n5. Testing interval change...")
        detector.set_detection_interval(2)
        print("   Interval changed to 2 seconds")
        
        # Test 6: Wait and get current emotion again
        print("\n6. Waiting 8 seconds with new interval...")
        time.sleep(8)
        current = detector.get_current_emotion()
        print(f"   Current emotion after wait: {current}")
        
        # Test 7: Test disable/enable
        print("\n7. Testing disable/enable...")
        detector.set_enabled(False)
        print("   Disabled detection")
        time.sleep(3)
        detector.set_enabled(True)
        print("   Re-enabled detection")
        
        # Test 8: Final status check
        print("\n8. Final status check...")
        status = detector.get_status()
        print(f"   Final status: {status}")
        
        # Test 9: Check emotion file
        print("\n9. Checking emotion file...")
        if os.path.exists(detector.log_file):
            with open(detector.log_file, 'r') as f:
                lines = f.readlines()
            print(f"   Emotion file has {len(lines)} lines")
            if len(lines) > 1:
                print(f"   Current emotion in file: {lines[1].strip()}")
            else:
                print("   No emotion stored in file")
        else:
            print("   Emotion file not found")
        
    except Exception as e:
        print(f"Error during testing: {e}")
    
    finally:
        # Clean up
        print("\n10. Cleaning up...")
        detector.stop()
        print("   Detection stopped")
        
        # Remove test emotion file
        if os.path.exists("test_emotion_log.txt"):
            os.remove("test_emotion_log.txt")
            print("   Test emotion file removed")
    
    print("\nTest completed!")

if __name__ == "__main__":
    test_emotion_detection()
