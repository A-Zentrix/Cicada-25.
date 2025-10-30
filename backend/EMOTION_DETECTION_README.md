# Background Emotion Detection System

This document describes the background emotion detection feature that runs parallel to the main AI Mental Wellness Chatbot application.

## Overview

The background emotion detection system continuously monitors facial expressions using the camera and logs detected emotions to a text file. It runs in a separate thread, allowing it to operate independently of the main chatbot functionality.

## Features

- **Continuous Monitoring**: Runs in the background without interrupting the main app
- **Configurable Interval**: Set detection frequency (1-60 seconds)
- **Emotion Logging**: Stores emotions with timestamps and confidence scores
- **Real-time Control**: Start, stop, enable, or disable detection via web interface
- **Data Export**: Download emotion logs as text files
- **Status Monitoring**: View current detection status and recent emotions

## Files Added

### `background_emotion.py`
Main module containing the `BackgroundEmotionDetector` class with the following key methods:

- `start()`: Start background emotion detection
- `stop()`: Stop background emotion detection
- `set_enabled(enabled)`: Enable or disable detection
- `set_detection_interval(interval)`: Set detection frequency
- `get_status()`: Get current detector status
- `get_recent_emotions(count)`: Get recent emotion data
- `_log_emotion()`: Log emotion to text file

### API Endpoints Added

The following new endpoints are available in `main.py`:

- `GET /emotion_detector/status` - Get detector status
- `POST /emotion_detector/start` - Start detection
- `POST /emotion_detector/stop` - Stop detection
- `POST /emotion_detector/enable` - Enable detection
- `POST /emotion_detector/disable` - Disable detection
- `POST /emotion_detector/set_interval` - Set detection interval
- `GET /emotion_detector/recent` - Get recent emotions
- `GET /emotion_detector/log_file` - Download emotion log

### Web Interface Updates

- **HTML**: Added emotion detection control panel in `templates/index.html`
- **CSS**: Added styling for emotion controls in `static/style.css`
- **JavaScript**: Added control functions in `static/script.js`

## Usage

### Starting the Application

The background emotion detection starts automatically when the main application starts:

```bash
python main.py
```

### Web Interface Controls

1. **Start Detection**: Click "Start Detection" to begin monitoring
2. **Stop Detection**: Click "Stop Detection" to pause monitoring
3. **Enable/Disable**: Toggle detection on/off
4. **Set Interval**: Adjust detection frequency (1-60 seconds)
5. **View Recent**: See the last 10 detected emotions
6. **Download Log**: Download the complete emotion log file
7. **Get Status**: View current detector status

### Configuration

The detector can be configured by modifying the `BackgroundEmotionDetector` initialization in `main.py`:

```python
emotion_detector = BackgroundEmotionDetector(
    detection_interval=5,  # seconds between detections
    log_file="emotion_log.txt",  # log file path
    enabled=True  # start enabled
)
```

## Log File Format

Emotions are logged to a CSV file with the following format:

```
Timestamp,Emotion,Confidence,Face_Detected
2024-01-15 14:30:25,happy,85.23,Yes
2024-01-15 14:30:30,neutral,72.15,Yes
2024-01-15 14:30:35,no_face,0.00,No
```

## Testing

Run the test script to verify the emotion detection system:

```bash
python test_emotion_detection.py
```

This will:
- Create a test detector
- Run detection for 20+ seconds
- Test all major functions
- Display results and clean up

## Technical Details

### Threading
- Uses Python's `threading` module
- Runs as a daemon thread (automatically stops when main app stops)
- Non-blocking operation

### Camera Access
- Uses OpenCV for camera access
- Automatically handles camera initialization and cleanup
- Graceful error handling for camera issues

### Emotion Detection
- Uses DeepFace library for emotion analysis
- Supports 7 basic emotions: angry, disgust, fear, happy, sad, surprise, neutral
- Includes confidence scores for each detection

### Error Handling
- Comprehensive error handling and logging
- Graceful degradation when camera is unavailable
- Automatic retry mechanisms for failed detections

## Requirements

The following additional dependencies are required (already in `requirements.txt`):

- `opencv-python==4.8.1.78`
- `deepface==0.0.79`
- `tensorflow==2.13.0`

## Troubleshooting

### Camera Issues
- Ensure camera permissions are granted
- Check if camera is being used by another application
- Verify camera hardware is working

### Detection Issues
- Ensure good lighting conditions
- Position face clearly in camera view
- Check if face detection models are properly loaded

### Performance Issues
- Increase detection interval to reduce CPU usage
- Close other camera-using applications
- Ensure adequate system resources

## Security and Privacy

- All processing is done locally
- No data is sent to external servers
- Emotion logs are stored locally only
- Camera access is only used for emotion detection

## Future Enhancements

Potential improvements for the emotion detection system:

1. **Real-time Dashboard**: Live emotion visualization
2. **Emotion Trends**: Historical emotion analysis
3. **Mood Tracking**: Long-term emotional state monitoring
4. **Alerts**: Notifications for concerning emotional patterns
5. **Data Analytics**: Statistical analysis of emotional data
6. **Export Options**: Multiple file formats (JSON, CSV, Excel)
7. **Cloud Storage**: Optional cloud backup of emotion data
