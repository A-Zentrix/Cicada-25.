from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import subprocess
import json
from datetime import datetime
import asyncio
import threading
from typing import Optional

# Lazy imports - only load when needed
genai = None
pyttsx3 = None
sr = None
face = None
emotion_detector = None
analysis_bot = None

# Language-specific TTS rates for optimal speech speed
LANGUAGE_TTS_RATES = {
    # English variants - moderate speed
    "en-US": 180,
    "en-GB": 180,
    "en-AU": 180,
    "en-IE": 180,
    "en-IN": 180,
    "en-ZA": 180,
    "en-CA": 180,
    
    # Romance languages - slower for clarity
    "es-ES": 150,  # Spanish
    "es-MX": 150,
    "fr-FR": 150,  # French
    "fr-CA": 150,
    "it-IT": 150,  # Italian
    "pt-BR": 150,  # Portuguese
    "pt-PT": 150,
    "ro-RO": 150,  # Romanian
    
    # Germanic languages - moderate speed
    "de-DE": 160,  # German
    "nl-NL": 160,  # Dutch
    "nl-BE": 160,
    "sv-SE": 160,  # Swedish
    "da-DK": 160,  # Danish
    "nb-NO": 160,  # Norwegian
    
    # Slavic languages - slower for clarity
    "ru-RU": 140,  # Russian
    "pl-PL": 140,  # Polish
    "cs-CZ": 140,  # Czech
    "sk-SK": 140,  # Slovak
    "hr-HR": 140,  # Croatian
    "sl-SI": 140,  # Slovenian
    "uk-UA": 140,  # Ukrainian
    "bg-BG": 140,  # Bulgarian
    
    # Asian languages - much slower for clarity
    "zh-CN": 120,  # Chinese (Simplified)
    "zh-TW": 120,  # Chinese (Traditional)
    "zh-HK": 120,  # Chinese (Hong Kong)
    "ja-JP": 130,  # Japanese
    "ko-KR": 130,  # Korean
    "th-TH": 130,  # Thai
    "vi-VN": 130,  # Vietnamese
    
    # Middle Eastern languages - slower for clarity
    "ar-001": 140,  # Arabic
    "ar-EG": 140,
    "ar-SA": 140,
    "he-IL": 140,  # Hebrew
    
    # South Asian languages - slower for clarity
    "hi-IN": 130,  # Hindi
    "ta-IN": 130,  # Tamil
    "te-IN": 130,  # Telugu
    "kn-IN": 130,  # Kannada
    "ml-IN": 130,  # Malayalam
    "bn-IN": 130,  # Bengali
    "gu-IN": 130,  # Gujarati
    "mr-IN": 130,  # Marathi
    "pa-IN": 130,  # Punjabi
    "ur-IN": 130,  # Urdu
    
    # Other languages - moderate speed
    "fi-FI": 150,  # Finnish
    "hu-HU": 150,  # Hungarian
    "tr-TR": 150,  # Turkish
    "el-GR": 150,  # Greek
    "ca-ES": 150,  # Catalan
    "ms-MY": 150,  # Malay
    "id-ID": 150,  # Indonesian
}

app = FastAPI(title="AI Mental Wellness Chatbot")

# CORS (allow React dev server)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost",
        "http://127.0.0.1",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Path to built React app (mounted later after API routes)
frontend_dist = os.path.join(os.path.dirname(__file__), "frontend", "dist")

# Initialize speech engine (lazy initialization)
engine = None

# Lazy loading functions
def load_google_ai():
    """Load/ensure Google Generative AI client and model."""
    global genai, model
    try:
        if not api_key:
            print("Google AI API key missing; cannot initialize model")
            return False
        if genai is None:
            import google.generativeai as genai_module
            genai = genai_module
            genai.configure(api_key=api_key)
        # Ensure model is initialized even if genai was already set
        if model is None:
            model = genai.GenerativeModel(
                model_name="gemini-2.0-flash-lite",
                generation_config=generation_config,
                system_instruction=system_prompt
            )
        return True
    except Exception as e:
        print(f"Failed to initialize Google AI model: {e}")
        model = None
        return False

def load_tts():
    """Load TTS engine only when needed"""
    global pyttsx3, engine
    if pyttsx3 is None:
        import pyttsx3
        pyttsx3 = pyttsx3
    if engine is None:
        try:
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            if voices and len(voices) > 0:
                engine.setProperty('voice', voices[0].id)
            engine.setProperty("rate", 160)
        except Exception as e:
            print(f"Warning: Could not initialize TTS engine: {e}")

def load_speech_recognition():
    """Load speech recognition only when needed"""
    global sr
    if sr is None:
        import speech_recognition as sr_module
        sr = sr_module

def load_emotion_detection():
    """Load emotion detection modules only when needed"""
    global face, emotion_detector
    if face is None:
        from dpmodel import face
    if emotion_detector is None:
        from background_emotion import emotion_detector

def load_analysis():
    """Load analysis module only when needed"""
    global analysis_bot
    if analysis_bot is None:
        from analysis import bot as analysis_bot

def get_speech_rate(language):
    """Get the optimal speech rate for a given language"""
    return LANGUAGE_TTS_RATES.get(language, 160)

def set_speech_rate(language, rate):
    """Set a custom speech rate for a language"""
    if 50 <= rate <= 300:  # Reasonable range
        LANGUAGE_TTS_RATES[language] = rate
        return True
    return False

