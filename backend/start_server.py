#!/usr/bin/env python3
"""
Fast startup script for the AI Mental Wellness Chatbot
This script provides a quick way to start the server with minimal overhead
"""

import uvicorn
import sys
import os
from pathlib import Path

def main():
    """Start the server with optimized settings"""
    print("🚀 Starting AI Mental Wellness Chatbot...")
    print("📝 Note: Heavy AI models will load only when first used")
    print("⚡ This should start much faster now!")
    print("-" * 50)
    
    # Change to the script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    try:
        # Start the server with optimized settings
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=False,  # Disable reload for faster startup
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
