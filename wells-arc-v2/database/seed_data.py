"""
Wells Arc - Synthetic Data Generator
Generates realistic transaction data for demo purposes.
Run: python database/seed_data.py
"""

import sqlite3
import uuid
import random
from datetime import datetime, timedelta
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_PATH = os.path.join(os.path.dirname(__file__), "wells_arc.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")

# ── Sample data pools ────────────────────────────────────────────────────────

CUSTOMERS = [
    {
        "id": "cust_001",
        "name": "Sarah Mitchell",
        "email": "sarah.mitchell@email.com",
        "phone": "+1-415-555-0101",
        "account_number": "WF-4521-8832",
        "account_type": "Checking",
        "balance": 8420.50,
        "alert_threshold": 500.0,
    },
    {
        "id": "cust_002",
        "name": "James Rivera",
        "email": "james.rivera@email.com",
        "phone": "+1-512-555-0182",
        "account_number": "WF-7743-2291",
        "account_type": "Checking",
        "balance": 15230.75,
        "alert_threshold": 1000.0,
    },
]

NORMAL_MERCHANTS = [
    ("Whole Foods Market", "Groceries", 45, 150),
    ("Netflix", "Subscriptions", 15, 20),
    ("Spotify", "Subscriptions", 10, 15),
    ("Shell Gas Station", "Gas", 40, 80),
    ("Starbucks", "Food & Drink", 5, 15),
    ("Amazon", "Shopping", 20, 200),
    ("CVS Pharmacy", "Health", 10, 60),
    ("Uber", "Transport", 8, 35),
    ("Chipotle", "Food & Drink", 10, 20),
    ("Target", "Shopping", 30, 150),
    ("AT&T", "Utilities", 80, 120),
    ("PG&E Electric", "Utilities", 60, 180),
    ("Planet Fitness", "Health", 10, 25),
    ("Apple Store", "Shopping", 5, 50),
    ("Trader Joe's", "Groceries", 30, 100),
]

SUSPICIOUS_MERCHANTS = [
    ("Unknown Merchant - Lagos, NG", "Unknown", 200, 1500),
    ("Wire Transfer - International", "Transfer", 500, 3000),
    ("Crypto Exchange XYZ", "Finance", 300, 2000),
    ("Unknown Merchant - Las Vegas, NV", "Unknown", 400, 1200),
    ("Foreign ATM Withdrawal", "Cash", 200, 800),
    ("Online Gambling Platform", "Entertainment", 100, 500),
]

LOCATIONS = [
    "San Francisco, CA", "Austin, TX", "New York, NY",
    "Chicago, IL", "Seattle, WA", "Boston, MA",
    "Denver, CO", "Miami, FL", "Portland, OR",
]


def generate_transactions(customer_id: str, threshold: float, count: int = 40):
    """Generate a realistic mix of transactions for a customer."""
    transactions = []
    now = datetime.now()

    # 70% normal, 20% yellow (above threshold), 10% red (suspicious)
    for i in range(count):
        txn_type = random.choices(
            ["normal", "yellow", "red"],
            weights=[70, 20, 10]
        )[0]

        days_ago = random.randint(0, 30)
        hours_ago = random.randint(0, 23)
        timestamp = now - timedelta(days=days_ago, hours=hours_ago)

        if txn_type == "normal":
            merchant, category, min_amt, max_amt = random.choice(NORMAL_MERCHANTS)
            amount = round(random.uniform(min_amt, min(max_amt, threshold * 0.9)), 2)
            location = random.choice(LOCATIONS)
            flag = "green"
            flag_reason = None
            anomaly_score = round(random.uniform(0.0, 0.2), 3)
            is_recurring = 1 if category == "Subscriptions" else 0

        elif txn_type == "yellow":
            merchant, category, min_amt, max_amt = random.choice(NORMAL_MERCHANTS)
            amount = round(random.uniform(threshold * 1.1, threshold * 2.5), 2)
            location = random.choice(LOCATIONS)
            flag = "yellow"
            flag_reason = f"Amount exceeds your ${threshold:.0f} threshold"
            anomaly_score = round(random.uniform(0.3, 0.6), 3)
            is_recurring = 0

        else:  # red
            merchant, category, min_amt, max_amt = random.choice(SUSPICIOUS_MERCHANTS)
            amount = round(random.uniform(min_amt, max_amt), 2)
            # Suspicious transactions often happen at odd hours
            timestamp = now - timedelta(
                days=random.randint(0, 7),
                hours=random.randint(0, 5)
            )
            location = merchant.split(" - ")[-1] if " - " in merchant else "Unknown"
            flag = "red"
            flag_reason = "Unrecognized merchant / unusual activity detected"
            anomaly_score = round(random.uniform(0.7, 1.0), 3)
            is_recurring = 0

        transactions.append({
            "id": f"txn_{uuid.uuid4().hex[:12]}",
            "customer_id": customer_id,
            "merchant_name": merchant,
            "amount": amount,
            "location": location,
            "category": category,
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "status": "active",
            "flag": flag,
            "flag_reason": flag_reason,
            "anomaly_score": anomaly_score,
            "is_recurring": is_recurring,
        })

    # Sort by timestamp descending (most recent first)
    transactions.sort(key=lambda x: x["timestamp"], reverse=True)
    return transactions


def seed_database():
    """Initialize and seed the Wells Arc database."""
    print("🏦 Wells Arc - Database Seeder")
    print("=" * 40)

    # Create DB and apply schema
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    with open(SCHEMA_PATH, "r") as f:
        cursor.executescript(f.read())
    print("✅ Schema applied")

    # Clear existing data
    cursor.execute("DELETE FROM transaction_actions")
    cursor.execute("DELETE FROM chat_history")
    cursor.execute("DELETE FROM transactions")
    cursor.execute("DELETE FROM customers")
    print("✅ Existing data cleared")

    # Insert customers
    for customer in CUSTOMERS:
        cursor.execute("""
            INSERT INTO customers 
            (id, name, email, phone, account_number, account_type, balance, alert_threshold)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            customer["id"], customer["name"], customer["email"],
            customer["phone"], customer["account_number"], customer["account_type"],
            customer["balance"], customer["alert_threshold"]
        ))
    print(f"✅ {len(CUSTOMERS)} customers inserted")

    # Insert transactions
    total_txns = 0
    for customer in CUSTOMERS:
        txns = generate_transactions(customer["id"], customer["alert_threshold"])
        for txn in txns:
            cursor.execute("""
                INSERT INTO transactions
                (id, customer_id, merchant_name, amount, location, category,
                 timestamp, status, flag, flag_reason, anomaly_score, is_recurring)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                txn["id"], txn["customer_id"], txn["merchant_name"],
                txn["amount"], txn["location"], txn["category"],
                txn["timestamp"], txn["status"], txn["flag"],
                txn["flag_reason"], txn["anomaly_score"], txn["is_recurring"]
            ))
        total_txns += len(txns)

    print(f"✅ {total_txns} transactions generated")
    conn.commit()
    conn.close()

    print("\n🎉 Database seeded successfully!")
    print(f"📁 Location: {DB_PATH}")
    print("\nDemo login:")
    for c in CUSTOMERS:
        print(f"  Account: {c['account_number']} | Name: {c['name']}")


if __name__ == "__main__":
    seed_database()
