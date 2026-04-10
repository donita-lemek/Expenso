"""
backend/services/duplicate_service.py
Three-layer duplicate detection: exact SHA256, perceptual hash, semantic match.
Updated for MongoDB.
"""
import imagehash
from PIL import Image
from io import BytesIO
from typing import Optional
import sys
import os
from motor.motor_asyncio import AsyncIOMotorDatabase

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from backend.utils.helpers import compute_sha256

async def check_duplicate(
    image_bytes: bytes,
    new_sha256: str,
    employee_id: str,
    merchant: Optional[str],
    transaction_date: Optional[str],
    claimed_amount: float,
    db: AsyncIOMotorDatabase,
) -> dict:
    existing = await db.claims.find_one({"sha256": new_sha256})
    if existing:
        return {
            "is_duplicate": True,
            "duplicate_of": existing["claim_id"],
            "similarity_score": 100.0,
            "detection_layer": "exact",
            "message": f"Exact duplicate of {existing['claim_id']} (SHA256 match).",
            "phash": None,
        }

    try:
        img = Image.open(BytesIO(image_bytes))
        new_phash = imagehash.phash(img)
        new_phash_str = str(new_phash)
    except Exception as e:
        print(f"⚠️  pHash computation failed: {e}")
        new_phash = None
        new_phash_str = None

    all_claims = await db.claims.find().to_list(length=None)

    if new_phash is not None:
        for doc in all_claims:
            phash_val = doc.get("phash")
            if phash_val:
                try:
                    stored_phash = imagehash.hex_to_hash(phash_val)
                    distance = new_phash - stored_phash
                    if distance <= 10:
                        similarity = ((64 - distance) / 64) * 100
                        return {
                            "is_duplicate": True,
                            "duplicate_of": doc["claim_id"],
                            "similarity_score": round(similarity, 2),
                            "detection_layer": "visual",
                            "message": f"Visual duplicate of {doc['claim_id']} ({similarity:.1f}% similar).",
                            "phash": new_phash_str,
                        }
                except Exception:
                    continue

    if merchant and transaction_date:
        for c in all_claims:
            if (c.get("employee_id") == employee_id and
                c.get("merchant") == merchant and
                c.get("transaction_date") == transaction_date and
                c.get("claimed_amount") == claimed_amount):
                return {
                    "is_duplicate": True,
                    "duplicate_of": c["claim_id"],
                    "similarity_score": 95.0,
                    "detection_layer": "semantic",
                    "message": f"Semantic duplicate of {c['claim_id']} — same employee, merchant, date, and amount.",
                    "phash": new_phash_str,
                }

    return {
        "is_duplicate": False,
        "duplicate_of": None,
        "similarity_score": 0.0,
        "detection_layer": None,
        "message": "No duplicates found.",
        "phash": new_phash_str,
    }
