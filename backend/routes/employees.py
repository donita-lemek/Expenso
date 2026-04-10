"""
backend/routes/employees.py
Employee listing and budget endpoints.
Updated for MongoDB.
"""
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from backend.services.currency_service import convert_currency
import sys, os
from motor.motor_asyncio import AsyncIOMotorDatabase

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from backend.database import get_database

router = APIRouter(prefix="/employees", tags=["employees"])

@router.get("/")
async def list_employees(db: AsyncIOMotorDatabase = Depends(get_database)):
    employees = await db.employees.find().to_list(length=None)
    for e in employees:
        e.pop("_id", None)
    return employees

@router.get("/{employee_id}/budget")
async def get_employee_budget(employee_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    employee = await db.employees.find_one({"employee_id": employee_id})
    if not employee:
        raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found")
    employee.pop("_id", None)

    now = datetime.utcnow()
    month_start = datetime(now.year, now.month, 1).isoformat()

    spend = {}
    
    claims = await db.claims.find({"employee_id": employee_id, "status": {"$in": ["Approved", "Pending", "Flagged"]}}).to_list(length=None)

    for c in claims:
        created = c.get("created_at") or ""
        if created >= month_start:
            cat = (c.get("category") or "other").lower()
            converted = float(c.get("converted_amount_usd") or 0.0)
            if converted and converted > 0:
                amt = converted
            else:
                claimed = float(c.get("claimed_amount") or 0.0)
                orig_cur = (c.get("original_currency") or "").upper()
                if orig_cur == "USD" or not orig_cur:
                    amt = claimed
                else:
                    try:
                        fx = await convert_currency(claimed, orig_cur, c.get("transaction_date"))
                        amt = float(fx.get("converted_amount") or claimed)
                    except Exception:
                        amt = claimed

            spend[cat] = round(spend.get(cat, 0.0) + amt, 2)

    limits = employee.get("monthly_limits", {})
    remaining = {}
    for cat, limit in limits.items():
        spent = spend.get(cat.lower(), 0.0)
        remaining[cat] = round(max(0.0, limit - spent), 2)

    return {
        "employee": employee,
        "current_month_spend": spend,
        "limits": limits,
        "remaining": remaining,
        "month": now.strftime("%B %Y"),
        "days_remaining": (datetime(now.year, now.month % 12 + 1, 1) - now).days if now.month < 12 else (datetime(now.year + 1, 1, 1) - now).days,
    }
