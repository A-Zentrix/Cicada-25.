#!/usr/bin/env python3
"""
Test script for conversation logging
This script tests the conversation logging functionality
"""

import os
import time
from main import log_conversation, read_current_emotion

def test_conversation_logging():
    """Test the conversation logging system"""
    print("Testing Conversation Logging System")
    print("=" * 50)
    
    # Test 1: Test basic conversation logging
    print("\n1. Testing basic conversation logging...")
    log_conversation("Hello, how are you?", "I'm doing well, thank you for asking!")
    print("   Basic conversation logged")
    
    # Test 2: Test conversation logging with emotion
    print("\n2. Testing conversation logging with emotion...")
    log_conversation("I'm feeling sad today", "I understand you're feeling sad. Let's talk about what's on your mind.", "sad")
    print("   Conversation with emotion logged")
    
    # Test 3: Test different types of conversations
    print("\n3. Testing different conversation types...")
    conversations = [
        ("[Voice] Tell me a joke", "Why don't scientists trust atoms? Because they make up everything!", "happy"),
        ("[Emotion Detection] I'm feeling angry", "I can see you're feeling angry. Let's work through this together.", "angry"),
        ("[AI with Emotion] Help me relax", "Since you're feeling stressed, let's try some deep breathing exercises.", "stressed"),
        ("What's the weather like?", "I don't have access to real-time weather data, but I'm here to help with your mental wellness!", None)
    ]
    
    for user_msg, ai_response, emotion in conversations:
        log_conversation(user_msg, ai_response, emotion)
        print(f"   Logged: {user_msg[:30]}...")
        time.sleep(0.1)  # Small delay between logs
    
    # Test 4: Check if conversation file was created
    print("\n4. Checking conversation file...")
    conversation_file = "conversation_log.txt"
    if os.path.exists(conversation_file):
        with open(conversation_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        print(f"   Conversation file created with {len(lines)} lines")
        print(f"   File size: {len(content)} characters")
        
        # Show first few lines
        print("   First few lines of conversation log:")
        for i, line in enumerate(lines[:10]):
            if line.strip():
                print(f"     {i+1}: {line}")
    else:
        print("   ERROR: Conversation file not found!")
    
    # Test 5: Test emotion reading
    print("\n5. Testing emotion reading...")
    current_emotion = read_current_emotion()
    print(f"   Current emotion: {current_emotion}")
    
    # Test 6: Test conversation with current emotion
    print("\n6. Testing conversation with current emotion...")
    if current_emotion:
        log_conversation(f"Based on my current emotion ({current_emotion}), what should I do?", 
                        f"Since you're feeling {current_emotion}, I recommend taking some time to process your emotions.", 
                        current_emotion)
        print("   Conversation with current emotion logged")
    else:
        print("   No current emotion detected, skipping emotion-based conversation test")
    
    print("\nTest completed!")
    print(f"\nConversation log saved to: {conversation_file}")
    print("You can download this file using the 'Download Conversation' button in the web interface.")

if __name__ == "__main__":
    test_conversation_logging()
