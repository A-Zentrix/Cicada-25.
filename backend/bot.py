"""Minimal chatbot backed by Google GenAI with emotion + memory context.

Dependencies:
    pip install google-genai

Env vars:
    GOOGLE_API_KEY          # required
    GOOGLE_GENAI_MODEL      # optional, defaults to 'gemini-2.0-flash-exp'
"""

import os
from typing import Optional, Dict, Final
from google import genai
from google.genai import types
from dotenv import load_dotenv, find_dotenv


# --- Configuration & Globals ---
_GOOGLE_API_KEY_ENV: Final[str] = "GOOGLE_API_KEY"
_MODEL_NAME: Final[str] = os.environ.get("GOOGLE_GENAI_MODEL", "gemini-2.0-flash-exp")

client: Optional[genai.Client] = None

ALLOWED_LANGUAGES: Dict[str, Dict[str, str]] = {
    "en-US": {"name": "English (US)"},
    "en-GB": {"name": "English (UK)"},
    "ta-IN": {"name": "Tamil"},
    "hi-IN": {"name": "Hindi"},
    "es-ES": {"name": "Spanish"},
    "fr-FR": {"name": "French"},
}


def load_google_ai() -> None:
    """Initialize the Google GenAI client once using the API key from env."""
    global client
    if client is not None:
        return

    # Load .env for local/dev if present
    load_dotenv(find_dotenv(), override=False)

    api_key = os.environ.get(_GOOGLE_API_KEY_ENV)
    if not api_key:
        raise RuntimeError(
            f"Missing {_GOOGLE_API_KEY_ENV} environment variable required for Google GenAI"
        )
    client = genai.Client(api_key=api_key)


def _backend_dir() -> str:
    return os.path.dirname(__file__)


def _read_text_file_if_exists(path: str) -> Optional[str]:
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                return content or None
    except Exception:
        return None
    return None


def read_current_emotion() -> Optional[str]:
    """Read current emotion from 'current_emotion.txt' if present."""
    path = os.path.join(_backend_dir(), "current_emotion.txt")
    return _read_text_file_if_exists(path)


def get_conversation_context(max_chars: int = 1500) -> Optional[str]:
    """Read recent conversation history for context, truncated to max_chars."""
    path = os.path.join(_backend_dir(), "conversation_history.txt")
    history = _read_text_file_if_exists(path)
    if not history:
        return None
    if len(history) > max_chars:
        return history[-max_chars:]
    return history


def _append_history(role: str, text: str) -> None:
    try:
        path = os.path.join(_backend_dir(), "conversation_history.txt")
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"{role}: {text}\n")
    except Exception:
        pass


def bot(prompt: str, language: str = "en-US") -> str:
    """AI bot with intelligent responses, emotion awareness, memory, and language support."""
    try:
        load_google_ai()
    except Exception as init_error:
        print(f"AI init error: {init_error}")
        return "The AI is not configured. Please set GOOGLE_API_KEY and try again."

    current_emotion = read_current_emotion()
    conversation_context = get_conversation_context()

    emotion_context = ""
    if current_emotion:
        emotion_context = (
            f"IMPORTANT: The user currently seems to feel {current_emotion}. "
            "Use this emotional context to respond empathetically. "
        )

    memory_context = ""
    if conversation_context:
        memory_context = (
            "CONVERSATION MEMORY: Use the recent history below as context to keep continuity. "
            f"{conversation_context} "
        )

    language_context = ""
    if language:
        normalized = language.replace('_', '-')
        meta = ALLOWED_LANGUAGES.get(normalized)
        if meta:
            language_context = f"LANGUAGE REQUIREMENT: Respond strictly in {meta['name']}. "

    system_preamble = (
        "You are a compassionate and highly intelligent mental wellness assistant. "
        "Prioritize empathy, avoid judgment, acknowledge feelings, and keep responses concise. "
        "Provide actionable advice only if the user seeks it. "
        "Encourage healthy coping mechanisms and suggest professional help when appropriate. "
        "Keep each reply within 20 to 30 words, no symbols, a single paragraph. "
    )

    try:
        assert client is not None
        full_prompt = (
            f"{system_preamble}{language_context}{emotion_context}{memory_context}"
            f"User input: {prompt}"
        )
        response = client.models.generate_content(
            model=_MODEL_NAME,
            contents=full_prompt,
        )

        text = getattr(response, "text", None)
        if not text:
            try:
                candidates = getattr(response, "candidates", None)
                if candidates and len(candidates) > 0:
                    text = candidates[0].content.parts[0].text
            except Exception:
                text = None

        reply = text or "I'm sorry, I couldn't generate a response just now. Please try again."

        _append_history("user", prompt)
        _append_history("assistant", reply)
        return reply
    except Exception as e:
        print(f"AI response error: {e}")
        return "I'm sorry, I'm having trouble responding right now. Please try again."
