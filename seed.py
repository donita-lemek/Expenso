import os
from datetime import datetime, timedelta

def get_seed_data():
    now = datetime.utcnow()
    common_audit_trail = [
        {"timestamp": (now - timedelta(minutes=5)).isoformat(), "event": "RECEIPT_UPLOADED", "detail": "Seeded receipt", "metadata": {}},
        {"timestamp": (now - timedelta(minutes=4)).isoformat(), "event": "OCR_COMPLETE", "detail": "OCR extraction complete", "metadata": {}},
        {"timestamp": (now - timedelta(minutes=3)).isoformat(), "event": "DUPLICATE_CHECK_PASS", "detail": "No duplicates found", "metadata": {}},
        {"timestamp": (now - timedelta(minutes=2)).isoformat(), "event": "CURRENCY_CONVERTED", "detail": "USD — no conversion", "metadata": {}},
        {"timestamp": (now - timedelta(minutes=1)).isoformat(), "event": "AUTHENTICITY_SCORED", "detail": "Forgery Risk: Low", "metadata": {}},
        {"timestamp": now.isoformat(), "event": "VERDICT_GENERATED", "detail": "Audit complete (seeded)", "metadata": {}},
    ]

    employees = [
        {
            "employee_id": "EMP-001",
            "password": "password123",
            "name": "Alice Chen",
            "email": "alice.chen@acmecorp.com",
            "department": "Engineering",
            "city": "New York",
            "city_tier": "A",
            "role_title": "Senior Solutions Engineer",
            "joining_date": "14 Aug 2021",
            "experience": "4.5 Years",
            "monthly_limits": {"meals": 500, "transport": 800, "lodging": 1500, "entertainment": 300},
        },
        {
            "employee_id": "EMP-002",
            "password": "password123",
            "name": "Bob Patel",
            "email": "bob.patel@acmecorp.com",
            "department": "Sales",
            "city": "Chicago",
            "city_tier": "B",
            "role_title": "Enterprise Sales Director",
            "joining_date": "03 Jan 2019",
            "experience": "7.2 Years",
            "monthly_limits": {"meals": 400, "transport": 600, "lodging": 1000, "entertainment": 200},
        },
        {
            "employee_id": "EMP-003",
            "password": "password123",
            "name": "Carol Smith",
            "email": "carol.smith@acmecorp.com",
            "department": "Operations",
            "city": "Austin",
            "city_tier": "B",
            "role_title": "Regional Operations Manager",
            "joining_date": "22 Nov 2022",
            "experience": "3.3 Years",
            "monthly_limits": {"meals": 400, "transport": 500, "lodging": 1000, "entertainment": 150},
        },
    ]

    auditors = [
        {
            "auditor_id": "AUD-491",
            "password": "admin",
            "name": "System Auditor",
            "role_title": "Lead Finance Auditor",
            "joining_date": "10 Feb 2017",
            "experience": "9.1 Years",
            "department": "Finance",
            "email": "audit@acmecorp.com"
        }
    ]

    policy_path = os.path.join(os.path.dirname(__file__), "sample_policy.txt")
    policy_content = open(policy_path).read() if os.path.exists(policy_path) else "Default policy."

    policy = [{
        "version": "v3.2",
        "content": policy_content,
        "uploaded_at": datetime.utcnow().isoformat(),
        "is_active": True,
    }]

    claims = [
        {
            "claim_id": "CLM-001",
            "employee_id": "EMP-001",
            "employee_name": "Alice Chen",
            "employee_email": "alice.chen@acmecorp.com",
            "city": "New York",
            "city_tier": "A",
            "category": "Meals",
            "merchant": "Le Bernardin",
            "transaction_date": (now - timedelta(days=3)).strftime("%Y-%m-%d"),
            "transaction_time": "20:30",
            "claimed_amount": 87.50,
            "original_currency": "USD",
            "converted_amount_usd": 87.50,
            "exchange_rate": 1.0,
            "exchange_rate_date": (now - timedelta(days=3)).strftime("%Y-%m-%d"),
            "exchange_rate_source": "none",
            "business_purpose": "Client dinner at Le Bernardin with product team.",
            "receipt_gcs_url": "",
            "receipt_filename": "le_bernardin_receipt.jpg",
            "phash": "aabbccddeeff0011",
            "sha256": "abc123def456",
            "status": "Rejected",
            "risk_score": 80,
            "ai_confidence": 0.95,
            "uncertainty_notes": None,
            "explanation": "Rejected: Section 1.1 sets Tier A dinner limit at $60.00; claim of $87.50 exceeds this by $27.50 which is 45.8% over the allowed amount.",
            "decision_factors": [
                {"factor": "Meal Amount vs Policy Limit", "weight": "HIGH", "result": "FAIL", "detail": "Section 1.1: Tier A dinner limit is $60.00. Claimed $87.50 — overage of $27.50 (45.8%)", "data_used": {"limit": 60.0, "claimed": 87.50, "overage": 27.50}},
                {"factor": "Business Purpose Documented", "weight": "MEDIUM", "result": "PASS", "detail": "Clear business purpose provided: client dinner.", "data_used": {}},
                {"factor": "Receipt Authenticity", "weight": "HIGH", "result": "PASS", "detail": "No forgery indicators detected.", "data_used": {}},
                {"factor": "Duplicate Check", "weight": "HIGH", "result": "PASS", "detail": "No duplicate receipts found.", "data_used": {}},
            ],
            "policy_evidence": {"section": "1.1", "section_title": "Daily Meal Limits", "full_text": "Tier A (New York, London, San Francisco, Tokyo): Breakfast $20 | Lunch $30 | Dinner $60", "applied_rule": "Dinner limit: $60.00 for Tier A cities", "matching_reason": "Category is Meals in New York (Tier A), transaction time 20:30 indicates dinner."},
            "confidence_breakdown": {"ocr_confidence": 0.95, "policy_match_confidence": 0.99, "overall_confidence": 0.95, "low_confidence_reasons": []},
            "counterfactuals": ["Reduce claim to $60.00 (the Tier A dinner limit) for approval.", "Obtain VP approval to claim above the standard dinner limit."],
            "violations": ["Section 1.1 — Tier A dinner limit ($60.00) exceeded by $27.50 (45.8%)"],
            "warnings": [],
            "audit_trail": common_audit_trail,
            "claude_prompt_sent": "Sample seeded prompt for CLM-001",
            "claude_raw_response": '{"status": "Rejected", "risk_score": 80}',
            "forgery_risk": "Low",
            "forgery_reasoning": "Receipt appears genuine with consistent fonts and standard elements.",
            "forgery_flags": [],
            "duplicate_of": None,
            "similarity_score": 0.0,
            "duplicate_detection_layer": None,
            "rate_manipulation_flag": False,
            "currency_warning": None,
            "auditor_override": False,
            "created_at": (now - timedelta(days=3)).isoformat(),
            "updated_at": (now - timedelta(days=3)).isoformat(),
        },
        {
            "claim_id": "CLM-002",
            "employee_id": "EMP-002",
            "employee_name": "Bob Patel",
            "employee_email": "bob.patel@acmecorp.com",
            "city": "Chicago",
            "city_tier": "B",
            "category": "Lodging",
            "merchant": "Marriott Chicago",
            "transaction_date": (now - timedelta(days=5)).strftime("%Y-%m-%d"),
            "transaction_time": "14:00",
            "claimed_amount": 230.0,
            "original_currency": "USD",
            "converted_amount_usd": 230.0,
            "exchange_rate": 1.0,
            "exchange_rate_date": (now - timedelta(days=5)).strftime("%Y-%m-%d"),
            "exchange_rate_source": "none",
            "business_purpose": "Hotel stay in Chicago for client meeting trip — 1 night.",
            "receipt_gcs_url": "",
            "receipt_filename": "marriott_chicago.jpg",
            "phash": "1122334455667788",
            "sha256": "def456ghi789",
            "status": "Approved",
            "risk_score": 5,
            "ai_confidence": 0.97,
            "uncertainty_notes": None,
            "explanation": "Approved: Section 3.1 sets Tier B hotel limit at $250.00; claim of $230.00 is within limit by $20.00.",
            "decision_factors": [
                {"factor": "Lodging Amount vs Policy Limit", "weight": "HIGH", "result": "PASS", "detail": "Section 3.1: Tier B hotel limit $250. Claimed $230 — within limit by $20.", "data_used": {"limit": 250, "claimed": 230}},
            ],
            "policy_evidence": {"section": "3.1", "section_title": "Hotel Nightly Limits", "full_text": "Hotel nightly limits: Tier A $350 | Tier B $250 | Tier C $175", "applied_rule": "Tier B hotel limit: $250/night", "matching_reason": "Category is Lodging in Chicago (Tier B)."},
            "confidence_breakdown": {"ocr_confidence": 0.96, "policy_match_confidence": 0.99, "overall_confidence": 0.97, "low_confidence_reasons": []},
            "counterfactuals": [],
            "violations": [],
            "warnings": [],
            "audit_trail": common_audit_trail,
            "claude_prompt_sent": "Sample seeded prompt for CLM-002",
            "claude_raw_response": '{"status": "Approved", "risk_score": 5}',
            "forgery_risk": "Low",
            "forgery_reasoning": "Standard hotel receipt with all required elements present.",
            "forgery_flags": [],
            "duplicate_of": None,
            "similarity_score": 0.0,
            "duplicate_detection_layer": None,
            "rate_manipulation_flag": False,
            "currency_warning": None,
            "auditor_override": False,
            "created_at": (now - timedelta(days=5)).isoformat(),
            "updated_at": (now - timedelta(days=5)).isoformat(),
        },
    ]

    return {
        "claims": claims,
        "employees": employees,
        "policy": policy,
        "auditors": auditors
    }

if __name__ == "__main__":
    print("This script is now a module imported by database.py for in-memory seed.")
