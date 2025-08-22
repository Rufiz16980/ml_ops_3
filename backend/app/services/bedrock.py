import boto3
import os
import json
from dotenv import load_dotenv
from app.services.rag import retrieve_context

# Load .env so boto3 can pick up AWS credentials
load_dotenv()

# Create Bedrock client with explicit credentials if present
bedrock = boto3.client(
    "bedrock-runtime",
    region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    aws_session_token=os.getenv("AWS_SESSION_TOKEN"),  # optional
)

MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")


def stream_bedrock_response(prompt: str, mode: str = "General Chat"):
    """Handles both General Chat and Knowledge Base (RAG) chat."""
    # Inject retrieved knowledge if in RAG mode
    if mode == "Knowledge Base (RAG)":
        retrieved = retrieve_context(prompt)
        if retrieved:
            prompt = f"Use the following context to answer:\n{retrieved}\n\nUser question: {prompt}"

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
        "max_tokens": 500,
    }

    try:
        response = bedrock.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )
        result = json.loads(response["body"].read().decode("utf-8"))
    except Exception as e:
        yield json.dumps(
            {"text": f"Backend error: {e}", "model": MODEL_ID, "usage": {}}
        )
        return

    # Extract the assistant text output
    text_output = ""
    if "content" in result and len(result["content"]) > 0:
        for block in result["content"]:
            if block.get("type") == "text":
                text_output += block.get("text", "")

    output = {
        "text": text_output.strip() if text_output else "(no response)",
        "model": result.get("model", MODEL_ID),
        "usage": result.get("usage", {}),
    }

    yield json.dumps(output)
