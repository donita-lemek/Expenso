"""
backend/utils/secrets.py
Reads secrets from GCP Secret Manager in production;
falls back to environment variables in local dev.
"""
from google.cloud import secretmanager
import os
from dotenv import load_dotenv

load_dotenv()

def get_secret(secret_id: str) -> str:
    env = os.getenv("ENV", "local")
    if env == "local":
        return os.getenv(secret_id, "")

    client = secretmanager.SecretManagerServiceClient()
    project_id = os.getenv("GCP_PROJECT_ID", "expenso-app")
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    try:
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception:
        return ""

GEMINI_API_KEY  = get_secret("GEMINI_API_KEY")
GCP_BUCKET_NAME = get_secret("GCP_BUCKET_NAME") or os.getenv("GCP_BUCKET_NAME", "expenso-receipts")
