from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from app.services.bedrock import stream_bedrock_response

router = APIRouter()

@router.post("/")
async def chat(request: Request):
    body = await request.json()
    user_message = body.get("message", "")
    mode = body.get("mode", "General Chat")  # 👈 pick up the mode from frontend

    async def event_stream():
        for chunk in stream_bedrock_response(user_message, mode=mode):  # 👈 forward mode
            yield chunk

    return StreamingResponse(event_stream(), media_type="text/event-stream")