# Allowed languages (single source of truth)
# Codes use hyphen (-). Underscore variants from UI/API are normalized to hyphen.
ALLOWED_LANGUAGES = {
    "ar-001": {"name": "Arabic (Majed)", "voices": ["Maged", "Laila"]},
    "bg-BG": {"name": "Bulgarian", "voices": ["Daria"]},
    "ca-ES": {"name": "Catalan", "voices": ["Montse"]},
    "cs-CZ": {"name": "Czech", "voices": ["Zuzana"]},
    "da-DK": {"name": "Danish", "voices": ["Sara"]},
    "de-DE": {"name": "German (Germany)", "voices": ["Shelley", "Eddy", "Anna"]},
    "el-GR": {"name": "Greek", "voices": ["Melina"]},
    "en-AU": {"name": "English (Australia)", "voices": ["Karen"]},
    "en-GB": {"name": "English (UK)", "voices": ["Shelley", "Daniel", "Flo"]},
    "en-IE": {"name": "English (Ireland)", "voices": ["Moira"]},
    "en-IN": {"name": "English (India)", "voices": ["Rishi"]},
    "en-US": {"name": "English (US)", "voices": ["Samantha", "Alex"]},
    "en-ZA": {"name": "English (South Africa)", "voices": ["Tessa"]},
    "es-ES": {"name": "Spanish (Spain)", "voices": ["Monica", "Diego"]},
    "es-MX": {"name": "Spanish (Mexico)", "voices": ["Paulina", "Monica", "Diego"]},
    "fi-FI": {"name": "Finnish", "voices": ["Satu", "Shelley"]},
    "fr-CA": {"name": "French (Canada)", "voices": ["Amelie", "Shelley"]},
    "fr-FR": {"name": "French (France)", "voices": ["Thomas", "Audrey"]},
    "he-IL": {"name": "Hebrew", "voices": ["Carmit"]},
    "hi-IN": {"name": "Hindi", "voices": ["Lekha", "Rishi"]},
    "hr-HR": {"name": "Croatian", "voices": ["Lana"]},
    "hu-HU": {"name": "Hungarian", "voices": ["Tünde"]},
    "id-ID": {"name": "Indonesian", "voices": ["Damayanti"]},
    "it-IT": {"name": "Italian", "voices": ["Alice", "Shelley"]},
    "ja-JP": {"name": "Japanese", "voices": ["Kyoko", "Shelley"]},
    "ko-KR": {"name": "Korean", "voices": ["Yuna", "Shelley"]},
    "ms-MY": {"name": "Malay", "voices": ["Amira"]},
    "nb-NO": {"name": "Norwegian", "voices": ["Nora"]},
    "nl-BE": {"name": "Dutch (Belgium)", "voices": ["Ellen"]},
    "nl-NL": {"name": "Dutch (Netherlands)", "voices": ["Xander"]},
    "pl-PL": {"name": "Polish", "voices": ["Zosia"]},
    "pt-BR": {"name": "Portuguese (Brazil)", "voices": ["Luciana", "Shelley"]},
    "pt-PT": {"name": "Portuguese (Portugal)", "voices": ["Joana"]},
    "ro-RO": {"name": "Romanian", "voices": ["Ioana"]},
    "ru-RU": {"name": "Russian", "voices": ["Milena", "Yuri"]},
    "sk-SK": {"name": "Slovak", "voices": ["Laura"]},
    "sl-SI": {"name": "Slovenian", "voices": ["Tina"]},
    "sv-SE": {"name": "Swedish", "voices": ["Alva"]},
    "ta-IN": {"name": "Tamil", "voices": ["Vani"]},
    "th-TH": {"name": "Thai", "voices": ["Kanya"]},
    "tr-TR": {"name": "Turkish", "voices": ["Yelda"]},
    "uk-UA": {"name": "Ukrainian", "voices": ["Lesya"]},
    "vi-VN": {"name": "Vietnamese", "voices": ["Linh"]},
    "zh-CN": {"name": "Chinese (Mandarin, mainland)", "voices": ["Ting-Ting", "Eddy"]},
    "zh-HK": {"name": "Chinese (Hong Kong)", "voices": ["Sin-ji"]},
    "zh-TW": {"name": "Chinese (Taiwan)", "voices": ["Mei-Jia", "Shelley"]}
}

# Preferred macOS voice IDs and names per language (normalized with hyphens)
VOICE_PREFERENCES = {
    "ar-001": {"id": "com.apple.voice.compact.ar-001.Maged", "name": "Majed"},
    "bg-BG": {"id": "com.apple.voice.compact.bg-BG.Daria", "name": "Daria"},
    "ca-ES": {"id": "com.apple.voice.compact.ca-ES.Montserrat", "name": "Montse"},
    "cs-CZ": {"id": "com.apple.voice.compact.cs-CZ.Zuzana", "name": "Zuzana"},
    "da-DK": {"id": "com.apple.voice.compact.da-DK.Sara", "name": "Sara"},
    "de-DE": {"id": "com.apple.eloquence.de-DE.Shelley", "name": "Shelley"},
    "el-GR": {"id": "com.apple.voice.compact.el-GR.Melina", "name": "Melina"},
    "en-AU": {"id": "com.apple.voice.compact.en-AU.Karen", "name": "Karen"},
    "en-GB": {"id": "com.apple.eloquence.en-GB.Shelley", "name": "Shelley"},
    "en-IE": {"id": "com.apple.voice.compact.en-IE.Moira", "name": "Moira"},
    "en-IN": {"id": "com.apple.voice.compact.en-IN.Rishi", "name": "Rishi"},
    "en-US": {"id": "com.apple.speech.synthesis.voice.Samantha", "name": "Samantha"},
    "en-ZA": {"id": "com.apple.voice.compact.en-ZA.Tessa", "name": "Tessa"},
    "es-ES": {"id": "com.apple.eloquence.es-ES.Shelley", "name": "Shelley"},
    "es-MX": {"id": "com.apple.eloquence.es-MX.Shelley", "name": "Shelley"},
    "fi-FI": {"id": "com.apple.eloquence.fi-FI.Shelley", "name": "Shelley"},
    "fr-CA": {"id": "com.apple.eloquence.fr-CA.Shelley", "name": "Shelley"},
    "fr-FR": {"id": "com.apple.voice.compact.fr-FR.Thomas", "name": "Thomas"},
    "he-IL": {"id": "com.apple.voice.compact.he-IL.Carmit", "name": "Carmit"},
    "hi-IN": {"id": "com.apple.voice.compact.hi-IN.Lekha", "name": "Lekha"},
    "hr-HR": {"id": "com.apple.voice.compact.hr-HR.Lana", "name": "Lana"},
    "hu-HU": {"id": "com.apple.voice.compact.hu-HU.Mariska", "name": "Tünde"},
    "id-ID": {"id": "com.apple.voice.compact.id-ID.Damayanti", "name": "Damayanti"},
    "it-IT": {"id": "com.apple.eloquence.it-IT.Shelley", "name": "Shelley"},
    "ja-JP": {"id": "com.apple.eloquence.ja-JP.Shelley", "name": "Shelley"},
    "ko-KR": {"id": "com.apple.voice.compact.ko-KR.Yuna", "name": "Yuna"},
    "ms-MY": {"id": "com.apple.voice.compact.ms-MY.Amira", "name": "Amira"},
    "nb-NO": {"id": "com.apple.voice.compact.nb-NO.Nora", "name": "Nora"},
    "nl-BE": {"id": "com.apple.voice.compact.nl-BE.Ellen", "name": "Ellen"},
    "nl-NL": {"id": "com.apple.voice.compact.nl-NL.Xander", "name": "Xander"},
    "pl-PL": {"id": "com.apple.voice.compact.pl-PL.Zosia", "name": "Zosia"},
    "pt-BR": {"id": "com.apple.eloquence.pt-BR.Shelley", "name": "Shelley"},
    "pt-PT": {"id": "com.apple.voice.compact.pt-PT.Joana", "name": "Joana"},
    "ro-RO": {"id": "com.apple.voice.compact.ro-RO.Ioana", "name": "Ioana"},
    "ru-RU": {"id": "com.apple.voice.compact.ru-RU.Milena", "name": "Milena"},
    "sk-SK": {"id": "com.apple.voice.compact.sk-SK.Laura", "name": "Laura"},
    "sl-SI": {"id": "com.apple.voice.compact.sl-SI.Tina", "name": "Tina"},
    "sv-SE": {"id": "com.apple.voice.compact.sv-SE.Alva", "name": "Alva"},
    "ta-IN": {"id": "com.apple.voice.compact.ta-IN.Vani", "name": "Vani"},
    "th-TH": {"id": "com.apple.voice.compact.th-TH.Kanya", "name": "Kanya"},
    "tr-TR": {"id": "com.apple.voice.compact.tr-TR.Yelda", "name": "Yelda"},
    "uk-UA": {"id": "com.apple.voice.compact.uk-UA.Lesya", "name": "Lesya"},
    "vi-VN": {"id": "com.apple.voice.compact.vi-VN.Linh", "name": "Linh"},
    "zh-CN": {"id": "com.apple.voice.compact.zh-CN.Tingting", "name": "Tingting"},
    "zh-HK": {"id": "com.apple.voice.compact.zh-HK.Sinji", "name": "Sinji"},
    "zh-TW": {"id": "com.apple.eloquence.zh-TW.Shelley", "name": "Shelley"},
}

def cleanup_tts():
    """Clean up TTS resources"""
    global engine
    if engine is not None:
        try:
            engine.stop()
        except:
            pass
        engine = None

