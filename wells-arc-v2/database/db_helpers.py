"""
Wells Arc - Database Helper
All database operations in one place.
"""

import sqlite3
import os
from typing import Optional
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "wells_arc.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ── Customer ──────────────────────────────────────────────────────────────────
def get_customer(account_number: str) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM customers WHERE account_number = ?",
            (account_number,)
        ).fetchone()
    return dict(row) if row else None


def update_threshold(customer_id: str, threshold: float):
    with get_connection() as conn:
        conn.execute(
            "UPDATE customers SET alert_threshold = ? WHERE id = ?",
            (threshold, customer_id)
        )
        conn.commit()


# ── Transactions ──────────────────────────────────────────────────────────────
def get_transactions(customer_id: str, flag_filter: Optional[str] = None) -> list[dict]:
    with get_connection() as conn:
        # Special filter: return stopped/disputed/cleared transactions
        if flag_filter == "actioned":
            rows = conn.execute(
                """SELECT * FROM transactions
                   WHERE customer_id = ? AND status IN ('stopped','disputed','cleared')
                   ORDER BY timestamp DESC""",
                (customer_id,)
            ).fetchall()
        elif flag_filter and flag_filter != "all":
            rows = conn.execute(
                """SELECT * FROM transactions 
                   WHERE customer_id = ? AND flag = ? AND status = 'active'
                   ORDER BY timestamp DESC""",
                (customer_id, flag_filter)
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT * FROM transactions 
                   WHERE customer_id = ? AND status = 'active'
                   ORDER BY timestamp DESC""",
                (customer_id,)
            ).fetchall()
    return [dict(r) for r in rows]


def get_transaction(transaction_id: str) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM transactions WHERE id = ?",
            (transaction_id,)
        ).fetchone()
    return dict(row) if row else None


def update_transaction_status(transaction_id: str, status: str, action: str):
    with get_connection() as conn:
        conn.execute(
            "UPDATE transactions SET status = ? WHERE id = ?",
            (status, transaction_id)
        )
        conn.execute(
            "INSERT INTO transaction_actions (transaction_id, action) VALUES (?, ?)",
            (transaction_id, action)
        )
        conn.commit()


def get_transaction_summary(customer_id: str) -> dict:
    with get_connection() as conn:
        row = conn.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN flag = 'red' AND status = 'active' THEN 1 ELSE 0 END) as red_count,
                SUM(CASE WHEN flag = 'yellow' AND status = 'active' THEN 1 ELSE 0 END) as yellow_count,
                SUM(CASE WHEN flag = 'green' AND status = 'active' THEN 1 ELSE 0 END) as green_count,
                SUM(amount) as total_spent
            FROM transactions 
            WHERE customer_id = ?
        """, (customer_id,)).fetchone()
    return dict(row) if row else {}


# ── Chat History ──────────────────────────────────────────────────────────────
def save_chat_message(customer_id: str, role: str, message: str):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO chat_history (customer_id, role, message) VALUES (?, ?, ?)",
            (customer_id, role, message)
        )
        conn.commit()


def get_chat_history(customer_id: str, limit: int = 20) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT role, message, timestamp FROM chat_history 
               WHERE customer_id = ? ORDER BY timestamp DESC LIMIT ?""",
            (customer_id, limit)
        ).fetchall()
    return [dict(r) for r in reversed(rows)]


def clear_chat_history(customer_id: str):
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM chat_history WHERE customer_id = ?",
            (customer_id,)
        )
        conn.commit()
