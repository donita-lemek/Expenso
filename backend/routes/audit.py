"""
backend/routes/audit.py
On-demand re-run of the audit pipeline for a specific claim.
Updated for MongoDB.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from datetime import datetime
import sys, os
from motor.motor_asyncio import AsyncIOMotorDatabase

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from backend.database import get_database

router = APIRouter(prefix="/audit", tags=["audit"])

@router.post("/run/{claim_id}")
async def rerun_audit(claim_id: str, background_tasks: BackgroundTasks, db: AsyncIOMotorDatabase = Depends(get_database)):
    from backend.routes.claims import run_full_pipeline

    doc = await db.claims.find_one({"claim_id": claim_id})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Claim {claim_id} not found")
    
    gcs_url = doc.get("receipt_gcs_url", "")
    receipt_filename = doc.get("receipt_filename", "receipt.jpg")

    if gcs_url.startswith("data:"):
        import base64
        header, b64data = gcs_url.split(",", 1)
        image_bytes = base64.b64decode(b64data)
    else:
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get(gcs_url)
            image_bytes = resp.content

    await db.claims.update_one(
        {"claim_id": claim_id},
        {"$set": {
            "status": "Pending",
            "updated_at": datetime.utcnow().isoformat()
        }}
    )

    background_tasks.add_task(run_full_pipeline, claim_id, image_bytes, receipt_filename, db)
    return {"message": f"Audit re-run started for {claim_id}", "claim_id": claim_id}
