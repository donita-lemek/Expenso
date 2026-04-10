"""
backend/models.py
Pydantic v2 models for all MongoDB collections and API I/O.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ── XAI Sub-models ────────────────────────────────────────

class DecisionFactor(BaseModel):
    factor: str
    weight: str           # HIGH | MEDIUM | LOW
    result: str           # PASS | FAIL | WARNING
    detail: str
    data_used: Dict[str, Any] = {}


class PolicyEvidence(BaseModel):
    section: str
    section_title: str
    full_text: str
    applied_rule: str
    matching_reason: str


class ConfidenceBreakdown(BaseModel):
    ocr_confidence: float
    policy_match_confidence: float
    overall_confidence: float
    low_confidence_reasons: List[str] = []


class AuditTrailEvent(BaseModel):
    timestamp: str
    event: str
    detail: str
    metadata: Dict[str, Any] = {}


# ── Employee ──────────────────────────────────────────────

class MonthlyLimits(BaseModel):
    meals: float = 500.0
    transport: float = 800.0
    lodging: float = 1500.0
    entertainment: float = 300.0


class EmployeeModel(BaseModel):
    employee_id: str
    name: str
    email: str
    department: str
    city: str
    city_tier: str
    monthly_limits: MonthlyLimits = MonthlyLimits()


class EmployeeBudget(BaseModel):
    employee: EmployeeModel
    current_month_spend: Dict[str, float]
    remaining: Dict[str, float]
    month: str


# ── Policy ────────────────────────────────────────────────

class PolicyCreate(BaseModel):
    content: str
    version: str = "v1.0"


class PolicyModel(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    version: str
    content: str
    uploaded_at: str
    is_active: bool = True


# ── Claim ─────────────────────────────────────────────────

class ClaimCreate(BaseModel):
    employee_id: str
    employee_name: str
    employee_email: str
    city: str
    city_tier: str
    category: str
    claimed_amount: float
    original_currency: str
    business_purpose: str
    merchant: Optional[str] = None
    transaction_date: Optional[str] = None


class OverrideRequest(BaseModel):
    status: str           # Approved | Rejected
    auditor_id: str
    comment: str
    reason: str


class ClaimSummary(BaseModel):
    """Lightweight list-view model."""
    claim_id: str
    employee_name: str
    merchant: Optional[str]
    transaction_date: Optional[str]
    claimed_amount: float
    original_currency: str
    converted_amount_usd: Optional[float]
    category: str
    status: str
    risk_score: int
    forgery_risk: Optional[str]
    is_duplicate: Optional[bool]
    created_at: str


class ClaimResponse(BaseModel):
    """Full claim with all XAI layers."""
    id: Optional[str] = Field(None, alias="_id")
    claim_id: str
    employee_id: str
    employee_name: str
    employee_email: str
    city: str
    city_tier: str
    category: str
    merchant: Optional[str]
    transaction_date: Optional[str]
    transaction_time: Optional[str]
    claimed_amount: float
    original_currency: str
    converted_amount_usd: float = 0.0
    exchange_rate: float = 1.0
    exchange_rate_date: Optional[str]
    exchange_rate_source: Optional[str]
    business_purpose: str
    receipt_gcs_url: Optional[str]
    receipt_filename: Optional[str]
    phash: Optional[str]
    sha256: Optional[str]

    # Core verdict
    status: str = "Pending"
    risk_score: int = 0
    ai_confidence: float = 0.0
    uncertainty_notes: Optional[str]

    # XAI layers
    explanation: Optional[str]
    decision_factors: List[DecisionFactor] = []
    policy_evidence: Optional[PolicyEvidence]
    confidence_breakdown: Optional[ConfidenceBreakdown]
    counterfactuals: List[str] = []
    audit_trail: List[AuditTrailEvent] = []
    claude_prompt_sent: Optional[str]
    claude_raw_response: Optional[str]

    # Integrity signals
    forgery_risk: Optional[str]
    forgery_reasoning: Optional[str]
    forgery_flags: List[str] = []
    duplicate_of: Optional[str]
    similarity_score: float = 0.0
    duplicate_detection_layer: Optional[str]

    # Currency signals
    rate_manipulation_flag: bool = False
    currency_warning: Optional[str]

    # Override
    auditor_override: bool = False
    auditor_comment: Optional[str]
    auditor_id: Optional[str]
    override_reason: Optional[str]

    created_at: Optional[str]
    updated_at: Optional[str]

    class Config:
        populate_by_name = True
