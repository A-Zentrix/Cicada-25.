# To run this code you need to install the following dependencies:
# pip install google-genai

import base64
import os
from google import genai
from google.genai import types


def generate():
    client = genai.Client(
        api_key=os.environ.get("AIzaSyA3f8izcUDNQTik3utegfZ5bKvxeG0vwq8"),
    )

    model = "gemini-2.5-flash-lite"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text="""hello"""),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        thinking_config = types.ThinkingConfig(
            thinking_budget=0,
        ),
        image_config=types.ImageConfig(
            image_size="1K",
        ),
    )

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        print(chunk.text, end="")

if __name__ == "__main__":
    generate()