def check_audio_system():
    """Check if audio system is working"""
    try:
        print("Checking audio system...")
        # Test with a simple system sound
        result = subprocess.run(['afplay', '/System/Library/Sounds/Glass.aiff'], 
                              timeout=5, capture_output=True)
        if result.returncode == 0:
            print("Audio system is working")
            return True
        else:
            print("Audio system test failed")
            return False
    except Exception as e:
        print(f"Audio system check failed: {e}")
        return False

system_prompt = f"""
You are a compassionate, intelligent mental wellness companion. Always interact as a supportive and trusted friend, never as a bot, therapist, or professional. Your purpose is to provide comfort, reduce stress, and guide users toward positive mental health while subtly gathering deep insights with the awareness of a PhD-level psychologist.

Tone and Style:
- Speak warmly, casually, and empathetically, like a close friend who truly cares.
- Avoid clinical or robotic language. Never mention therapy, assessments, or structured tests.
- Keep each response a single smooth paragraph of 20–30 words, never breaking into lists, bullets, or symbols.

Behavior:
- Listen carefully and acknowledge emotions naturally with empathy and warmth.
- Casually weave in gentle, everyday questions inspired by PHQ-9, GAD-7, and GHQ tools, but disguise them as friendly curiosity about life, stress, energy, mood, or motivation.
- Explore student life, challenges, routines, and sources of support like friends, mentors, or counsellors in a natural way.
- Offer encouragement, reassurance, and simple coping suggestions when it feels right, but give deeper strategies only if directly asked.
- If severe distress appears, respond with kindness and gently encourage reaching out to a trusted professional, helpline, or loved one, while keeping tone hopeful and supportive.
- you must speak in the language of the user which is specified in the language context, 
- you must speak in the language of the user which is specified in the language context very clearly and explicitly, don't use symbols, don't split your reply into phrases, just end it in one paragraph.
-you speake very casually and naturally, like a friend would. don't speak like a therapist or a professional.
Core Principle:
The user should always feel they are talking to a caring, understanding friend. Beneath the surface, your questions and reflections should carry the depth of a trained psychologist without ever revealing the method.
"""
# macOS TTS voices dictionary
mac_voices = {
    "English": {
        "US": ["com.apple.voice.compact.en-US.Samantha",
               "com.apple.eloquence.en-US.Daniel",
               "com.apple.speech.synthesis.voice.Fred",
               "com.apple.speech.synthesis.voice.Albert"],
        "UK": ["com.apple.voice.compact.en-GB.Daniel",
               "com.apple.eloquence.en-GB.Flo",
               "com.apple.eloquence.en-GB.Grandma",
               "com.apple.eloquence.en-GB.Shelley"],
        "Australia": ["com.apple.voice.compact.en-AU.Karen"],
        "Ireland": ["com.apple.voice.compact.en-IE.Moira"],
        "South Africa": ["com.apple.voice.compact.en-ZA.Tessa"],
        "India": ["com.apple.voice.compact.en-IN.Rishi"]
    },
    "Tamil": {
        "India": ["com.apple.voice.compact.ta-IN.Vani"]
    },
    "Hindi": {
        "India": ["com.apple.voice.compact.hi-IN.Lekha"]
    },
    "French": {
        "France": ["com.apple.eloquence.fr-FR.Jacques",
                   "com.apple.eloquence.fr-FR.Flo",
                   "com.apple.eloquence.fr-FR.Sandy",
                   "com.apple.eloquence.fr-FR.Shelley"],
        "Canada": ["com.apple.voice.compact.fr-CA.Amelie",
                   "com.apple.eloquence.fr-CA.Flo",
                   "com.apple.eloquence.fr-CA.Sandy",
                   "com.apple.eloquence.fr-CA.Shelley"]
    },
    "Spanish": {
        "Spain": ["com.apple.eloquence.es-ES.Eddy",
                  "com.apple.eloquence.es-ES.Flo",
                  "com.apple.eloquence.es-ES.Grandma",
                  "com.apple.eloquence.es-ES.Reed"],
        "Mexico": ["com.apple.eloquence.es-MX.Eddy",
                   "com.apple.eloquence.es-MX.Flo",
                   "com.apple.eloquence.es-MX.Grandma",
                   "com.apple.eloquence.es-MX.Reed",
                   "com.apple.voice.compact.es-MX.Paulina"]
    },
    "Italian": {
        "Italy": ["com.apple.voice.compact.it-IT.Alice",
                  "com.apple.eloquence.it-IT.Eddy",
                  "com.apple.eloquence.it-IT.Flo",
                  "com.apple.eloquence.it-IT.Grandma",
                  "com.apple.eloquence.it-IT.Rocko",
                  "com.apple.eloquence.it-IT.Sandy",
                  "com.apple.eloquence.it-IT.Shelley"]
    },
    "German": {
        "Germany": ["com.apple.voice.compact.de-DE.Anna",
                    "com.apple.eloquence.de-DE.Eddy",
                    "com.apple.eloquence.de-DE.Flo",
                    "com.apple.eloquence.de-DE.Grandma",
                    "com.apple.eloquence.de-DE.Reed",
                    "com.apple.eloquence.de-DE.Rocko",
                    "com.apple.eloquence.de-DE.Sandy",
                    "com.apple.eloquence.de-DE.Shelley"]
    },
    "Japanese": {
        "Japan": ["com.apple.voice.compact.ja-JP.Kyoko",
                  "com.apple.eloquence.ja-JP.Eddy",
                  "com.apple.eloquence.ja-JP.Flo",
                  "com.apple.eloquence.ja-JP.Reed",
                  "com.apple.eloquence.ja-JP.Rocko",
                  "com.apple.eloquence.ja-JP.Sandy",
                  "com.apple.eloquence.ja-JP.Shelley"]
    },
    "Korean": {
        "South Korea": ["com.apple.voice.compact.ko-KR.Yuna",
                        "com.apple.eloquence.ko-KR.Eddy",
                        "com.apple.eloquence.ko-KR.Flo",
                        "com.apple.eloquence.ko-KR.Grandma",
                        "com.apple.eloquence.ko-KR.Reed",
                        "com.apple.eloquence.ko-KR.Rocko",
                        "com.apple.eloquence.ko-KR.Shelley"]
    },
    "Chinese": {
        "China": ["com.apple.voice.compact.zh-CN.Tingting",
                  "com.apple.eloquence.zh-CN.Eddy",
                  "com.apple.eloquence.zh-CN.Flo",
                  "com.apple.eloquence.zh-CN.Grandma",
                  "com.apple.eloquence.zh-CN.Reed",
                  "com.apple.eloquence.zh-CN.Rocko",
                  "com.apple.eloquence.zh-CN.Sandy",
                  "com.apple.eloquence.zh-CN.Shelley"],
        "Taiwan": ["com.apple.voice.compact.zh-TW.Meijia",
                   "com.apple.eloquence.zh-TW.Eddy",
                   "com.apple.eloquence.zh-TW.Flo",
                   "com.apple.eloquence.zh-TW.Grandma",
                   "com.apple.eloquence.zh-TW.Reed",
                   "com.apple.eloquence.zh-TW.Rocko",
                   "com.apple.eloquence.zh-TW.Sandy",
                   "com.apple.eloquence.zh-TW.Shelley"],
        "Hong Kong": ["com.apple.voice.compact.zh-HK.Sinji"]
    },
    "Portuguese": {
        "Brazil": ["com.apple.eloquence.pt-BR.Eddy",
                   "com.apple.eloquence.pt-BR.Flo",
                   "com.apple.eloquence.pt-BR.Grandma",
                   "com.apple.eloquence.pt-BR.Reed",
                   "com.apple.eloquence.pt-BR.Rocko",
                   "com.apple.eloquence.pt-BR.Shelley",
                   "com.apple.voice.compact.pt-BR.Luciana"],
        "Portugal": ["com.apple.voice.compact.pt-PT.Joana"]
    },
    "Dutch": {
        "Netherlands": ["com.apple.voice.compact.nl-NL.Xander"],
        "Belgium": ["com.apple.voice.compact.nl-BE.Ellen"]
    },
    "Other": {
        "Swedish": ["com.apple.voice.compact.sv-SE.Alva"],
        "Finnish": ["com.apple.voice.compact.fi-FI.Satu"],
        "Romanian": ["com.apple.voice.compact.ro-RO.Ioana"],
        "Hebrew": ["com.apple.voice.compact.he-IL.Carmit"],
        "Thai": ["com.apple.voice.compact.th-TH.Kanya"],
        "Czech": ["com.apple.voice.compact.cs-CZ.Zuzana"],
        "Polish": ["com.apple.voice.compact.pl-PL.Zosia"],
        "Slovenian": ["com.apple.voice.compact.sl-SI.Tina"],
        "Ukrainian": ["com.apple.voice.compact.uk-UA.Lesya"],
        "Vietnamese": ["com.apple.voice.compact.vi-VN.Linh"],
        "Arabic": ["com.apple.voice.compact.ar-001.Maged"]
    }
}
# 🌍 SpeechRecognition language codes dictionary
LANGUAGE_CODES_SR = {
    # Indian Languages
    "hindi": "hi-IN",
    "tamil": "ta-IN",
    "telugu": "te-IN",
    "kannada": "kn-IN",
    "malayalam": "ml-IN",
    "bengali": "bn-IN",
    "gujarati": "gu-IN",
    "marathi": "mr-IN",
    "punjabi": "pa-IN",
    "urdu": "ur-IN",

    # English Variants
    "english_india": "en-IN",
    "english_us": "en-US",
    "english_uk": "en-GB",
    "english_australia": "en-AU",
    "english_canada": "en-CA",

    # Other Major Languages
    "spanish_spain": "es-ES",
    "spanish_mexico": "es-MX",
    "french_france": "fr-FR",
    "french_canada": "fr-CA",
    "german": "de-DE",
    "italian": "it-IT",
    "portuguese_brazil": "pt-BR",
    "portuguese_portugal": "pt-PT",
    "russian": "ru-RU",
    "chinese_simplified": "zh-CN",
    "chinese_traditional": "zh-TW",
    "japanese": "ja-JP",
    "korean": "ko-KR",
    "arabic_egypt": "ar-EG",
    "arabic_saudi": "ar-SA"
}

