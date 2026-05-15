"""
backend/utils/secrets.py
Reads secrets from environment variables.
Simplified for local execution.
"""
import os
from dotenv import load_dotenv

load_dotenv()

def get_secret(secret_id: str) -> str:
    return os.getenv(secret_id, "")

GEMINI_API_KEY  = get_secret("GEMINI_API_KEY")
GCP_BUCKET_NAME = get_secret("GCP_BUCKET_NAME") or os.getenv("GCP_BUCKET_NAME", "expenso-receipts")
