"""
backend/services/xai_service.py
Audit trail builder — creates an immutable ordered event log
of every pipeline step for full explainability.
"""
from datetime import datetime
from typing import List, Dict, Any


def _event(event: str, detail: str, metadata: dict = None) -> dict:
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "event": event,
        "detail": detail,
        "metadata": metadata or {},
    }


def build_audit_trail(pipeline: dict) -> List[Dict[str, Any]]:
    """
    Build an ordered, immutable audit trail from all pipeline results.

    pipeline keys expected:
        receipt_filename, receipt_size, receipt_format,
        ocr_result, duplicate_result, currency_result,
        authenticity_result, audit_result,
        policy_version, category, city_tier, claim_id
    """
    trail = []

    # ── RECEIPT_UPLOADED ──────────────────────────────────
    trail.append(_event(
        "RECEIPT_UPLOADED",
        f"Receipt file received: {pipeline.get('receipt_filename', 'unknown')}",
        {
            "filename": pipeline.get("receipt_filename"),
            "size_bytes": pipeline.get("receipt_size"),
            "format": pipeline.get("receipt_format"),
        },
    ))

    # ── OCR_COMPLETE ──────────────────────────────────────
    ocr = pipeline.get("ocr_result", {})
    trail.append(_event(
        "OCR_COMPLETE",
        (
            f"Merchant: {ocr.get('merchant_name', 'N/A')} | "
            f"Date: {ocr.get('transaction_date', 'N/A')} | "
            f"Amount: {ocr.get('total_amount', 'N/A')} {ocr.get('currency', '')} | "
            f"OCR confidence: {ocr.get('ocr_confidence', 0):.0%}"
        ),
        {
            "merchant": ocr.get("merchant_name"),
            "date": ocr.get("transaction_date"),
            "amount": ocr.get("total_amount"),
            "currency": ocr.get("currency"),
            "quality": ocr.get("receipt_quality"),
            "confidence": ocr.get("ocr_confidence"),
        },
    ))

    # ── DUPLICATE_CHECK ───────────────────────────────────
    dup = pipeline.get("duplicate_result", {})
    if dup.get("is_duplicate"):
        trail.append(_event(
            "DUPLICATE_CHECK_FAIL",
            (
                f"Duplicate detected ({dup.get('detection_layer', 'unknown')} layer) — "
                f"{dup.get('similarity_score', 0):.1f}% similar to {dup.get('duplicate_of', 'N/A')}"
            ),
            {
                "duplicate_of": dup.get("duplicate_of"),
                "similarity_score": dup.get("similarity_score"),
                "layer": dup.get("detection_layer"),
            },
        ))
    else:
        trail.append(_event(
            "DUPLICATE_CHECK_PASS",
            "No duplicate receipts found across all detection layers.",
            {"layers_checked": ["exact_sha256", "phash_visual", "semantic"]},
        ))

    # ── CURRENCY_CONVERTED ────────────────────────────────
    fx = pipeline.get("currency_result", {})
    trail.append(_event(
        "CURRENCY_CONVERTED",
        (
            f"Converted to USD: ${fx.get('converted_amount', 0):.2f} @ "
            f"{fx.get('exchange_rate', 1.0)} ({fx.get('source', 'N/A')}) "
            f"on {fx.get('rate_date', 'N/A')}"
        ),
        {
            "converted_amount": fx.get("converted_amount"),
            "rate": fx.get("exchange_rate"),
            "rate_date": fx.get("rate_date"),
            "source": fx.get("source"),
            "manipulation_flag": fx.get("rate_manipulation_flag"),
            "warning": fx.get("warning"),
        },
    ))

    # ── AUTHENTICITY_SCORED ───────────────────────────────
    auth = pipeline.get("authenticity_result", {})
    trail.append(_event(
        "AUTHENTICITY_SCORED",
        (
            f"Forgery risk: {auth.get('forgery_risk', 'N/A')} | "
            f"Confidence: {auth.get('confidence', 0):.0%} | "
            f"Flags: {', '.join(auth.get('specific_flags', [])) or 'None'}"
        ),
        {
            "forgery_risk": auth.get("forgery_risk"),
            "confidence": auth.get("confidence"),
            "flags": auth.get("specific_flags"),
            "is_screenshot": auth.get("is_screenshot"),
        },
    ))

    # ── POLICY_AUDIT_STARTED ──────────────────────────────
    trail.append(_event(
        "POLICY_AUDIT_STARTED",
        (
            f"Policy v{pipeline.get('policy_version', 'N/A')} | "
            f"Category: {pipeline.get('category', 'N/A')} | "
            f"City Tier: {pipeline.get('city_tier', 'N/A')}"
        ),
        {
            "policy_version": pipeline.get("policy_version"),
            "category": pipeline.get("category"),
            "city_tier": pipeline.get("city_tier"),
        },
    ))

    # ── RULE_MATCHED ──────────────────────────────────────
    audit = pipeline.get("audit_result", {})
    evidence = audit.get("policy_evidence", {})
    if evidence:
        trail.append(_event(
            "RULE_MATCHED",
            f"Section {evidence.get('section', 'N/A')} — {evidence.get('section_title', 'N/A')}",
            {
                "section": evidence.get("section"),
                "title": evidence.get("section_title"),
                "applied_rule": evidence.get("applied_rule"),
            },
        ))

    # ── CONSTRAINT_CHECKED (one event per decision factor) ─
    factors = audit.get("decision_factors", [])
    for factor in factors:
        trail.append(_event(
            "CONSTRAINT_CHECKED",
            (
                f"[{factor.get('weight', '?')}] {factor.get('factor', 'N/A')}: "
                f"{factor.get('result', '?')} — {factor.get('detail', '')}"
            ),
            {
                "factor": factor.get("factor"),
                "weight": factor.get("weight"),
                "result": factor.get("result"),
                "data_used": factor.get("data_used", {}),
            },
        ))

    # ── VERDICT_GENERATED ─────────────────────────────────
    trail.append(_event(
        "VERDICT_GENERATED",
        (
            f"Status: {audit.get('status', 'N/A')} | "
            f"Risk Score: {audit.get('risk_score', 0)} | "
            f"Confidence: {audit.get('ai_confidence', 0):.0%}"
        ),
        {
            "status": audit.get("status"),
            "risk_score": audit.get("risk_score"),
            "confidence": audit.get("ai_confidence"),
        },
    ))

    # ── EXPLANATION_STORED ────────────────────────────────
    explanation = audit.get("explanation", "")
    trail.append(_event(
        "EXPLANATION_STORED",
        explanation[:100] + ("..." if len(explanation) > 100 else ""),
        {"char_count": len(explanation)},
    ))

    # ── CLAIM_UPDATED ─────────────────────────────────────
    trail.append(_event(
        "CLAIM_UPDATED",
        f"MongoDB updated for claim {pipeline.get('claim_id', 'N/A')} with full audit results.",
        {"claim_id": pipeline.get("claim_id")},
    ))

    return trail
