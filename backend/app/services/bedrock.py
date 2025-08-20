import os
import boto3
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(os.path.join(os.path.dirname(__file__), "../../..", ".env"))

class BedrockService:
    def __init__(self):
        self.client = boto3.client(
            service_name="bedrock-runtime",
            region_name=os.getenv("AWS_DEFAULT_REGION"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
        )
        self.model_id = "anthropic.claude-v2:1"  # Example model

    def query_model(self, prompt: str) -> str:
        response = self.client.invoke_model(
            modelId=self.model_id,
            contentType="application/json",
            accept="application/json",
            body=f'{{"prompt": "{prompt}", "max_tokens_to_sample": 200}}'
        )
        return response["body"].read().decode("utf-8")