def speak(audio, language="en-US"):
    global engine, current_language
    
    # Load TTS if not already loaded
    load_tts()
    
    # Use the current language if not specified
    if language == "en-US":
        language = current_language
    # Normalize underscores to hyphens
    language = language.replace('_', '-')
    # Enforce allowed language set; fallback to en-US if unsupported
    if language not in ALLOWED_LANGUAGES:
        language = "en-US"
    
    print(f"Attempting to speak: {audio} (Language: {language})")
    
    # Get language-specific speech rate
    speech_rate = LANGUAGE_TTS_RATES.get(language, 160)  # Default to 160 if language not found
    print(f"Using speech rate: {speech_rate} words per minute for {language}")
    
    # Force audio output to default device and ensure volume
    try:
        # Set volume to ensure audio is audible
        subprocess.run(['osascript', '-e', 'set volume output volume 75'], timeout=5)
        
        # Use the most reliable approach - simple say command with language-specific voice
        print(f"Using macOS 'say' command with language: {language}")
        
        # Preferred voice: use explicit voice ID/name mapping first
        preferred = VOICE_PREFERENCES.get(language)
        voices_to_try = []
        if preferred:
            # Try by readable name first, then by ID fallback via 'say' -v expects name; ID is used with 'say' via full identifier too
            voices_to_try.extend([preferred.get('name'), preferred.get('id')])
        # Backfill with display names configured in allowed list
        voices_to_try.extend(ALLOWED_LANGUAGES.get(language, ALLOWED_LANGUAGES["en-US"])['voices'])
        # Remove Nones and duplicates while preserving order
        seen = set()
        voices_to_try = [v for v in voices_to_try if v and (v not in seen and not seen.add(v))]
        
        # Try language-specific voices first
        for voice in voices_to_try:
            try:
                subprocess.run(['say', '-v', voice, '-r', str(speech_rate), audio], 
                              timeout=30, check=True)
                print(f"Successfully spoke using {voice} voice for {language} at {speech_rate} WPM")
                return
            except:
                continue
        
        # Try default voice with language parameter
        try:
            subprocess.run(['say', '-r', str(speech_rate), audio], timeout=30, check=True)
            print(f"Successfully spoke using default voice for {language} at {speech_rate} WPM")
            return
        except:
            pass
            
        print("All say command options failed")
    except Exception as e:
        print(f"macOS 'say' command failed: {e}")
    
    # Fallback to pyttsx3 if say fails
    if engine is None:
        try:
            print("Initializing TTS engine as fallback...")
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            if voices:
                # Look for a voice that matches the language
                language_prefix = language.split('-')[0]
                for i, voice in enumerate(voices):
                    voice_name = voice.name.lower()
                    if (language_prefix in voice_name or 
                        'female' in voice_name or 
                        'woman' in voice_name or 
                        'girl' in voice_name):
                        engine.setProperty('voice', voice.id)
                        print(f"Using voice for {language}: {voice.name}")
                        break
                else:
                    # If no language-specific voice found, use a feminine voice
                    for i, voice in enumerate(voices):
                        if 'female' in voice.name.lower() or 'woman' in voice.name.lower() or 'girl' in voice.name.lower():
                            engine.setProperty('voice', voice.id)
                            print(f"Using feminine voice: {voice.name}")
                            break
                    else:
                        # If no feminine voice found, use a higher index voice
                        if len(voices) > 50:
                            engine.setProperty('voice', voices[50].id)
                            print(f"Using voice: {voices[50].name}")
                        else:
                            engine.setProperty('voice', voices[0].id)
                            print(f"Using default voice: {voices[0].name}")
            # Set language-specific rate for optimal speech speed
            engine.setProperty("rate", speech_rate)
            print(f"TTS engine initialized successfully with rate {speech_rate} WPM")
        except Exception as e:
            print(f"Warning: Could not initialize TTS engine: {e}")
            print(f"TTS not available, would speak: {audio}")
            return
    
    def _speak_blocking(text):
        try:
            engine.say(text)
            engine.runAndWait()
        except Exception as inner_e:
            print(f"pyttsx3 speak error: {inner_e}")

    try:
        print("Queueing speech on background thread...")
        t = threading.Thread(target=_speak_blocking, args=(audio,), daemon=True)
        t.start()
        print("Speech started asynchronously")
    except Exception as e:
        print(f"TTS error: {e}")
        # Reset engine on error
        try:
            engine.stop()
        except:
            pass
        engine = None
        
        # Final fallback - try system beep to test audio
        try:
            print("Testing audio with system beep...")
            subprocess.run(['afplay', '/System/Library/Sounds/Glass.aiff'], timeout=5)
            print("Audio system is working, trying simple say command...")
            subprocess.run(['say', '-r', str(speech_rate), audio], timeout=30)
            print(f"Successfully spoke using simple say command at {speech_rate} WPM")
            return
        except Exception as e2:
            print(f"Final audio test failed: {e2}")
            print(f"TTS not available, would speak: {audio}")

