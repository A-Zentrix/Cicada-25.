"""FastAPI server exposing the chatbot and serving a simple frontend.

Run:
  export GOOGLE_API_KEY="your_key"
  uvicorn backend.server:app --reload
"""

from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .bot import bot


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, description="User message")
    language: Optional[str] = Field(default="en-US", description="BCP-47 tag like en-US")


class ChatResponse(BaseModel):
    reply: str


app = FastAPI(title="Cicada-25 Chatbot", version="0.1.0")

# Allow local dev origins; tighten for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    try:
        reply = bot(req.message, language=req.language or "en-US")
        return ChatResponse(reply=reply)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Serve the basic frontend from ../frontend
app.mount("/", StaticFiles(directory=str(__file__).rsplit("/", 2)[0] + "/../frontend", html=True), name="static")


