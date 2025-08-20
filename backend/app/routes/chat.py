from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.services.bedrock import BedrockService

router = APIRouter()
bedrock = BedrockService()

@router.post("/chat")
async def chat(request: dict):
    user_input = request.get("prompt", "")
    response = bedrock.query_model(user_input)
    return JSONResponse(content={"response": response})
