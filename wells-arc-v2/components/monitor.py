"""
Wells Arc - Smart Monitor Component
Correct Streamlit pattern: HTML cards for display only.
Buttons are always OUTSIDE html blocks — no mixing.
"""

import streamlit as st
from database.db_helpers import (
    get_transactions, update_transaction_status,
    get_transaction_summary, update_threshold
)

FLAG_CONFIG = {
    "red": {
        "emoji": "🔴", "label": "Suspicious",
        "bg": "#FCEBEB", "border": "#E24B4A",
        "badge_bg": "#F7C1C1", "badge_color": "#791F1F",
        "text": "#791F1F",
    },
    "yellow": {
        "emoji": "🟡", "label": "Above Threshold",
        "bg": "#FAEEDA", "border": "#EF9F27",
        "badge_bg": "#FAC775", "badge_color": "#633806",
        "text": "#633806",
    },
    "green": {
        "emoji": "🟢", "label": "Clear",
        "bg": "#F0FFF4", "border": "#639922",
        "badge_bg": "#C0DD97", "badge_color": "#27500A",
        "text": "#27500A",
    },
}

ACTION_CONFIG = {
    "stopped": {
        "emoji": "🛑", "label": "Transaction Stopped",
        "bg": "#FFF8E1", "border": "#FFC107", "badge": "#FFC107",
        "message": "Transaction stopped. A Wells Fargo specialist will contact you within 24 hours to confirm the block and process any eligible refund.",
    },
    "disputed": {
        "emoji": "🚫", "label": "Dispute Filed",
        "bg": "#E8F4FD", "border": "#2196F3", "badge": "#2196F3",
        "message": "Dispute filed. You are protected under Wells Fargo Zero Liability — you will not be charged for unauthorized transactions.",
    },
    "cleared": {
        "emoji": "✅", "label": "Cleared by You",
        "bg": "#F0FFF4", "border": "#639922", "badge": "#639922",
        "message": "You confirmed this transaction is legitimate. No further action needed.",
    },
}


def card_html(bg, border, content_html):
    """
    Renders a complete, self-contained styled card.
    One opening tag, one closing tag — always balanced.
    Content must be a single string with no unclosed tags.
    """
    return f"""<div style="background:{bg};border:1.5px solid {border};border-radius:12px;padding:14px 18px;margin-bottom:6px;">{content_html}</div>"""


def render_summary_cards(customer_id: str):
    summary = get_transaction_summary(customer_id)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🔴 Suspicious", summary.get("red_count", 0),
                  help="Transactions flagged as suspicious")
    with col2:
        st.metric("🟡 Above Threshold", summary.get("yellow_count", 0),
                  help="Transactions above your alert threshold")
    with col3:
        st.metric("🟢 Clear", summary.get("green_count", 0),
                  help="Normal transactions")
    with col4:
        total = summary.get("total_spent", 0) or 0
        st.metric("💳 Total (30 days)", f"${total:,.2f}")


def render_threshold_control(customer: dict):
    st.markdown("#### ⚙️ Your Alert Threshold")
    st.caption("Transactions above this amount will be flagged yellow for your attention.")
    new_threshold = st.slider(
        "Alert threshold ($)",
        min_value=100, max_value=5000,
        value=int(customer["alert_threshold"]),
        step=50, format="$%d", key="threshold_slider"
    )
    if new_threshold != int(customer["alert_threshold"]):
        update_threshold(customer["id"], new_threshold)
        st.session_state.customer["alert_threshold"] = float(new_threshold)
        st.success(f"✅ Threshold updated to ${new_threshold:,}")
        st.rerun()


def render_actioned_transactions(customer_id: str):
    actioned = get_transactions(customer_id, flag_filter="actioned")
    if not actioned:
        return

    with st.expander(f"📂 Actions Taken — {len(actioned)} transaction(s)", expanded=True):
        st.caption("Wells Fargo has been notified and will follow up where required.")
        for txn in actioned:
            status = txn.get("status", "")
            cfg = ACTION_CONFIG.get(status)
            if not cfg:
                continue

            # Build content as one string — no unclosed tags
            merchant = txn['merchant_name']
            amount = f"${txn['amount']:,.2f}"
            loc = txn.get('location', 'Unknown')
            ts = txn['timestamp'][:16]
            label = cfg['label']
            badge_color = cfg['badge']
            emoji = cfg['emoji']
            msg = cfg['message']
            bg = cfg['bg']
            border = cfg['border']

            content = (
                f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
                f"<span style='font-size:15px;font-weight:600;color:#1a1a1a;'>{emoji} {merchant} "
                f"<span style='background:{badge_color};color:white;font-size:10px;font-weight:600;"
                f"padding:2px 8px;border-radius:4px;margin-left:6px;'>{label}</span></span>"
                f"<span style='font-weight:700;color:#555;'>-{amount}</span>"
                f"</div>"
                f"<div style='font-size:12px;color:#666;margin-top:4px;'>📍 {loc} &nbsp;·&nbsp; 🕐 {ts}</div>"
                f"<div style='margin-top:8px;padding:8px 10px;background:rgba(255,255,255,0.75);"
                f"border-radius:6px;font-size:12px;color:#333;'>🏦 {msg}</div>"
            )
            st.markdown(card_html(bg, border, content), unsafe_allow_html=True)


