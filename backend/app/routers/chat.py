import json
import logging

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.config import settings
from app.deps import CurrentUser, DbSession
from app.schemas import ChatRequest, ChatResponse
from app.services.chat import answer_chat, chat_events
from app.services.rate_limit import SlidingWindowRateLimiter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])

chat_rate_limiter = SlidingWindowRateLimiter(settings.chat_rate_limit_per_minute)


def _frame(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def _sse(db, user, payload: ChatRequest):
    try:
        async for event in chat_events(db, user, payload):
            yield _frame(event["type"], event)
    except Exception:
        logger.exception("Chat stream failed")
        yield _frame(
            "error",
            {"message": "I couldn't finish that answer. Please retry."},
        )


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, user: CurrentUser, db: DbSession):
    chat_rate_limiter.check(str(user.id))
    if payload.stream:
        return StreamingResponse(
            _sse(db, user, payload),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-transform",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    return await answer_chat(db, user, payload)
