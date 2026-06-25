"""
Chat API — streaming endpoint that calls Claude with access to MCP tools.
"""
import json
import os

from fastapi import APIRouter
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from app.services.chat_service import stream_chat

router = APIRouter(prefix="/chat", tags=["chat"])

DEFAULT_MODEL = "claude-haiku-4-5-20251001"


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    model: str = DEFAULT_MODEL


@router.get("/providers")
def get_providers():
    """Returns available AI providers and whether they're configured."""
    return {
        "anthropic": {
            "name": "Claude",
            "available": bool(os.getenv("ANTHROPIC_API_KEY")),
            "default_model": DEFAULT_MODEL,
        }
    }


@router.post("/message")
async def chat_message(request: ChatRequest):
    """
    Stream a chat response as Server-Sent Events. Each event is a JSON object:
      {"type": "tool_call",   "tool": "..."}
      {"type": "tool_result", "tool": "...", "success": true}
      {"type": "text",        "content": "..."}
      {"type": "done"}
      {"type": "error",       "message": "..."}
    """
    messages = [{"role": m.role, "content": m.content} for m in request.messages]

    async def event_generator():
        async for event in stream_chat(messages, request.model):
            yield {"data": json.dumps(event)}

    return EventSourceResponse(event_generator())
