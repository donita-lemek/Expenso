# 🧾 Expenso — Policy-First Expense Auditor with Explainable AI

A production-quality, portfolio-grade FinTech application that audits expense claims using
AI-powered OCR, forensic authenticity scoring, policy compliance checking, and a full
6-layer Explainable AI (XAI) verdict system.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit 1.35 (multi-page with `st.navigation`) |
| Backend | FastAPI 0.111 (async, port 8000) |
| Database | In-Memory Dictionary Store (Zero external dependencies) |
| AI — Vision | Google Gemini `gemini-1.5-flash` (OCR + Authenticity) |
| AI — Text | Google Gemini `gemini-1.5-pro` (Policy Audit + XAI) |
| Currency | frankfurter.app (free, no key needed) |
| Duplicate Detection | imagehash + Pillow (3-layer: SHA256 + pHash + Semantic) |
| File Storage | GCP Cloud Storage (local: base64 fallback) |
| Secrets | GCP Secret Manager (local: .env fallback) |
| Deployment | GCP Cloud Run (2 services: frontend + backend) |
| CI/CD | GitHub Actions → GCP Cloud Build |

---

## Quick Start (Local Dev)

### Prerequisites
- Python 3.9+
- A Google Gemini API key

### 1. Clone & Install

```bash
git clone https://github.com/your-org/expenso.git
cd expenso
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and set your `GEMINI_API_KEY`:
```
GEMINI_API_KEY=AIzaSy...
FASTAPI_URL=http://localhost:8000
ENV=local
```

### 3. Start Backend

No database setup is required! The app automatically seeds an in-memory database on startup.

```bash
cd /path/to/expenso
python -m uvicorn backend.main:app --reload --port 8000
```

Validates at: http://localhost:8000/health → `{"status": "ok", "version": "1.0.0"}`
API docs: http://localhost:8000/docs

### 4. Start Frontend (new terminal)

```bash
cd /path/to/expenso
python -m streamlit run frontend/app.py
```

Opens at: http://localhost:8501

---

## AI Pipeline

Every submitted claim runs through a 6-step pipeline:

```
Step 1: OCR (Gemini 1.5 Flash)
         └── Extract merchant, date, amount, line items

Step 2: PARALLEL via asyncio.gather():
         ├── Authenticity scoring (Gemini 1.5 Flash — forgery detection)
         ├── Duplicate detection (SHA256 → pHash → Semantic)
         └── Currency conversion (frankfurter.app historical rate)

Step 3: Policy Audit + XAI Generation (Gemini 1.5 Pro)
         └── Returns all 6 XAI layers in one structured JSON response

Step 4: Audit Trail Building
         └── 12 immutable timestamped events (RECEIPT_UPLOADED → CLAIM_UPDATED)

Step 5: In-Memory DB Update
         └── Full claim document with all XAI fields written synchronously
```

---

## Seeded Claims Reference

The database automatically seeds 3 employees and 6 pre-audited claims on startup.

| Claim | Employee | Status | Risk | Description |
|-------|----------|--------|------|-------------|
| CLM-001 | Alice Chen | ❌ Rejected | 80 | Le Bernardin $87.50 — 45.8% over Tier A dinner limit |
| CLM-002 | Bob Patel | ✅ Approved | 5 | Marriott Chicago $230 — within Tier B lodging limit |
| CLM-003 | Carol Smith | ⚠️ Flagged | 35 | Whole Foods $45 — Saturday meal, no manager approval |
| CLM-004 | Alice Chen | ❌ Rejected | 100 | 94% visual duplicate of CLM-001 (pHash) |
| CLM-005 | Bob Patel | ⚠️ Flagged | 45 | Gaucho £38→$48.26 — medium forgery risk (screenshot) |
| CLM-006 | Carol Smith | ✅ Approved | 8 | Tokyo Marriott ¥42000→$280 — within Tier A limit |