api_key = "AIzaSyA3f8izcUDNQTik3utegfZ5bKvxeG0vwq8"

# Model configuration (will be used when model is loaded)
generation_config = {
    "temperature": 0.9,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 512,
    "response_mime_type": "text/plain",
}

# Model will be initialized lazily
model = None
FALLBACK_ERROR_MESSAGE = "I'm sorry, I'm having trouble responding right now. Please try again."

def read_current_emotion():
    """Read current emotion from emotion_log.txt file"""
    try:
        # Load emotion detection if not already loaded
        load_emotion_detection()
        emotion_file = emotion_detector.log_file
        if os.path.exists(emotion_file):
            with open(emotion_file, 'r') as f:
                lines = f.readlines()
            # Skip header and get the emotion
            if len(lines) > 1:
                emotion = lines[1].strip()
                return emotion if emotion else None
        return None
    except Exception as e:
        print(f"Error reading emotion: {e}")
        return None

# Global conversation memory
conversation_memory = []

# Global language setting
current_language = "en-US"

def load_conversation_memory():
    """Load conversation memory from file"""
    global conversation_memory
    try:
        memory_file = "conversation_memory.json"
        if os.path.exists(memory_file):
            import json
            with open(memory_file, 'r', encoding='utf-8') as f:
                conversation_memory = json.load(f)
            print(f"Loaded {len(conversation_memory)} conversation entries from memory")
        else:
            conversation_memory = []
            print("No conversation memory found, starting fresh")
    except Exception as e:
        print(f"Error loading conversation memory: {e}")
        conversation_memory = []

def save_conversation_memory():
    """Save conversation memory to file"""
    try:
        memory_file = "conversation_memory.json"
        import json
        with open(memory_file, 'w', encoding='utf-8') as f:
            json.dump(conversation_memory, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(conversation_memory)} conversation entries to memory")
    except Exception as e:
        print(f"Error saving conversation memory: {e}")

def add_to_memory(user_message, ai_response, emotion=None):
    """Add conversation to memory"""
    global conversation_memory
    try:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        memory_entry = {
            "timestamp": timestamp,
            "user": user_message,
            "ai": ai_response,
            "emotion": emotion
        }
        
        conversation_memory.append(memory_entry)
        
        # Keep only last 20 conversations to avoid memory overflow
        if len(conversation_memory) > 20:
            conversation_memory = conversation_memory[-20:]
        
        # Save to file
        save_conversation_memory()
        
    except Exception as e:
        print(f"Error adding to memory: {e}")

def get_conversation_context():
    """Get recent conversation context for AI"""
    global conversation_memory
    
    if not conversation_memory:
        return ""
    
    # Get last 5 conversations for context
    recent_conversations = conversation_memory[-5:]
    
    context = "Previous conversation context:\n"
    for conv in recent_conversations:
        context += f"User: {conv['user']}\n"
        context += f"AI: {conv['ai']}\n"
        if conv.get('emotion'):
            context += f"Emotion: {conv['emotion']}\n"
        context += "---\n"
    
    return context

def log_conversation(user_message, ai_response, emotion=None):
    """Log conversation to text file and memory"""
    try:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Add to memory
        add_to_memory(user_message, ai_response, emotion)
        
        # Create conversation log file if it doesn't exist
        conversation_file = "conversation_log.txt"
        if not os.path.exists(conversation_file):
            with open(conversation_file, 'w', encoding='utf-8') as f:
                f.write("Conversation Log\n")
                f.write("=" * 50 + "\n\n")
        
        # Append conversation entry
        with open(conversation_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}]\n")
            f.write(f"User: {user_message}\n")
            if emotion:
                f.write(f"Detected Emotion: {emotion}\n")
            f.write(f"AI: {ai_response}\n")
            f.write("-" * 50 + "\n\n")
        
        print(f"Conversation logged to {conversation_file}")
        
    except Exception as e:
        print(f"Error logging conversation: {e}")

def bot(prompt, language="en-US"):
    """AI bot with intelligent responses, emotion awareness, conversation memory, and language support"""
    global current_language
    
    # Load AI model if not already loaded
    ok = load_google_ai()
    
    # Read current emotion from file
    current_emotion = read_current_emotion()
    
    # Get conversation context
    conversation_context = get_conversation_context()
    
    # Create emotion context for AI
    emotion_context = ""
    if current_emotion:
        emotion_context = f"IMPORTANT: I can see that the person is currently feeling {current_emotion}. Use this emotional context to provide more personalized and empathetic responses. "
    
    # Create memory context for AI
    memory_context = ""
    if conversation_context:
        memory_context = f"CONVERSATION MEMORY: Remember our previous conversations and use this context to provide more personalized and continuous support. {conversation_context}"
    
    # Create language context for AI
    language_context = ""
    if language:
        # Normalize underscores to hyphens and enforce allowed set for context label
        normalized = language.replace('_', '-')
        meta = ALLOWED_LANGUAGES.get(normalized)
        if meta:
            language_context = f"LANGUAGE REQUIREMENT: You must respond in {meta['name']}. All responses must be in this language. "
    
    # Simple but intelligent response system with emotion awareness, memory, and language support
    # Try up to two attempts (re-init model once on failure)
    if ok and model is not None:
        for attempt in range(2):
            try:
                response = model.generate_content([
                    f"You are a compassionate and highly intelligent mental wellness assistant. Your role is to provide emotional support, help users manage stress, and guide them toward positive mental health. Speak in a warm, understanding, and friendly tone. Always prioritize empathy and avoid judgment. {language_context}{emotion_context}{memory_context}When interacting: Listen carefully to users' concerns and acknowledge their feelings. Offer actionable advice when necessary but only if the user seeks it. Share motivational and uplifting words during difficult times. Be conversational and supportive during good times, like a trusted friend. Encourage healthy coping mechanisms and, if needed, suggest seeking professional help but you need to speak within 20 to 30 words, don't use symbols, don't split your reply into phrases, just end it in one paragraph.",
                    f"input:{prompt} ",
                    "output: ",
                ])
                return response.text
            except Exception as e:
                print(f"AI response error (attempt {attempt+1}): {e}")
                try:
                    load_google_ai()
                except Exception:
                    pass
    # Local fallback response if model unavailable or keeps failing
    base = prompt.strip()[:80]
    fallback = (
        (base + " ") if base else ""
    ) + "Take a slow breath and be gentle with yourself; one small step is enough today."
    words = fallback.split()
    if len(words) > 30:
        fallback = " ".join(words[:30])
    return fallback


