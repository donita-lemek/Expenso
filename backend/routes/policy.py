"""
backend/routes/policy.py
Policy management endpoints.
Updated for MongoDB.
"""
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
import sys, os
from motor.motor_asyncio import AsyncIOMotorDatabase

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from backend.database import get_database
from backend.models import PolicyCreate

router = APIRouter(prefix="/policy", tags=["policy"])

@router.post("/upload")
async def upload_policy(policy: PolicyCreate, db: AsyncIOMotorDatabase = Depends(get_database)):
    await db.policy.update_many({"is_active": True}, {"$set": {"is_active": False}})

    doc_data = {
        "version": policy.version,
        "content": policy.content,
        "uploaded_at": datetime.utcnow().isoformat(),
        "is_active": True,
    }
    
    await db.policy.insert_one(doc_data)
    return {"message": "Policy uploaded and activated."}

@router.get("/active")
async def get_active_policy(db: AsyncIOMotorDatabase = Depends(get_database)):
    policy = await db.policy.find_one({"is_active": True})
    if not policy:
        raise HTTPException(status_code=404, detail="No active policy found.")
    policy.pop("_id", None)
    return policy
