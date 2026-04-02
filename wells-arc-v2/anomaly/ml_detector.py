"""
Wells Arc - ML Anomaly Detector (Isolation Forest)
Trains on transaction history to detect anomalies.
Combines with rule engine for final classification.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import sqlite3
import os
import pickle
from datetime import datetime
from typing import Optional

from anomaly.rule_engine import check_rules, FlagResult

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "wells_arc.db")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "isolation_forest.pkl")
SCALER_PATH = os.path.join(os.path.dirname(__file__), "scaler.pkl")


def extract_features(
    amount: float,
    timestamp: str,
    merchant_name: str,
    category: str,
    location: str,
    is_recurring: bool,
) -> np.ndarray:
    """Extract numerical features from a transaction for ML model."""

    # Hour of day (0-23)
    try:
        txn_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        hour = txn_time.hour
        day_of_week = txn_time.weekday()
    except Exception:
        hour = 12
        day_of_week = 0

    # Is odd hour (midnight to 5am)?
    is_odd_hour = 1 if hour < 5 or hour > 23 else 0

    # Is weekend?
    is_weekend = 1 if day_of_week >= 5 else 0

    # Contains suspicious keyword?
    suspicious_keywords = ["unknown", "wire", "crypto", "gambling", "foreign", "international"]
    has_suspicious_keyword = 1 if any(kw in merchant_name.lower() for kw in suspicious_keywords) else 0

    # Category risk score
    high_risk_categories = ["Unknown", "Transfer", "Finance", "Cash"]
    category_risk = 1 if category in high_risk_categories else 0

    # Is recurring
    recurring = 1 if is_recurring else 0

    return np.array([
        amount,
        hour,
        day_of_week,
        is_odd_hour,
        is_weekend,
        has_suspicious_keyword,
        category_risk,
        recurring,
    ]).reshape(1, -1)


def train_model(customer_id: Optional[str] = None):
    """
    Train Isolation Forest on existing transaction data.
    Saves model and scaler to disk for reuse.
    """
    conn = sqlite3.connect(DB_PATH)

    query = "SELECT * FROM transactions WHERE status = 'active'"
    if customer_id:
        query += f" AND customer_id = '{customer_id}'"

    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty or len(df) < 10:
        print("⚠️  Not enough data to train model — using rule engine only.")
        return None, None

    # Extract features for all transactions
    features = []
    for _, row in df.iterrows():
        feat = extract_features(
            row["amount"],
            row["timestamp"],
            row["merchant_name"],
            row["category"],
            row["location"] or "",
            bool(row["is_recurring"]),
        )
        features.append(feat.flatten())

    X = np.array(features)

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Train Isolation Forest
    # contamination = expected proportion of anomalies (~10%)
    model = IsolationForest(
        n_estimators=100,
        contamination=0.1,
        random_state=42,
        max_features=1.0,
    )
    model.fit(X_scaled)

    # Save model and scaler
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    with open(SCALER_PATH, "wb") as f:
        pickle.dump(scaler, f)

    print(f"✅ Isolation Forest trained on {len(df)} transactions")
    return model, scaler


def load_model():
    """Load trained model and scaler from disk."""
    if not os.path.exists(MODEL_PATH) or not os.path.exists(SCALER_PATH):
        return train_model()

    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    with open(SCALER_PATH, "rb") as f:
        scaler = pickle.load(f)

    return model, scaler


def detect_anomaly(
    amount: float,
    timestamp: str,
    merchant_name: str,
    category: str,
    location: str,
    threshold: float,
    is_recurring: bool = False,
) -> FlagResult:
    """
    Hybrid detection: combines Isolation Forest ML score
    with rule-based engine for final classification.
    """

    # ── Step 1: Rule-based check ─────────────────────────────────────────────
    rule_result = check_rules(
        merchant_name=merchant_name,
        amount=amount,
        location=location,
        category=category,
        timestamp=timestamp,
        threshold=threshold,
        is_recurring=is_recurring,
    )

    # ── Step 2: ML-based check ────────────────────────────────────────────────
    try:
        model, scaler = load_model()
        if model is None:
            return rule_result

        features = extract_features(
            amount, timestamp, merchant_name,
            category, location, is_recurring
        )
        features_scaled = scaler.transform(features)

        # Isolation Forest: -1 = anomaly, 1 = normal
        prediction = model.predict(features_scaled)[0]
        ml_score = model.score_samples(features_scaled)[0]

        # Normalize ML score to 0-1 (more negative = more anomalous)
        ml_anomaly_score = max(0.0, min(1.0, (-ml_score + 0.5)))

    except Exception:
        # If ML fails, fall back to rule engine
        return rule_result

    # ── Step 3: Combine scores ────────────────────────────────────────────────
    # Weighted combination: 60% rules, 40% ML
    combined_score = round((rule_result.score * 0.6) + (ml_anomaly_score * 0.4), 3)

    # If ML says anomaly and rules agree → strengthen red flag
    if prediction == -1 and rule_result.flag == "red":
        combined_score = min(combined_score + 0.1, 1.0)

    # Final classification
    if combined_score >= 0.45 or rule_result.flag == "red":
        return FlagResult(
            flag="red",
            reason=rule_result.reason or "Unusual activity detected by AI",
            score=combined_score,
        )
    elif rule_result.flag == "yellow":
        return FlagResult(
            flag="yellow",
            reason=rule_result.reason,
            score=combined_score,
        )
    else:
        return FlagResult(
            flag="green",
            reason=None,
            score=combined_score,
        )
