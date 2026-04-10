"""
frontend/components/api_client.py
HTTP client wrapping all FastAPI calls used by Streamlit pages.
"""
import httpx
import os
import streamlit as st
from typing import Optional, Dict, Any, List

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")
TIMEOUT = 30.0


def _get(path: str, params: dict = None) -> Optional[Any]:
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            resp = client.get(f"{FASTAPI_URL}{path}", params=params or {})
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        st.error(f"API Error {e.response.status_code}: {e.response.text[:200]}")
        return None
    except Exception as e:
        st.error(f"Connection error: {e}")
        return None


def _post(path: str, json: dict = None, data: dict = None, files=None) -> Optional[Any]:
    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(
                f"{FASTAPI_URL}{path}",
                json=json,
                data=data,
                files=files,
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        st.error(f"API Error {e.response.status_code}: {e.response.text[:200]}")
        return None
    except Exception as e:
        st.error(f"Connection error: {e}")
        return None


def _delete(path: str) -> Optional[Any]:
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            resp = client.delete(f"{FASTAPI_URL}{path}")
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        st.error(f"Delete error: {e}")
        return None


# ── Claims ────────────────────────────────────────────────

def submit_claim(
    employee_id, employee_name, employee_email,
    city, city_tier, category,
    claimed_amount, original_currency,
    business_purpose, receipt_bytes, receipt_filename,
) -> Optional[Dict]:
    return _post(
        "/claims/submit",
        data={
            "employee_id": employee_id,
            "employee_name": employee_name,
            "employee_email": employee_email,
            "city": city,
            "city_tier": city_tier,
            "category": category,
            "claimed_amount": str(claimed_amount),
            "original_currency": original_currency,
            "business_purpose": business_purpose,
        },
        files={"receipt": (receipt_filename, receipt_bytes, "image/jpeg")},
    )


def get_claim(claim_id: str) -> Optional[Dict]:
    return _get(f"/claims/{claim_id}")


def list_claims(
    status: str = None,
    category: str = None,
    employee_id: str = None,
    search: str = None,
) -> List[Dict]:
    params = {}
    if status:
        params["status"] = status
    if category:
        params["category"] = category
    if employee_id:
        params["employee_id"] = employee_id
    if search:
        params["search"] = search
    result = _get("/claims/", params=params)
    return result or []


def override_claim(claim_id: str, status: str, auditor_id: str, comment: str, reason: str) -> Optional[Dict]:
    return _post(
        f"/claims/{claim_id}/override",
        json={"status": status, "auditor_id": auditor_id, "comment": comment, "reason": reason},
    )


def delete_claim(claim_id: str) -> Optional[Dict]:
    return _delete(f"/claims/{claim_id}")


def get_audit_trail(claim_id: str) -> Optional[Dict]:
    return _get(f"/claims/{claim_id}/audit-trail")


def get_xai_report(claim_id: str) -> Optional[Dict]:
    return _get(f"/claims/{claim_id}/xai-report")


def rerun_audit(claim_id: str) -> Optional[Dict]:
    return _post(f"/audit/run/{claim_id}")


# ── Policy ────────────────────────────────────────────────

def get_active_policy() -> Optional[Dict]:
    return _get("/policy/active")


def upload_policy(content: str, version: str = "v1.0") -> Optional[Dict]:
    return _post("/policy/upload", json={"content": content, "version": version})


# ── Employees ─────────────────────────────────────────────

def list_employees() -> List[Dict]:
    return _get("/employees/") or []


def get_employee_budget(employee_id: str) -> Optional[Dict]:
    return _get(f"/employees/{employee_id}/budget")


# ── Health ────────────────────────────────────────────────

def check_health() -> bool:
    result = _get("/health")
    return result is not None and result.get("status") == "ok"
