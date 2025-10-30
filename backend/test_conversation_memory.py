#!/usr/bin/env python3
"""
Test script for conversation memory functionality
This script tests the AI's ability to remember previous conversations
"""

import time
import os
import json
from main import bot, load_conversation_memory, get_conversation_context, add_to_memory

def test_conversation_memory():
    """Test the conversation memory system"""
    print("Testing Conversation Memory System")
    print("=" * 50)
    
    # Load existing memory
    load_conversation_memory()
    
    # Test 1: Test basic conversation memory
    print("\n1. Testing basic conversation memory...")
    
    # Simulate a conversation
    conversations = [
        ("My name is John", "Nice to meet you, John! I'm here to support your mental wellness."),
        ("I'm feeling stressed about work", "I understand work stress can be overwhelming. Let's talk about what's bothering you."),
        ("I have a big presentation tomorrow", "Presentations can be nerve-wracking. Would you like some tips to prepare?"),
        ("What's my name?", "Your name is John, and you mentioned you have a presentation tomorrow that's causing stress."),
        ("How can I relax?", "Since you're stressed about tomorrow's presentation, try deep breathing exercises or visualization techniques.")
    ]
    
    for user_msg, expected_context in conversations:
        print(f"\n   User: {user_msg}")
        
        # Get AI response (this will use memory)
        response = bot(user_msg)
        print(f"   AI: {response}")
        
        # Add to memory manually for testing
        add_to_memory(user_msg, response)
        
        # Show current memory context
        context = get_conversation_context()
        print(f"   Memory Context: {len(context)} characters")
        
        time.sleep(0.5)  # Small delay between conversations
    
    # Test 2: Test memory persistence
    print("\n2. Testing memory persistence...")
    
    # Clear current memory and reload
    global conversation_memory
    conversation_memory = []
    
    # Add some test conversations
    test_conversations = [
        ("I like pizza", "Pizza is great! What's your favorite topping?"),
        ("I prefer pepperoni", "Pepperoni is a classic choice! I'll remember that."),
        ("What's my favorite pizza?", "You mentioned you prefer pepperoni pizza!"),
    ]
    
    for user_msg, response in test_conversations:
        add_to_memory(user_msg, response)
        print(f"   Added: {user_msg} -> {response}")
    
    # Test memory context
    context = get_conversation_context()
    print(f"\n   Memory context length: {len(context)} characters")
    print(f"   Memory entries: {len(conversation_memory)}")
    
    # Test 3: Test memory file
    print("\n3. Testing memory file...")
    memory_file = "conversation_memory.json"
    if os.path.exists(memory_file):
        with open(memory_file, 'r', encoding='utf-8') as f:
            memory_data = json.load(f)
        print(f"   Memory file contains {len(memory_data)} entries")
        print(f"   Last entry: {memory_data[-1]['user']} -> {memory_data[-1]['ai']}")
    else:
        print("   Memory file not found")
    
    # Test 4: Test AI with memory
    print("\n4. Testing AI responses with memory...")
    
    # Test questions that should use memory
    memory_questions = [
        "What do you know about me?",
        "What did I tell you about my preferences?",
        "Can you remind me what we discussed?",
        "What's my favorite food?"
    ]
    
    for question in memory_questions:
        print(f"\n   Question: {question}")
        response = bot(question)
        print(f"   AI Response: {response}")
        time.sleep(0.5)
    
    # Test 5: Test memory overflow (keep only last 20)
    print("\n5. Testing memory overflow...")
    
    # Add many conversations to test overflow
    for i in range(25):
        add_to_memory(f"Test message {i}", f"Test response {i}")
    
    print(f"   Memory entries after overflow test: {len(conversation_memory)}")
    print(f"   Should be 20 (limited by overflow protection)")
    
    # Test 6: Test conversation context
    print("\n6. Testing conversation context...")
    context = get_conversation_context()
    print(f"   Context preview: {context[:200]}...")
    
    print("\nTest completed!")
    print("\nThe AI should now remember previous conversations and provide contextual responses.")
    print("Try asking questions like 'What did we talk about?' or 'What's my name?'")

if __name__ == "__main__":
    test_conversation_memory()
