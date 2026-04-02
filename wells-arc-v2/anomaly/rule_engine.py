"""
Wells Arc - Rule-Based Anomaly Detection Engine
Applies business rules to classify transactions as red/yellow/green.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class FlagResult:
    flag: str           # green, yellow, red
    reason: Optional[str]
    score: float        # 0.0 to 1.0


# ── Suspicious keywords in merchant names ────────────────────────────────────
SUSPICIOUS_KEYWORDS = [
    "unknown", "wire transfer", "crypto", "gambling", "foreign atm",
    "international", "offshore", "unnamed", "unverified",
]

SUSPICIOUS_LOCATIONS = [
    "lagos", "ng", "unknown", "offshore", "international",
]

HIGH_RISK_CATEGORIES = [
    "Unknown", "Transfer", "Finance", "Cash",
]

ODD_HOURS_START = 0   # midnight
ODD_HOURS_END = 5     # 5am


def check_rules(
    merchant_name: str,
    amount: float,
    location: str,
    category: str,
    timestamp: str,
    threshold: float,
    is_recurring: bool = False,
) -> FlagResult:
    """
    Apply rule-based checks to classify a transaction.
    Returns a FlagResult with flag color, reason, and score.
    """

    merchant_lower = merchant_name.lower()
    location_lower = (location or "").lower()
    score = 0.0
    reasons = []

    # ── Rule 1: Suspicious merchant name ────────────────────────────────────
    if any(kw in merchant_lower for kw in SUSPICIOUS_KEYWORDS):
        score += 0.4
        reasons.append("Unrecognized or suspicious merchant")

    # ── Rule 2: Suspicious location ─────────────────────────────────────────
    if any(loc in location_lower for loc in SUSPICIOUS_LOCATIONS):
        score += 0.3
        reasons.append("Unusual transaction location")

    # ── Rule 3: High risk category ───────────────────────────────────────────
    if category in HIGH_RISK_CATEGORIES:
        score += 0.2
        reasons.append("High-risk transaction category")

    # ── Rule 4: Odd hours (midnight - 5am) ──────────────────────────────────
    try:
        txn_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        if ODD_HOURS_START <= txn_time.hour < ODD_HOURS_END:
            score += 0.2
            reasons.append(f"Transaction occurred at unusual hour ({txn_time.strftime('%I:%M %p')})")
    except Exception:
        pass

    # ── Rule 5: Very large amount (3x threshold) ─────────────────────────────
    if amount > threshold * 3:
        score += 0.3
        reasons.append(f"Amount (${amount:,.2f}) is significantly above normal")

    # ── Rule 6: Above threshold but not suspicious ───────────────────────────
    above_threshold = amount > threshold and not is_recurring

    # ── Determine flag ───────────────────────────────────────────────────────
    score = min(score, 1.0)

    if score >= 0.5:
        return FlagResult(
            flag="red",
            reason=" · ".join(reasons) if reasons else "Suspicious activity detected",
            score=round(score, 3),
        )
    elif above_threshold:
        return FlagResult(
            flag="yellow",
            reason=f"Amount exceeds your ${threshold:,.0f} alert threshold",
            score=round(max(score, 0.3), 3),
        )
    else:
        return FlagResult(
            flag="green",
            reason=None,
            score=round(score, 3),
        )
