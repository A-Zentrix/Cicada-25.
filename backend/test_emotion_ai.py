#!/usr/bin/env python3
"""
Test script for emotion-integrated AI responses
This script tests the AI's ability to read emotions from the file and respond accordingly
"""

import time
import os
from main import read_current_emotion, bot

def test_emotion_ai_integration():
    """Test the emotion-integrated AI system"""
    print("Testing Emotion-Integrated AI System")
    print("=" * 50)
    
    # Test 1: Check if emotion file exists and read current emotion
    print("\n1. Testing emotion file reading...")
    current_emotion = read_current_emotion()
    print(f"   Current emotion from file: {current_emotion}")
    
    if not current_emotion:
        print("   No emotion detected. Please ensure background emotion detection is running.")
        print("   Creating a test emotion file...")
        
        # Create a test emotion file
        with open("emotion_log.txt", "w") as f:
            f.write("Current_Emotion\n")
            f.write("happy\n")
        print("   Test emotion file created with 'happy' emotion")
        current_emotion = read_current_emotion()
        print(f"   Current emotion after creating test file: {current_emotion}")
    
    # Test 2: Test AI response with emotion context
    print("\n2. Testing AI response with emotion context...")
    try:
        response = bot("Hello, how are you?")
        print(f"   AI Response: {response}")
        print(f"   (This response should be influenced by the current emotion: {current_emotion})")
    except Exception as e:
        print(f"   Error getting AI response: {e}")
    
    # Test 3: Test different emotions
    print("\n3. Testing AI responses with different emotions...")
    test_emotions = ["sad", "angry", "neutral", "surprise"]
    
    for emotion in test_emotions:
        print(f"\n   Testing with emotion: {emotion}")
        
        # Update emotion file
        with open("emotion_log.txt", "w") as f:
            f.write("Current_Emotion\n")
            f.write(f"{emotion}\n")
        
        # Wait a moment for file to be written
        time.sleep(0.5)
        
        # Test AI response
        try:
            response = bot("I need some advice")
            print(f"   AI Response: {response}")
        except Exception as e:
            print(f"   Error: {e}")
    
    # Test 4: Test without emotion
    print("\n4. Testing AI response without emotion...")
    try:
        # Clear emotion file
        with open("emotion_log.txt", "w") as f:
            f.write("Current_Emotion\n")
        
        response = bot("Tell me something positive")
        print(f"   AI Response (no emotion): {response}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 5: Test emotion reading function
    print("\n5. Testing emotion reading function...")
    test_emotions = ["happy", "sad", "angry", "neutral", "fear", "surprise", "disgust"]
    
    for emotion in test_emotions:
        with open("emotion_log.txt", "w") as f:
            f.write("Current_Emotion\n")
            f.write(f"{emotion}\n")
        
        time.sleep(0.1)
        read_emotion = read_current_emotion()
        print(f"   Set: {emotion}, Read: {read_emotion}, Match: {emotion == read_emotion}")
    
    print("\nTest completed!")
    print("\nNote: The AI responses should show different tones and approaches based on the detected emotion.")
    print("For example:")
    print("- 'happy' emotion should get more celebratory responses")
    print("- 'sad' emotion should get more comforting responses")
    print("- 'angry' emotion should get more calming responses")

if __name__ == "__main__":
    test_emotion_ai_integration()