def takecommand(language="en-US"):
    """Enhanced voice recognition with proper error handling and language support"""
    global current_language
    
    # Load speech recognition if not already loaded
    load_speech_recognition()
    
    try:
        r = sr.Recognizer()
        
        # Configure microphone for better recognition
        with sr.Microphone() as source:
            print(f"Adjusting for ambient noise... (Language: {language})")
            r.adjust_for_ambient_noise(source, duration=0.5)
            print("Listening... (speak now)")
            
            # Listen with longer timeout and better parameters
            audio = r.listen(source, timeout=5, phrase_time_limit=5)
            print("Recognising...")
        
        # Try multiple recognition services for better accuracy
        try:
            # Primary: Google Speech Recognition with selected language
            query = r.recognize_google(audio, language=language)
            print(f"Recognized ({language}): {query}")
            return query
        except sr.UnknownValueError:
            print(f"Google Speech Recognition could not understand audio in {language}")
            try:
                # Fallback: Try with English if other language fails
                if language != "en-US":
                    query = r.recognize_google(audio, language='en-US')
                    print(f"Recognized (fallback to English): {query}")
                    return query
            except:
                pass
        except sr.RequestError as e:
            print(f"Google Speech Recognition service error: {e}")
            try:
                # Fallback: Try Sphinx (offline) - only works with English
                if language.startswith('en'):
                    query = r.recognize_sphinx(audio)
                    print(f"Recognized (Sphinx): {query}")
                    return query
            except:
                pass
        
        print("All recognition methods failed")
        return "nothing"
        
    except sr.WaitTimeoutError:
        print("Listening timeout - no speech detected")
        return "nothing"
    except Exception as e:
        print(f"Voice recognition error: {e}")
        return "nothing"

# Remove explicit root handler; StaticFiles will serve '/' when build exists.

# Language Management Endpoints
@app.get("/language/current")
async def get_current_language():
    """Get current language setting"""
    try:
        return {
            "language": current_language,
            "success": True
        }
    except Exception as e:
        return {
            "language": "en-US",
            "success": False,
            "error": str(e)
        }

@app.post("/language/set")
async def set_language(language: str = Form(...)):
    """Set the current language"""
    global current_language
    try:
        # Normalize underscores to hyphens
        normalized = language.replace('_', '-')
        if normalized not in ALLOWED_LANGUAGES:
            return {
                "message": f"Invalid language code. Supported languages: {', '.join(ALLOWED_LANGUAGES.keys())}",
                "success": False
            }
        current_language = normalized
        print(f"Language changed to: {current_language}")
        
        return {
            "message": f"Language successfully changed to {current_language}",
            "language": current_language,
            "success": True
        }
    except Exception as e:
        return {
            "message": f"Failed to set language: {e}",
            "success": False,
            "error": str(e)
        }

@app.get("/language/list")
async def list_supported_languages():
    """Get list of supported languages (from allowed list)"""
    try:
        languages = [{"code": code, "name": meta["name"]} for code, meta in ALLOWED_LANGUAGES.items()]
        return {
            "languages": languages,
            "current": current_language,
            "success": True
        }
    except Exception as e:
        return {
            "languages": [],
            "success": False,
            "error": str(e)
        }

@app.post("/detect_emotion")
async def detect_emotion():
    try:
        print("Starting emotion detection...")
        
        # Load emotion detection if not already loaded
        load_emotion_detection()
        
        # Use the face() function from dpmodel.py
        emotion = face()
        
        if emotion is None:
            return {
                "emotion": None,
                "response": "Could not detect emotion. Please ensure your face is visible in the camera and try again.",
                "success": False,
                "error": "No emotion detected"
            }
        
        print(f"Detected emotion: {emotion}")
        
        # Get AI response based on emotion (the bot function will automatically read the emotion from file)
        response = bot(f"I'm feeling {emotion}", current_language)
        print(f"AI response: {response}")
        
        # Log conversation
        log_conversation(f"[Emotion Detection] I'm feeling {emotion}", response, emotion)
        
        # Frontend handles speaking to avoid duplicate playback
        
        return {
            "emotion": emotion,
            "response": response,
            "success": True
        }
            
    except Exception as e:
        print(f"Error in detect_emotion: {e}")
        return {
            "emotion": None,
            "response": "Error occurred during emotion detection. Please try again.",
            "success": False,
            "error": str(e)
        }

@app.post("/send_message")
async def send_message(message: str = Form(...)):
    try:
        print(f"Processing message: {message}")
        response = bot(message, current_language)
        print(f"AI response: {response}")
        
        # Log conversation
        current_emotion = read_current_emotion()
        log_conversation(message, response, current_emotion)
        
        # Frontend handles speaking; always return success with generated/fallback text
        is_fallback = (response.strip() == FALLBACK_ERROR_MESSAGE)
        if is_fallback:
            # Replace opaque fallback with friendly local message so UI still shows/speaks something
            response = bot("")
        return { "response": response, "success": True }
    except Exception as e:
        print(f"Error in send_message: {e}")
        error_response = "I'm sorry, I'm having trouble processing your message right now. Please try again in a moment."
        speak(error_response, current_language)
        return {
            "response": error_response,
            "success": False,
            "error": str(e)
        }

@app.post("/voice_command")
async def voice_command():
    try:
        print(f"Starting voice command recognition... (Language: {current_language})")
        command = takecommand(current_language)
        
        if command == "nothing" or not command.strip():
            error_msg = "I couldn't hear you clearly. Please try speaking again, a bit louder and clearer."
            speak(error_msg, current_language)
            return {
                "command": None,
                "response": error_msg,
                "success": False,
                "error": "No speech detected"
            }
        
        print(f"Voice command received: {command}")
        response = bot(command, current_language)
        print(f"AI response: {response}")
        
        # Log conversation
        current_emotion = read_current_emotion()
        log_conversation(f"[Voice] {command}", response, current_emotion)
        
        # Speak the response
        speak(response, current_language)
        return {
            "command": command,
            "response": response,
            "success": True
        }
    except Exception as e:
        print(f"Voice command error: {e}")
        error_msg = "Sorry, there was a technical issue with voice recognition. Please try again."
        return {
            "command": None,
            "response": error_msg,
            "success": False,
            "error": str(e)
        }

@app.post("/speak")
async def speak_text(text: str = Form(...)):
    try:
        speak(text, current_language)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/test_tts")
async def test_tts():
    """Test endpoint to verify TTS is working"""
    test_message = "Hello, this is a test of the text to speech system."
    try:
        # Note: test endpoint still triggers speech
        speak(test_message, current_language)
        return {"message": "TTS test completed", "success": True}
    except Exception as e:
        return {"message": f"TTS test failed: {e}", "success": False}

@app.get("/test_audio")
async def test_audio():
    """Comprehensive audio test"""
    try:
        # Test 1: System beep
        subprocess.run(['afplay', '/System/Library/Sounds/Glass.aiff'], timeout=5)
        
        # Test 2: Simple say command
        subprocess.run(['say', 'Audio test one'], timeout=10)
        
        # Test 3: Say with specific voice
        subprocess.run(['say', '-v', 'Samantha', 'Audio test two with Samantha voice'], timeout=10)
        
        # Test 4: Volume check
        result = subprocess.run(['osascript', '-e', 'output volume of (get volume settings)'], 
                              capture_output=True, text=True, timeout=5)
        volume = result.stdout.strip()
        
        return {
            "message": "Audio tests completed",
            "volume": volume,
            "success": True
        }
    except Exception as e:
        return {"message": f"Audio test failed: {e}", "success": False}

# TTS Rate Management Endpoints

@app.get("/tts/rate/{language}")
async def get_speech_rate_for_language(language: str):
    """Get current speech rate for a language"""
    try:
        # Normalize language code
        normalized = language.replace('_', '-')
        rate = get_speech_rate(normalized)
        return {
            "language": normalized,
            "rate": rate,
            "success": True
        }
    except Exception as e:
        return {
            "language": language,
            "rate": 160,
            "success": False,
            "error": str(e)
        }

