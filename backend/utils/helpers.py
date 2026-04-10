"""
backend/utils/helpers.py
Shared utility functions: serialization, hashing, GCS upload, JSON parsing.
"""
import hashlib
import json
import re
import uuid
import base64
import os
from datetime import datetime
from typing import Any, Dict, Optional
from io import BytesIO


# ── MongoDB serialization ─────────────────────────────────

def serialize_doc(doc: Dict) -> Dict:
    """Convert MongoDB document: ObjectId → str, datetime → ISO string."""
    if doc is None:
        return {}
    result = {}
    for key, value in doc.items():
        if key == "_id":
            result["_id"] = str(value)
        elif isinstance(value, datetime):
            result[key] = value.isoformat()
        elif isinstance(value, dict):
            result[key] = serialize_doc(value)
        elif isinstance(value, list):
            result[key] = [
                serialize_doc(item) if isinstance(item, dict) else
                item.isoformat() if isinstance(item, datetime) else
                str(item) if hasattr(item, "__class__") and item.__class__.__name__ == "ObjectId" else item
                for item in value
            ]
        else:
            result[key] = value
    return result


# ── Claim ID generation ───────────────────────────────────

def generate_claim_id() -> str:
    """Generate a unique claim ID in CLM-XXXXXX format."""
    suffix = uuid.uuid4().hex[:6].upper()
    return f"CLM-{suffix}"


# ── Hashing ───────────────────────────────────────────────

def compute_sha256(image_bytes: bytes) -> str:
    """Return the SHA256 hex digest of image bytes."""
    return hashlib.sha256(image_bytes).hexdigest()


# ── GCS Upload / local base64 fallback ───────────────────

def upload_to_gcs(image_bytes: bytes, filename: str) -> str:
    """
    Upload image to GCP Cloud Storage and return a signed URL.
    Falls back to a base64 data URI in local dev (ENV=local).
    """
    env = os.getenv("ENV", "local")

    if env == "local":
        # Local fallback: store as base64 data URI
        ext = filename.rsplit(".", 1)[-1].lower()
        mime_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg",
                    "png": "image/png", "pdf": "application/pdf"}
        mime = mime_map.get(ext, "application/octet-stream")
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        return f"data:{mime};base64,{b64}"

    try:
        from google.cloud import storage
        bucket_name = os.getenv("GCP_BUCKET_NAME", "expenso-receipts")
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(f"receipts/{filename}")
        blob.upload_from_string(image_bytes, content_type="image/jpeg")

        # Return a signed URL valid for 1 hour
        from datetime import timedelta
        url = blob.generate_signed_url(expiration=timedelta(hours=1), method="GET")
        return url
    except Exception as e:
        print(f"⚠️  GCS upload failed, falling back to base64: {e}")
        ext = filename.rsplit(".", 1)[-1].lower()
        mime_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg",
                    "png": "image/png", "pdf": "application/pdf"}
        mime = mime_map.get(ext, "application/octet-stream")
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        return f"data:{mime};base64,{b64}"


# ── JSON parsing ──────────────────────────────────────────

def safe_json_parse(text: str, fallback: Optional[Dict] = None) -> Dict:
    """
    Strip markdown code fences and parse JSON.
    Returns fallback dict on failure.
    """
    if fallback is None:
        fallback = {}
    try:
        # Remove ```json ... ``` or ``` ... ``` fences
        cleaned = re.sub(r"```(?:json)?", "", text).strip()
        # Sometimes models wrap in extra text — try to find the JSON object
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(0)
        return json.loads(cleaned)
    except (json.JSONDecodeError, AttributeError):
        return fallback


def now_iso() -> str:
    """Return current UTC time as ISO string."""
    return datetime.utcnow().isoformat()


def humanize_filename(filename: str) -> str:
    """Turn a raw filename into a human-friendly label.
    Removes timestamps, common camera prefixes, and file extensions.
    """
    if not filename:
        return ""
    name = filename.rsplit("/", 1)[-1]
    # remove extension
    if "." in name:
        name = name.rsplit(".", 1)[0]
    # replace underscores and dashes with spaces
    name = re.sub(r"[_\-]+", " ", name)
    # remove common camera/utility prefixes
    name = re.sub(r"(?i)^(chatgpt|img|image|photo|receipt)\b", "", name).strip()
    # remove date-like parts e.g. Apr 10, 2026 or 2026_04_10 or 12_16_21_PM
    name = re.sub(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b[\w\s,\-]*", "", name)
    name = re.sub(r"\b\d{4}[_\-]\d{2}[_\-]\d{2}\b", "", name)
    name = re.sub(r"\b\d{1,2}[_\-]\d{2}[_\-]\d{2}(?:[_\-]AM|[_\-]PM|AM|PM)?\b", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\s+", " ", name).strip()
    return name or ""
