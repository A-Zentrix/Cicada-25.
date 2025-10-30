# AI Mental Wellness Chatbot

A FastAPI-based mental wellness chatbot with emotion detection and voice interaction capabilities.

## Features

- **Text Chat**: Send messages to the AI assistant
- **Emotion Detection**: Uses camera to detect facial emotions
- **Voice Commands**: Speak to the chatbot using voice recognition
- **Text-to-Speech**: AI responses are spoken aloud
- **Modern UI**: Clean, responsive web interface
- **Fast Startup**: Optimized with lazy loading for quick server startup

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure you have a webcam connected for emotion detection

## Running the Application

### Quick Start (Recommended)
```bash
python start_server.py
```

### Alternative Method
```bash
python main.py
```

### Test Startup Performance
```bash
python test_startup.py
```

2. Open your web browser and go to:
```
http://localhost:8000
```

## Performance Optimizations

This application has been optimized for fast startup and better user experience:

- **Lazy Loading**: Heavy AI models (DeepFace, TensorFlow, Google AI) only load when first used
- **Background Services**: Emotion detection starts manually via API, not automatically
- **Modular Imports**: Components load on-demand to reduce initial startup time
- **Startup Script**: Use `start_server.py` for the fastest startup experience
- **Smart TTS Rates**: Language-specific speech speeds for natural-sounding voice output

The server should now start in under 5 seconds instead of 30+ seconds!

## TTS (Text-to-Speech) Improvements

The TTS system has been optimized for different languages:

- **Asian Languages** (Chinese, Japanese, Korean): 120-130 WPM (much slower for clarity)
- **Slavic Languages** (Russian, Polish, etc.): 140 WPM (slower for better understanding)
- **Romance Languages** (Spanish, French, Italian, etc.): 150 WPM (moderate speed)
- **Germanic Languages** (German, Dutch, Swedish, etc.): 160 WPM (moderate speed)
- **English Variants**: 180 WPM (faster, as English speakers are used to this speed)

### Test TTS Speeds
```bash
python test_tts_speeds.py
```

### Customize Speech Rates
You can adjust speech rates via API:
- `GET /tts/rate/{language}` - Get current rate for a language
- `POST /tts/rate/{language}` - Set custom rate (50-300 WPM)
- `GET /tts/rates` - View all language rates
- `POST /tts/test_rate` - Test speech with custom rate

## Usage

- **Text Chat**: Type your message in the input field and click Send or press Enter
- **Detect Emotion**: Click the "Detect Emotion" button to analyze your facial expression
- **Voice Command**: Click the "Voice Command" button to speak to the chatbot

## API Endpoints

- `GET /`: Main web interface
- `POST /detect_emotion`: Detect emotion from camera
- `POST /send_message`: Send text message to AI
- `POST /voice_command`: Process voice command
- `POST /speak`: Convert text to speech

## Dependencies

- FastAPI: Web framework
- Google Generative AI: AI chatbot
- OpenCV: Camera and face detection
- DeepFace: Emotion analysis
- pyttsx3: Text-to-speech
- SpeechRecognition: Voice input