@app.post("/tts/rate/{language}")
async def set_speech_rate_for_language(language: str, rate: int = Form(...)):
    """Set custom speech rate for a language"""
    try:
        # Normalize language code
        normalized = language.replace('_', '-')
        
        if set_speech_rate(normalized, rate):
            return {
                "language": normalized,
                "rate": rate,
                "message": f"Speech rate set to {rate} WPM for {normalized}",
                "success": True
            }
        else:
            return {
                "language": normalized,
                "rate": get_speech_rate(normalized),
                "message": f"Invalid rate {rate}. Must be between 50-300 WPM",
                "success": False
            }
    except Exception as e:
        return {
            "language": language,
            "rate": 160,
            "success": False,
            "error": str(e)
        }

@app.get("/tts/rates")
async def get_all_speech_rates():
    """Get all current speech rates for all languages"""
    try:
        return {
            "rates": LANGUAGE_TTS_RATES,
            "success": True
        }
    except Exception as e:
        return {
            "rates": {},
            "success": False,
            "error": str(e)
        }

@app.post("/tts/test_rate")
async def test_speech_rate(language: str = Form(...), rate: int = Form(...), text: str = Form("Hello, this is a test of the speech rate.")):
    """Test speech with custom rate"""
    try:
        # Normalize language code
        normalized = language.replace('_', '-')
        
        # Temporarily set the rate
        original_rate = LANGUAGE_TTS_RATES.get(normalized, 160)
        LANGUAGE_TTS_RATES[normalized] = rate
        
        # Test speech
        speak(text, normalized)
        
        # Restore original rate
        LANGUAGE_TTS_RATES[normalized] = original_rate
        
        return {
            "message": f"Tested speech at {rate} WPM for {normalized}",
            "success": True
        }
    except Exception as e:
        return {
            "message": f"Speech rate test failed: {e}",
            "success": False,
            "error": str(e)
        }

@app.get("/test_microphone")
async def test_microphone():
    """Test microphone and voice recognition"""
    try:
        print("Testing microphone...")
        command = takecommand()
        
        if command == "nothing" or not command.strip():
            return {
                "message": "Microphone test failed - no speech detected",
                "command": None,
                "success": False
            }
        
        return {
            "message": "Microphone test successful",
            "command": command,
            "success": True
        }
    except Exception as e:
        return {
            "message": f"Microphone test failed: {e}",
            "command": None,
            "success": False
        }

# Background Emotion Detection Control Endpoints

@app.get("/emotion_detector/status")
async def get_emotion_detector_status():
    """Get current status of background emotion detection"""
    try:
        # Load emotion detection if not already loaded
        load_emotion_detection()
        status = emotion_detector.get_status()
        return {
            "status": status,
            "success": True
        }
    except Exception as e:
        return {
            "status": None,
            "success": False,
            "error": str(e)
        }

@app.post("/emotion_detector/start")
async def start_emotion_detector():
    """Start background emotion detection"""
    try:
        # Load emotion detection if not already loaded
        load_emotion_detection()
        emotion_detector.start()
        return {
            "message": "Background emotion detection started",
            "success": True
        }
    except Exception as e:
        return {
            "message": f"Failed to start emotion detection: {e}",
            "success": False,
            "error": str(e)
        }

@app.post("/emotion_detector/stop")
async def stop_emotion_detector():
    """Stop background emotion detection"""
    try:
        # Load emotion detection if not already loaded
        load_emotion_detection()
        emotion_detector.stop()
        return {
            "message": "Background emotion detection stopped",
            "success": True
        }
    except Exception as e:
        return {
            "message": f"Failed to stop emotion detection: {e}",
            "success": False,
            "error": str(e)
        }

@app.post("/emotion_detector/enable")
async def enable_emotion_detector():
    """Enable background emotion detection"""
    try:
        # Load emotion detection if not already loaded
        load_emotion_detection()
        emotion_detector.set_enabled(True)
        return {
            "message": "Background emotion detection enabled",
            "success": True
        }
    except Exception as e:
        return {
            "message": f"Failed to enable emotion detection: {e}",
            "success": False,
            "error": str(e)
        }

@app.post("/emotion_detector/disable")
async def disable_emotion_detector():
    """Disable background emotion detection"""
    try:
        # Load emotion detection if not already loaded
        load_emotion_detection()
        emotion_detector.set_enabled(False)
        return {
            "message": "Background emotion detection disabled",
            "success": True
        }
    except Exception as e:
        return {
            "message": f"Failed to disable emotion detection: {e}",
            "success": False,
            "error": str(e)
        }

@app.post("/emotion_detector/set_interval")
async def set_detection_interval(interval: int = Form(...)):
    """Set detection interval in seconds"""
    try:
        if interval < 1:
            return {
                "message": "Detection interval must be at least 1 second",
                "success": False
            }
        
        # Load emotion detection if not already loaded
        load_emotion_detection()
        emotion_detector.set_detection_interval(interval)
        return {
            "message": f"Detection interval set to {interval} seconds",
            "success": True
        }
    except Exception as e:
        return {
            "message": f"Failed to set detection interval: {e}",
            "success": False,
            "error": str(e)
        }

@app.get("/emotion_detector/current")
async def get_current_emotion():
    """Get current emotion from file"""
    try:
        # Load emotion detection if not already loaded
        load_emotion_detection()
        emotion = emotion_detector.get_current_emotion()
        return {
            "emotion": emotion,
            "success": True
        }
    except Exception as e:
        return {
            "message": f"Failed to get current emotion: {e}",
            "emotion": None,
            "success": False,
            "error": str(e)
        }

@app.get("/emotion_detector/emotion_file")
async def get_emotion_file():
    """Download the current emotion file"""
    try:
        # Load emotion detection if not already loaded
        load_emotion_detection()
        emotion_file_path = emotion_detector.log_file
        if not os.path.exists(emotion_file_path):
            return {
                "message": "Emotion file not found",
                "success": False
            }
        
        return FileResponse(
            path=emotion_file_path,
            filename="current_emotion.txt",
            media_type="text/plain"
        )
    except Exception as e:
        return {
            "message": f"Failed to get emotion file: {e}",
            "success": False,
            "error": str(e)
        }

@app.get("/emotion_detector/ai_with_emotion")
async def get_ai_response_with_emotion():
    """Get AI response that includes current emotion context"""
    try:
        current_emotion = read_current_emotion()
        
        if not current_emotion:
            return {
                "emotion": None,
                "response": "No emotion detected yet. Please ensure the background emotion detection is running and your face is visible.",
                "success": False
            }
        
        # Get AI response with emotion context
        response = bot(f"Please respond to me knowing that I'm currently feeling {current_emotion}")
        
        # Log conversation
        log_conversation(f"[AI with Emotion] Please respond knowing I'm feeling {current_emotion}", response, current_emotion)
        
        return {
            "emotion": current_emotion,
            "response": response,
            "success": True
        }
    except Exception as e:
        return {
            "emotion": None,
            "response": f"Error getting AI response with emotion: {e}",
            "success": False,
            "error": str(e)
        }

@app.get("/conversation/download")
async def download_conversation():
    """Download the conversation log file"""
    try:
        conversation_file = "conversation_log.txt"
        if not os.path.exists(conversation_file):
            return {
                "message": "Conversation log file not found",
                "success": False
            }
        
        return FileResponse(
            path=conversation_file,
            filename="conversation_log.txt",
            media_type="text/plain"
        )
    except Exception as e:
        return {
            "message": f"Failed to get conversation file: {e}",
            "success": False,
            "error": str(e)
        }

