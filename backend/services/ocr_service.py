"""
backend/services/ocr_service.py
Gemini API — receipt OCR extraction.
"""
import google.generativeai as genai
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from backend.utils.helpers import safe_json_parse
from backend.utils.secrets import GEMINI_API_KEY

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = (
    "You are a receipt OCR specialist. Extract structured data from receipt images "
    "with high precision. Always return valid JSON with no markdown formatting."
)

USER_PROMPT = """You are a high-precision receipt OCR extractor. Analyze this receipt image and extract structured fields.
Focus first on identifying the merchant/shop name — it is usually the largest or most prominent text near the top of the receipt. If multiple candidates exist, choose the one that looks like a business name (no timestamps, try to ignore handwritten notes). If you are uncertain, still attempt your best guess rather than returning null.

Return ONLY this exact JSON structure (no extra commentary):
{
    "merchant_name": "string or null",
    "transaction_date": "YYYY-MM-DD or null",
    "transaction_time": "HH:MM or null",
    "total_amount": "float or null",
    "currency": "3-letter ISO code e.g. USD GBP EUR or null",
    "subtotal": "float or null",
    "tax_amount": "float or null",
    "tip_amount": "float or null",
    "line_items": [{"description": "string", "amount": "float"}],
    "receipt_quality": "Clear or Blurry or Partial",
    "quality_note": "string",
    "ocr_confidence": "float between 0 and 1"
}

If any field cannot be determined, use null. For merchant_name, prefer business-like text (e.g. 'THE LONDON BISTRO', 'Marriott Chicago') and avoid filenames, timestamps, or camera-generated labels.
"""

FALLBACK = {
    "merchant_name": None,
    "transaction_date": None,
    "transaction_time": None,
    "total_amount": None,
    "currency": None,
    "subtotal": None,
    "tax_amount": None,
    "tip_amount": None,
    "line_items": [],
    "receipt_quality": "Partial",
    "quality_note": "OCR extraction failed — manual review required.",
    "ocr_confidence": 0.0,
}


async def extract_receipt_data(image_bytes: bytes) -> dict:
    if not GEMINI_API_KEY:
        print("⚠️  No Gemini API Key found.")
        return FALLBACK

    mime_type = "image/jpeg"
    if image_bytes[:8] == b"\x89PNG\r\n\x1a\n":
        mime_type = "image/png"
    elif image_bytes[:4] == b"%PDF":
        mime_type = "application/pdf"

    image_part = {
        "mime_type": mime_type,
        "data": image_bytes
    }

    model = genai.GenerativeModel(
        model_name="gemini-2.5-pro",
        system_instruction=SYSTEM_PROMPT
    )

    try:
        response = model.generate_content([image_part, USER_PROMPT])
        result = safe_json_parse(response.text, None)
        return result if result else FALLBACK
    except Exception as e:
        print(f"⚠️  OCR attempt failed: {e}")
        return FALLBACK