def render_transaction_card(txn: dict, idx: int):
    flag = txn["flag"]
    cfg = FLAG_CONFIG[flag]

    merchant = txn['merchant_name']
    amount = f"${txn['amount']:,.2f}"
    location = txn.get('location', 'Unknown')
    timestamp = txn['timestamp'][:16]
    category = txn.get('category', 'General')
    recurring = "&nbsp;·&nbsp; 🔄 Recurring" if txn.get("is_recurring") else ""
    flag_reason = txn.get("flag_reason", "")

    # Build flag reason line — only if present, fully self-contained
    reason_line = ""
    if flag_reason:
        reason_line = (
            f"<div style='margin-top:6px;font-size:11px;color:{cfg['text']};"
            f"font-weight:500;background:rgba(255,255,255,0.6);border-radius:4px;"
            f"padding:4px 8px;'>⚠️ {flag_reason}</div>"
        )

    # One complete self-contained HTML block — display only
    content = (
        f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
        f"<div><span style='font-size:15px;font-weight:600;color:#1a1a1a;'>{cfg['emoji']} {merchant}</span>"
        f"<span style='background:{cfg['badge_bg']};color:{cfg['badge_color']};font-size:10px;"
        f"font-weight:600;padding:2px 8px;border-radius:4px;margin-left:8px;'>{cfg['label']}</span>"
        f"</div>"
        f"<span style='font-size:16px;font-weight:700;color:#1a1a1a;'>-{amount}</span>"
        f"</div>"
        f"<div style='margin-top:4px;font-size:12px;color:#555;'>"
        f"📍 {location} &nbsp;·&nbsp; 🕐 {timestamp} &nbsp;·&nbsp; 📂 {category}{recurring}"
        f"</div>"
        f"{reason_line}"
    )

    st.markdown(card_html(cfg['bg'], cfg['border'], content), unsafe_allow_html=True)

    # Buttons OUTSIDE html — pure Streamlit, no mixing
    if flag in ["red", "yellow"]:
        col1, col2, col3, col4 = st.columns([2, 2.5, 2, 3])

        with col1:
            if st.button(
                "🛑 Stop",
                key=f"stop_{txn['id']}_{idx}",
                help="Immediately stop this transaction",
                type="primary" if flag == "red" else "secondary",
                use_container_width=True,
            ):
                update_transaction_status(txn["id"], "stopped", "stopped")
                st.rerun()

        with col2:
            if st.button(
                "🚫 Unauthorized",
                key=f"unauth_{txn['id']}_{idx}",
                help="Mark as unauthorized and file a dispute",
                use_container_width=True,
            ):
                update_transaction_status(txn["id"], "disputed", "disputed")
                st.rerun()

        with col3:
            if st.button(
                "✅ It's Mine",
                key=f"dismiss_{txn['id']}_{idx}",
                help="This transaction is legitimate",
                use_container_width=True,
            ):
                update_transaction_status(txn["id"], "cleared", "dismissed")
                st.rerun()

        with col4:
            if st.button(
                "💬 Ask AI",
                key=f"ask_{txn['id']}_{idx}",
                help="Open AI assistant for this transaction",
                use_container_width=True,
            ):
                st.session_state.switch_to_ai = True
                st.session_state.transaction_context = txn
                st.session_state.prefill_message = (
                    f"Can you explain this flagged transaction: "
                    f"{txn['merchant_name']} for ${txn['amount']:,.2f} "
                    f"on {txn['timestamp'][:16]}? Should I be concerned?"
                )
                st.rerun()

    # Spacer between cards
    st.markdown("<div style='margin-bottom:4px'></div>", unsafe_allow_html=True)


def render_monitor(customer: dict):
    # ── Banner when AI question is queued ─────────────────────────────────────
    if st.session_state.get("switch_to_ai") or st.session_state.get("transaction_context"):
        txn = st.session_state.get("transaction_context")
        merchant = txn['merchant_name'] if txn else "your transaction"
        st.markdown(f"""
        <div style="background:#8B0000;border-radius:10px;padding:14px 20px;margin-bottom:16px;
        display:flex;align-items:center;justify-content:space-between;">
            <div style="color:white;font-size:14px;font-weight:500;">
                💬 Question about <strong>{merchant}</strong> is ready in the AI Assistant tab
            </div>
            <div style="color:rgba(255,255,255,0.85);font-size:13px;">
                👆 Click <strong>AI Assistant</strong> tab above to continue
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("## 🏦 Smart Transaction Monitor")
    st.caption("Real-time transaction intelligence — your account health at a glance.")
    st.divider()

    render_summary_cards(customer["id"])
    st.divider()

    render_threshold_control(customer)
    st.divider()

    render_actioned_transactions(customer["id"])

    st.markdown("#### 📋 Active Transactions")
    col1, col2 = st.columns([3, 1])
    with col1:
        filter_option = st.selectbox(
            "Filter by",
            ["All", "🔴 Suspicious Only", "🟡 Above Threshold", "🟢 Clear"],
            key="txn_filter"
        )
    with col2:
        st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
        if st.button("🔄 Refresh", key="refresh_txns"):
            st.rerun()

    flag_map = {
        "All": "all",
        "🔴 Suspicious Only": "red",
        "🟡 Above Threshold": "yellow",
        "🟢 Clear": "green",
    }
    transactions = get_transactions(customer["id"], flag_map.get(filter_option, "all"))

    if not transactions:
        st.info("✅ No active transactions for this filter.")
        return

    for idx, txn in enumerate(transactions):
        render_transaction_card(txn, idx)