@app.get("/memory/status")
async def get_memory_status():
    """Get conversation memory status"""
    try:
        global conversation_memory
        return {
            "memory_entries": len(conversation_memory),
            "recent_conversations": conversation_memory[-5:] if conversation_memory else [],
            "success": True
        }
    except Exception as e:
        return {
            "message": f"Failed to get memory status: {e}",
            "success": False,
            "error": str(e)
        }

@app.post("/memory/clear")
async def clear_memory():
    """Clear conversation memory"""
    try:
        global conversation_memory
        conversation_memory = []
        save_conversation_memory()
        return {
            "message": "Conversation memory cleared successfully",
            "success": True
        }
    except Exception as e:
        return {
            "message": f"Failed to clear memory: {e}",
            "success": False,
            "error": str(e)
        }

@app.get("/memory/download")
async def download_memory():
    """Download the conversation memory file"""
    try:
        memory_file = "conversation_memory.json"
        if not os.path.exists(memory_file):
            return {
                "message": "Memory file not found",
                "success": False
            }
        
        return FileResponse(
            path=memory_file,
            filename="conversation_memory.json",
            media_type="application/json"
        )
    except Exception as e:
        return {
            "message": f"Failed to get memory file: {e}",
            "success": False,
            "error": str(e)
        }

@app.post("/generate_report")
async def generate_report():
    """Generate a mental health analysis report using conversation memory"""
    try:
        # Check if conversation memory exists
        memory_file = "conversation_memory.json"
        if not os.path.exists(memory_file):
            return {
                "message": "No conversation data found. Please have some conversations first.",
                "success": False,
                "error": "No conversation memory"
            }
        
        # Read conversation memory
        with open(memory_file, 'r', encoding='utf-8') as f:
            conversation_data = json.load(f)
        
        if not conversation_data:
            return {
                "message": "No conversation data available. Please have some conversations first.",
                "success": False,
                "error": "Empty conversation memory"
            }
        
        # Create conversation context for analysis
        conversation_context = ""
        for conv in conversation_data:
            conversation_context += f"User: {conv['user']}\n"
            conversation_context += f"AI: {conv['ai']}\n"
            if conv.get('emotion'):
                conversation_context += f"Emotion: {conv['emotion']}\n"
            conversation_context += "---\n"
        
        print("Generating mental health analysis report...")
        
        # Load analysis module if not already loaded
        load_analysis()
        
        # Use the analysis bot to generate the report
        analysis_result = analysis_bot(conversation_context)
        
        # Parse the analysis result (it should be a JSON string)
        try:
            # Clean up the response to extract JSON
            analysis_text = analysis_result.strip()
            if analysis_text.startswith("```json"):
                analysis_text = analysis_text.replace("```json", "").replace("```", "").strip()
            elif analysis_text.startswith("```"):
                analysis_text = analysis_text.replace("```", "").strip()
            
            # Try to parse as JSON
            analysis_data = json.loads(analysis_text)
        except json.JSONDecodeError:
            # If JSON parsing fails, create a structured response
            analysis_data = {
                "analysied_report": analysis_result,
                "root_case": "Analysis completed but format may need review",
                "mental_illness": "Analysis in progress",
                "problem": "Detailed analysis provided in report",
                "recommendation": "Please review the analysis report"
            }
        
        # Add metadata
        report_data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "conversation_count": len(conversation_data),
            "analysis": analysis_data,
            "conversation_data": conversation_data
        }
        
        # Create reports directory if it doesn't exist
        reports_dir = "reports"
        os.makedirs(reports_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"mental_health_report_{timestamp_str}.json"
        report_path = os.path.join(reports_dir, report_filename)
        
        # Save the report
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"Report generated successfully: {report_path}")
        
        return {
            "message": "Mental health analysis report generated successfully",
            "success": True,
            "report_filename": report_filename,
            "report_path": report_path,
            "analysis": analysis_data,
            "conversation_count": len(conversation_data)
        }
        
    except Exception as e:
        print(f"Error generating report: {e}")
        return {
            "message": f"Failed to generate report: {e}",
            "success": False,
            "error": str(e)
        }

@app.get("/reports/list")
async def list_reports():
    """List all available reports"""
    try:
        reports_dir = "reports"
        if not os.path.exists(reports_dir):
            return {
                "reports": [],
                "message": "No reports directory found",
                "success": True
            }
        
        report_files = []
        for filename in os.listdir(reports_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(reports_dir, filename)
                file_stat = os.stat(file_path)
                report_files.append({
                    "filename": filename,
                    "created": datetime.fromtimestamp(file_stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
                    "size": file_stat.st_size
                })
        
        # Sort by creation time (newest first)
        report_files.sort(key=lambda x: x['created'], reverse=True)
        
        return {
            "reports": report_files,
            "count": len(report_files),
            "success": True
        }
        
    except Exception as e:
        return {
            "reports": [],
            "message": f"Failed to list reports: {e}",
            "success": False,
            "error": str(e)
        }

@app.get("/reports/download/{filename}")
async def download_report(filename: str):
    """Download a specific report file"""
    try:
        reports_dir = "reports"
        report_path = os.path.join(reports_dir, filename)
        
        if not os.path.exists(report_path):
            return {
                "message": "Report file not found",
                "success": False
            }
        
        return FileResponse(
            path=report_path,
            filename=filename,
            media_type="application/json"
        )
        
    except Exception as e:
        return {
            "message": f"Failed to download report: {e}",
            "success": False,
            "error": str(e)
        }

@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup"""
    print("FastAPI server starting up...")
    
    # Load conversation memory (lightweight operation)
    print("Loading conversation memory...")
    load_conversation_memory()
    
    print("Server ready! Background emotion detection can be started manually via API.")
    # Warm-up: preload AI model to avoid first-request latency
    try:
        load_google_ai()
        _ = model  # ensure created
        print("AI model preloaded")
    except Exception as e:
        print(f"AI preload skipped: {e}")

    # Do not auto-start background emotion detection; user controls it via UI/API
    try:
        load_emotion_detection()
        emotion_detector.set_enabled(False)
        print("Background emotion detection is disabled by default")
    except Exception as e:
        print(f"Emotion detection initialization skipped: {e}")
    # Mount frontend after API routes to avoid intercepting them
    try:
        if os.path.isdir(frontend_dist):
            # Mount at /ui to match Vite base path
            app.mount("/ui", StaticFiles(directory=frontend_dist, html=True), name="frontend")
            print("Mounted React build at '/ui'")
        else:
            print("React build not found; dev mode expected at http://localhost:5173")
    except Exception as e:
        print(f"Failed to mount React build: {e}")

# Redirect root to UI if mounted
@app.get("/")
async def root_redirect():
    try:
        if os.path.isdir(frontend_dist):
            return RedirectResponse(url="/ui/")
    except Exception:
        pass
    return HTMLResponse(
        content=(
            "<html><body>Backend running. UI available at /ui/ after building the frontend." \
            "</body></html>"
        )
    )

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    print("Shutting down server...")
    
    # Stop emotion detection if it was loaded
    try:
        if emotion_detector is not None:
            print("Stopping background emotion detection...")
            emotion_detector.stop()
    except Exception as e:
        print(f"Error stopping emotion detection: {e}")
    
    # Clean up TTS
    cleanup_tts()

if __name__ == "__main__":
    # Check audio system at startup
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    finally:
        cleanup_tts()
