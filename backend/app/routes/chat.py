from app.services.bedrock import stream_bedrock_response
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

router = APIRouter()


@router.post("/stream")
async def chat_stream(request: Request):
    data = await request.json()
    user_input = data.get("input", "")
    mode = data.get("mode", "General Chat")

    if not user_input.strip():
        return StreamingResponse(
            iter(['data: {"text": "⚠️ Empty input"}\n\n']),
            media_type="text/event-stream",
        )

    def event_stream():
        for chunk in stream_bedrock_response(user_input, mode):
            yield f"data: {chunk}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
