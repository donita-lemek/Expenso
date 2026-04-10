"""
backend/routes/claims.py
All claim endpoints + background pipeline orchestration.
Updated for MongoDB.
"""
import asyncio
import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from motor.motor_asyncio import AsyncIOMotorDatabase

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.database import get_database
from backend.utils.helpers import generate_claim_id, compute_sha256, upload_to_gcs, now_iso
from backend.models import OverrideRequest
from backend.services.ocr_service import extract_receipt_data
from backend.services.authenticity_service import score_authenticity
from backend.services.duplicate_service import check_duplicate
from backend.services.currency_service import convert_currency
from backend.services.audit_service import run_policy_audit
from backend.services.xai_service import build_audit_trail

router = APIRouter(prefix="/claims", tags=["claims"])

async def run_full_pipeline(claim_id: str, image_bytes: bytes, receipt_filename: str, db: AsyncIOMotorDatabase):
    try:
        claim = await db.claims.find_one({"claim_id": claim_id})
        if not claim: return

        ocr_result = await extract_receipt_data(image_bytes)
        ocr_updates = {
            "merchant": ocr_result.get("merchant_name") or claim.get("merchant"),
            "transaction_date": ocr_result.get("transaction_date") or claim.get("transaction_date"),
            "transaction_time": ocr_result.get("transaction_time"),
            "line_items": ocr_result.get("line_items", []),
            "receipt_quality": ocr_result.get("receipt_quality"),
            "ocr_confidence": ocr_result.get("ocr_confidence", 0.0),
        }
        if not claim.get("claimed_amount") and ocr_result.get("total_amount"):
            ocr_updates["claimed_amount"] = ocr_result["total_amount"]
        if not claim.get("original_currency") and ocr_result.get("currency"):
            ocr_updates["original_currency"] = ocr_result["currency"]

        merged_claim = {**claim, **ocr_updates}
        sha256 = compute_sha256(image_bytes)

        auth_task = score_authenticity(image_bytes, ocr_result)
        dup_task = check_duplicate(image_bytes, sha256, claim["employee_id"], merged_claim.get("merchant"), merged_claim.get("transaction_date"), merged_claim.get("claimed_amount", 0.0), db)
        fx_task = convert_currency(merged_claim.get("claimed_amount", 0.0), merged_claim.get("original_currency", "USD"), merged_claim.get("transaction_date"))

        auth_result, dup_result, fx_result = await asyncio.gather(auth_task, dup_task, fx_task)

        policy_doc = await db.policy.find_one({"is_active": True})
        policy_text = policy_doc["content"] if policy_doc else "No active policy found."
        
        emp = await db.employees.find_one({"employee_id": claim["employee_id"]})

        audit_input = {
            **merged_claim,
            "department": emp["department"] if emp else "Unknown",
            "converted_amount_usd": fx_result["converted_amount"],
            "exchange_rate": fx_result["exchange_rate"],
            "exchange_rate_date": fx_result["rate_date"],
            "exchange_rate_source": fx_result["source"],
            "forgery_risk": auth_result.get("forgery_risk", "Low"),
            "forgery_reasoning": auth_result.get("reasoning", ""),
            "forgery_flags": auth_result.get("specific_flags", []),
            "duplicate_message": dup_result.get("message", ""),
            "duplicate_detection_layer": dup_result.get("detection_layer"),
            "rate_manipulation_flag": fx_result.get("rate_manipulation_flag", False),
        }

        audit_result = await run_policy_audit(audit_input, policy_text)
        status = "Rejected" if dup_result.get("is_duplicate") and dup_result.get("detection_layer") in ("exact", "visual") else audit_result.get("status", "Flagged")

        audit_trail = build_audit_trail({
            "receipt_filename": receipt_filename,
            "receipt_size": len(image_bytes),
            "receipt_format": receipt_filename.rsplit(".", 1)[-1].upper() if "." in receipt_filename else "UNKNOWN",
            "ocr_result": ocr_result, "duplicate_result": dup_result, "currency_result": fx_result,
            "authenticity_result": auth_result, "audit_result": audit_result,
            "policy_version": policy_doc.get("version", "N/A") if policy_doc else "N/A",
            "category": merged_claim.get("category"), "city_tier": merged_claim.get("city_tier"), "claim_id": claim_id
        })

        await db.claims.update_one(
            {"claim_id": claim_id},
            {"$set": {
                **ocr_updates,
                "converted_amount_usd": fx_result["converted_amount"],
                "exchange_rate": fx_result["exchange_rate"],
                "exchange_rate_date": fx_result["rate_date"],
                "exchange_rate_source": fx_result["source"],
                "rate_manipulation_flag": fx_result.get("rate_manipulation_flag", False),
                "currency_warning": fx_result.get("warning"),
                "sha256": sha256,
                "phash": dup_result.get("phash"),
                "forgery_risk": auth_result.get("forgery_risk", "Low"),
                "forgery_reasoning": auth_result.get("reasoning", ""),
                "forgery_flags": auth_result.get("specific_flags", []),
                "duplicate_of": dup_result.get("duplicate_of"),
                "similarity_score": dup_result.get("similarity_score", 0.0),
                "duplicate_detection_layer": dup_result.get("detection_layer"),
                "status": status,
                "risk_score": min(audit_result.get("risk_score", 0), 100),
                "ai_confidence": audit_result.get("ai_confidence", 0.0),
                "uncertainty_notes": audit_result.get("uncertainty_notes"),
                "explanation": audit_result.get("explanation"),
                "decision_factors": audit_result.get("decision_factors", []),
                "policy_evidence": audit_result.get("policy_evidence"),
                "confidence_breakdown": audit_result.get("confidence_breakdown"),
                "counterfactuals": audit_result.get("counterfactuals", []),
                "violations": audit_result.get("violations", []),
                "warnings": audit_result.get("warnings", []),
                "audit_trail": audit_trail,
                "claude_prompt_sent": audit_result.get("_prompt_sent", ""),
                "claude_raw_response": audit_result.get("_raw_response", ""),
                "updated_at": datetime.utcnow().isoformat()
            }}
        )
        print(f"✅ Pipeline complete for {claim_id}: {status}")

    except Exception as e:
        await db.claims.update_one(
            {"claim_id": claim_id},
            {"$set": {
                "status": "Flagged", "explanation": f"Pipeline error: {str(e)}",
                "risk_score": 60, "updated_at": datetime.utcnow().isoformat()
            }}
        )

