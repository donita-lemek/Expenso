"""
backend/services/audit_service.py
Core XAI Engine — policy compliance audit using Gemini.
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

SYSTEM_PROMPT = """You are a senior corporate expense compliance auditor with 20 years of experience. \
You make precise, evidence-based decisions and always explain your reasoning in full. \
You cite exact numbers, exact policy sections, and exact rules. \
You never say "policy violation" without specifying which rule, which number, \
and by exactly how much.
Return ONLY valid JSON. No markdown. No preamble. No text before or after the JSON object. \
Start with { and end with }."""

AUDIT_PROMPT_TEMPLATE = """## EMPLOYEE CONTEXT
Name: {name}
City: {city} (Tier {tier})
Department: {department}
Expense Category: {category}

## RECEIPT DATA
Merchant: {merchant}
Date: {date}
Original Amount: {amount} {currency}
Converted to USD: ${usd_amount}
Exchange Rate: {rate} ({source})

## INTEGRITY SIGNALS
Forgery Risk: {forgery_risk}
Specific Forgery Flags: {forgery_flags}
Duplicate: {duplicate_message}
Rate Manipulation: {rate_manipulation_flag}

## EMPLOYEE JUSTIFICATION
"{business_purpose}"

## COMPANY POLICY
{policy_text}

## TASK
Perform a complete compliance audit. Return this EXACT JSON structure (no markdown):
{{
  "status": "Approved or Flagged or Rejected",
  "risk_score": 0,
  "explanation": "One precise sentence with exact numbers and section citation.",
  "ai_confidence": 0.0,
  "uncertainty_notes": "string or null",
  "decision_factors": [
    {{
      "factor": "string",
      "weight": "HIGH or MEDIUM or LOW",
      "result": "PASS or FAIL or WARNING",
      "detail": "string",
      "data_used": {{}}
    }}
  ],
  "policy_evidence": {{
    "section": "string",
    "section_title": "string",
    "full_text": "string",
    "applied_rule": "string",
    "matching_reason": "string"
  }},
  "confidence_breakdown": {{
    "ocr_confidence": 0.0,
    "policy_match_confidence": 0.0,
    "overall_confidence": 0.0,
    "low_confidence_reasons": []
  }},
  "counterfactuals": ["string"],
  "violations": ["string"],
  "warnings": ["string"]
}}"""

FALLBACK = {
    "status": "Flagged",
    "risk_score": 50,
    "explanation": "Manual review required — AI parsing error.",
    "ai_confidence": 0.0,
    "decision_factors": [],
    "counterfactuals": ["Resubmit claim for manual review."],
    "violations": [],
    "warnings": ["AI audit engine error."],
}


async def run_policy_audit(claim_data: dict, policy_text: str) -> dict:
    if not GEMINI_API_KEY:
        return dict(FALLBACK)

    prompt = AUDIT_PROMPT_TEMPLATE.format(
        name=claim_data.get("employee_name", "Unknown"),
        city=claim_data.get("city", "Unknown"),
        tier=claim_data.get("city_tier", "C"),
        department=claim_data.get("department", "Unknown"),
        category=claim_data.get("category", "Other"),
        merchant=claim_data.get("merchant", "Unknown"),
        date=claim_data.get("transaction_date", "Unknown"),
        amount=claim_data.get("claimed_amount", 0.0),
        currency=claim_data.get("original_currency", "USD"),
        usd_amount=claim_data.get("converted_amount_usd", 0.0),
        rate=claim_data.get("exchange_rate", 1.0),
        source=claim_data.get("exchange_rate_source", "N/A"),
        forgery_risk=claim_data.get("forgery_risk", "Low"),
        forgery_flags=json.dumps(claim_data.get("forgery_flags", [])),
        duplicate_message=claim_data.get("duplicate_message", "None"),
        rate_manipulation_flag=claim_data.get("rate_manipulation_flag", False),
        business_purpose=claim_data.get("business_purpose", "Not provided"),
        policy_text=policy_text,
    )

    model = genai.GenerativeModel(
        model_name="gemini-2.5-pro",
        system_instruction=SYSTEM_PROMPT,
    )

    try:
        response = model.generate_content(prompt)
        result = safe_json_parse(response.text, None)
        if result:
            result["_raw_response"] = response.text
            result["_prompt_sent"] = prompt
            return result
    except Exception as e:
        print(f"⚠️  Audit failed: {e}")

    fallback = dict(FALLBACK)
    fallback["_raw_response"] = "Parse error"
    fallback["_prompt_sent"] = prompt
    return fallback
