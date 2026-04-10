"""
backend/services/currency_service.py
Historical FX conversion via frankfurter.app.
Includes rate manipulation detection.
"""
import httpx
from typing import Optional


FRANKFURTER_BASE = "https://api.frankfurter.app"


async def convert_currency(
    amount: float,
    currency: str,
    transaction_date: Optional[str] = None,
    user_provided_usd: Optional[float] = None,
) -> dict:
    """
    Convert amount to USD using frankfurter.app.
    Prefers historical rate for transaction_date.
    Falls back to current rate if historical unavailable.
    Detects rate manipulation if user_provided_usd differs > 2%.
    """
    currency = currency.upper().strip()

    # USD — no conversion needed
    if currency == "USD":
        return {
            "converted_amount": amount,
            "exchange_rate": 1.0,
            "rate_date": transaction_date or "N/A",
            "source": "none",
            "warning": None,
            "rate_manipulation_flag": False,
        }

    async with httpx.AsyncClient(timeout=10.0) as client:
        rate = None
        source = None
        rate_date = None
        warning = None

        # ── Try historical rate ────────────────────────────
        if transaction_date:
            try:
                resp = await client.get(
                    f"{FRANKFURTER_BASE}/{transaction_date}",
                    params={"from": currency, "to": "USD"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    rate = data["rates"]["USD"]
                    rate_date = data["date"]
                    source = "historical"
            except Exception as e:
                print(f"⚠️  Historical FX fetch failed: {e}")

        # ── Fallback to current rate ───────────────────────
        if rate is None:
            try:
                resp = await client.get(
                    f"{FRANKFURTER_BASE}/latest",
                    params={"from": currency, "to": "USD"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    rate = data["rates"]["USD"]
                    rate_date = data["date"]
                    source = "current_rate_fallback"
                    warning = "Historical rate unavailable. Current rate used."
            except Exception as e:
                print(f"⚠️  Current FX fetch also failed: {e}")

        # ── Hard fallback if both failed ───────────────────
        if rate is None:
            return {
                "converted_amount": amount,
                "exchange_rate": 1.0,
                "rate_date": "N/A",
                "source": "fallback",
                "warning": "FX rate unavailable — amount used as-is.",
                "rate_manipulation_flag": False,
            }

        converted = round(amount * rate, 2)

        # ── Rate manipulation check ────────────────────────
        rate_manipulation_flag = False
        if user_provided_usd is not None and user_provided_usd > 0:
            diff_pct = abs(user_provided_usd - converted) / converted
            if diff_pct > 0.02:
                rate_manipulation_flag = True
                warning = (
                    warning or ""
                ) + f" ⚠️ Rate manipulation suspected: user reported ${user_provided_usd:.2f}, "
                f"API rate gives ${converted:.2f} ({diff_pct*100:.1f}% difference)."

        return {
            "converted_amount": converted,
            "exchange_rate": round(rate, 6),
            "rate_date": rate_date,
            "source": source,
            "warning": warning,
            "rate_manipulation_flag": rate_manipulation_flag,
        }