@router.post("/submit")
async def submit_claim(
    background_tasks: BackgroundTasks,
    db: AsyncIOMotorDatabase = Depends(get_database),
    employee_id: str = Form(...), employee_name: str = Form(...), employee_email: str = Form(...),
    city: str = Form(...), city_tier: str = Form(...), category: str = Form(...),
    claimed_amount: float = Form(...), original_currency: str = Form(...), business_purpose: str = Form(...),
    receipt: UploadFile = File(...)
):
    image_bytes = await receipt.read()
    filename = receipt.filename or f"receipt_{uuid.uuid4().hex}.jpg"
    claim_id = generate_claim_id()
    
    merchant = None
    transaction_date = None
    try:
        ocr_result = await extract_receipt_data(image_bytes)
        merchant = ocr_result.get("merchant_name") or None
        transaction_date = ocr_result.get("transaction_date") or None
        if not claimed_amount and ocr_result.get("total_amount"):
            claimed_amount = ocr_result.get("total_amount")
        if not original_currency and ocr_result.get("currency"):
            original_currency = ocr_result.get("currency")
    except Exception:
        pass

    if not merchant:
        try:
            from backend.utils.helpers import humanize_filename
            hf = humanize_filename(filename)
            merchant = hf if hf else None
        except Exception:
            pass

    claim_doc = {
        "claim_id": claim_id, "employee_id": employee_id, "employee_name": employee_name, "employee_email": employee_email,
        "city": city, "city_tier": city_tier, "category": category,
        "claimed_amount": claimed_amount, "original_currency": original_currency, "converted_amount_usd": 0.0,
        "exchange_rate": 1.0, "business_purpose": business_purpose,
        "receipt_gcs_url": upload_to_gcs(image_bytes, filename), "receipt_filename": filename,
        "merchant": merchant, "transaction_date": transaction_date,
        "sha256": compute_sha256(image_bytes), "phash": None,
        "status": "Pending", "risk_score": 0, "ai_confidence": 0.0,
        "auditor_override": False, "audit_trail": [],
        "created_at": datetime.utcnow().isoformat(), "updated_at": datetime.utcnow().isoformat()
    }
    
    await db.claims.insert_one(claim_doc)
    
    background_tasks.add_task(run_full_pipeline, claim_id, image_bytes, filename, db)
    return {"claim_id": claim_id, "status": "Pending"}

@router.get("/")
async def list_claims(
    status: Optional[str] = None, category: Optional[str] = None, employee_id: Optional[str] = None, 
    search: Optional[str] = None, db: AsyncIOMotorDatabase = Depends(get_database)
):
    query = {}
    statuses = [s.strip() for s in status.split(",")] if status else []
    
    if statuses:
        query["status"] = {"$in": statuses} if len(statuses) > 1 else statuses[0]
    if category:
        query["category"] = category
    if employee_id:
        query["employee_id"] = employee_id
    
    docs = await db.claims.find(query).to_list(length=None)
    res = []
    for c in docs:
        c.pop("_id", None)
        if search:
            sm = search.lower()
            if sm not in c.get("employee_name", "").lower() and sm not in c.get("merchant", "").lower():
                continue
        res.append(c)
    
    status_order = {"Rejected": 0, "Flagged": 1, "Pending": 2, "Approved": 3}
    res.sort(key=lambda x: (status_order.get(x.get("status"), 4), -int(x.get("risk_score", 0))))
    return res

@router.get("/{claim_id}")
async def get_claim(claim_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    doc = await db.claims.find_one({"claim_id": claim_id})
    if not doc: raise HTTPException(404)
    doc.pop("_id", None)
    return doc

@router.post("/{claim_id}/override")
async def override_claim(claim_id: str, override: OverrideRequest, db: AsyncIOMotorDatabase = Depends(get_database)):
    doc = await db.claims.find_one({"claim_id": claim_id})
    if not doc: raise HTTPException(404)
    await db.claims.update_one(
        {"claim_id": claim_id},
        {"$set": {
            "status": override.status, "auditor_override": True, "auditor_comment": override.comment,
            "auditor_id": override.auditor_id, "override_reason": override.reason, "updated_at": datetime.utcnow().isoformat()
        }}
    )
    return {"message": "Success"}

@router.delete("/{claim_id}")
async def delete_claim(claim_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    res = await db.claims.delete_one({"claim_id": claim_id})
    if res.deleted_count == 0: raise HTTPException(404)
    return {"message": "Deleted"}

@router.get("/{claim_id}/audit-trail")
async def get_audit_trail(claim_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    doc = await db.claims.find_one({"claim_id": claim_id})
    if not doc: raise HTTPException(404)
    return {"claim_id": claim_id, "audit_trail": doc.get("audit_trail", [])}

@router.get("/{claim_id}/xai-report")
async def get_xai_report(claim_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    doc = await db.claims.find_one({"claim_id": claim_id})
    if not doc: raise HTTPException(404)
    doc.pop("_id", None)
    return doc
