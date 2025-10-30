#!/usr/bin/env python3
"""
Test script to verify startup optimizations
"""

import time
import sys
from pathlib import Path

def test_import_speed():
    """Test how fast the main module imports"""
    print("Testing import speed...")
    start_time = time.time()
    
    try:
        # Test importing main module
        import main
        import_time = time.time() - start_time
        print(f"✅ Main module imported in {import_time:.2f} seconds")
        
        # Test that lazy loading works
        print("Testing lazy loading...")
        
        # These should be None initially
        assert main.genai is None, "genai should be None initially"
        assert main.model is None, "model should be None initially"
        assert main.face is None, "face should be None initially"
        assert main.emotion_detector is None, "emotion_detector should be None initially"
        
        print("✅ Lazy loading is working correctly")
        
        # Test loading functions
        print("Testing lazy loading functions...")
        
        # Test Google AI loading
        start_ai = time.time()
        main.load_google_ai()
        ai_load_time = time.time() - start_ai
        print(f"✅ Google AI loaded in {ai_load_time:.2f} seconds")
        
        # Test TTS loading
        start_tts = time.time()
        main.load_tts()
        tts_load_time = time.time() - start_tts
        print(f"✅ TTS loaded in {tts_load_time:.2f} seconds")
        
        # Test speech recognition loading
        start_sr = time.time()
        main.load_speech_recognition()
        sr_load_time = time.time() - start_sr
        print(f"✅ Speech recognition loaded in {sr_load_time:.2f} seconds")
        
        total_time = time.time() - start_time
        print(f"\n🎉 Total test completed in {total_time:.2f} seconds")
        print("✅ All optimizations are working correctly!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Run the startup test"""
    print("🧪 Testing startup optimizations...")
    print("=" * 50)
    
    success = test_import_speed()
    
    if success:
        print("\n🎉 All tests passed! The server should start much faster now.")
        print("💡 Use 'python start_server.py' to start the optimized server")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
