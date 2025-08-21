import boto3
import os
import json
from app.services.rag import retrieve_context

bedrock = boto3.client(
    "bedrock-runtime",
    region_name=os.getenv("AWS_DEFAULT_REGION"),
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
        "max_tokens": 300,
    }

    response = bedrock.invoke_model(
        modelId=MODEL_ID,
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json",
    )

    result = json.loads(response["body"].read().decode("utf-8"))

    # Yield JSON string so frontend can parse model/usage
    yield json.dumps(result)
