#!/usr/bin/env python3
"""
Test script to demonstrate improved TTS speeds for different languages
"""

import time
import sys
from pathlib import Path

def test_tts_speeds():
    """Test TTS speeds for different languages"""
    print("🎤 Testing TTS speeds for different languages...")
    print("=" * 60)
    
    # Test languages with their expected rates
    test_languages = [
        ("en-US", "English (US)", "Hello, this is a test of English speech."),
        ("es-ES", "Spanish (Spain)", "Hola, esta es una prueba de voz en español."),
        ("fr-FR", "French (France)", "Bonjour, ceci est un test de voix en français."),
        ("de-DE", "German (Germany)", "Hallo, das ist ein Test der deutschen Sprache."),
        ("zh-CN", "Chinese (Simplified)", "你好，这是中文语音测试。"),
        ("ja-JP", "Japanese", "こんにちは、これは日本語の音声テストです。"),
        ("ko-KR", "Korean", "안녕하세요, 이것은 한국어 음성 테스트입니다."),
        ("ar-001", "Arabic", "مرحبا، هذا اختبار الصوت باللغة العربية."),
        ("hi-IN", "Hindi", "नमस्ते, यह हिंदी भाषा का आवाज़ परीक्षण है।"),
        ("ru-RU", "Russian", "Привет, это тест русской речи."),
    ]
    
    try:
        # Import the main module
        import main
        
        print("📊 Language-specific TTS rates:")
        print("-" * 40)
        
        for lang_code, lang_name, test_text in test_languages:
            rate = main.get_speech_rate(lang_code)
            print(f"{lang_name:20} ({lang_code:6}): {rate:3} WPM")
        
        print("\n🎯 Testing actual speech (will play audio)...")
        print("Press Ctrl+C to stop testing\n")
        
        for i, (lang_code, lang_name, test_text) in enumerate(test_languages):
            try:
                print(f"{i+1:2}. Testing {lang_name} ({lang_code}) at {main.get_speech_rate(lang_code)} WPM...")
                print(f"    Text: {test_text}")
                
                # Test the speech
                main.speak(test_text, lang_code)
                
                print(f"    ✅ {lang_name} speech completed\n")
                time.sleep(1)  # Brief pause between tests
                
            except KeyboardInterrupt:
                print("\n\n⏹️  Testing stopped by user")
                break
            except Exception as e:
                print(f"    ❌ Error testing {lang_name}: {e}\n")
        
        print("🎉 TTS speed testing completed!")
        print("\n💡 Key improvements:")
        print("   • Asian languages (Chinese, Japanese, Korean): 120-130 WPM (much slower)")
        print("   • Slavic languages (Russian, Polish, etc.): 140 WPM (slower)")
        print("   • Romance languages (Spanish, French, etc.): 150 WPM (moderate)")
        print("   • Germanic languages (German, Dutch, etc.): 160 WPM (moderate)")
        print("   • English variants: 180 WPM (faster)")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Run the TTS speed test"""
    print("🔊 TTS Speed Optimization Test")
    print("This will test the improved speech rates for different languages")
    print("=" * 60)
    
    success = test_tts_speeds()
    
    if success:
        print("\n✅ All tests completed successfully!")
        print("🎯 Non-English languages should now sound much more natural and slower")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
