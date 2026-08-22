"""
AI 智能问答接口
POST /api/v1/ai/chat  —— 流式对话（SSE）
"""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional
import json

from app.services.ai_service import stream_chat, AIConfigError

router = APIRouter()


class ChatRequest(BaseModel):
    messages: list[dict] = Field(..., description="对话消息列表，格式 [{role, content}]")
    temperature: float = Field(0.6, ge=0, le=2)


@router.post("/chat")
async def ai_chat(req: ChatRequest, request: Request):
    """流式 AI 对话，返回 SSE 格式"""
    ai_key = request.headers.get("X-AI-API-Key", "")
    ai_provider = request.headers.get("X-AI-Provider", "deepseek")
    ai_base_url = request.headers.get("X-AI-Base-URL", "")
    ai_model = request.headers.get("X-AI-Model", "")

    async def event_stream():
        try:
            async for delta in stream_chat(
                messages=req.messages,
                api_key=ai_key,
                provider=ai_provider,
                base_url=ai_base_url,
                model=ai_model,
                temperature=req.temperature,
            ):
                yield f"data: {json.dumps({'delta': delta}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        except AIConfigError as e:
            yield f"data: {json.dumps({'error': e.message, 'code': e.code}, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")