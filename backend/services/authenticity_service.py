"""
backend/services/authenticity_service.py
Gemini API — forensic receipt authenticity scoring.
"""
import google.generativeai as genai
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from backend.utils.helpers import safe_json_parse
from backend.utils.secrets import GEMINI_API_KEY

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = (
    "You are a forensic document analyst specializing in detecting fraudulent or digitally "
    "altered receipts. Return only valid JSON with no markdown or code fences."
)

FALLBACK = {
    "forgery_risk": "Medium",
    "confidence": 0.5,
    "reasoning": "Authenticity check failed.",
    "specific_flags": ["AI analysis error"],
    "is_screenshot": False,
    "font_consistent": True,
    "has_standard_elements": True,
}


async def score_authenticity(image_bytes: bytes, ocr_data: dict) -> dict:
    if not GEMINI_API_KEY:
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

    user_prompt = f"""Examine this receipt image carefully for signs of tampering or forgery. specifically check for:
1. Font inconsistencies
2. Pixel artifacts or JPEG compression anomalies around amounts
3. Evidence this is a screenshot rather than an original physical receipt
4. Misaligned text or spacing anomalies
5. Missing standard receipt elements
6. Inconsistencies between this OCR data and the layout: {json.dumps(ocr_data)}

Return ONLY this exact JSON:
{{
  "forgery_risk": "Low or Medium or High",
  "confidence": 0.9,
  "reasoning": "2-3 sentences",
  "specific_flags": ["list of specific issues found"],
  "is_screenshot": false,
  "font_consistent": true,
  "has_standard_elements": true
}}"""

    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=SYSTEM_PROMPT
    )

    try:
        response = model.generate_content([image_part, user_prompt])
        result = safe_json_parse(response.text, None)
        return result if result else FALLBACK
    except Exception as e:
        print(f"⚠️  Authenticity check failed: {e}")
        return FALLBACK
