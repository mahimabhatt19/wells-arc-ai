"""
Wells Arc - Main Application
AI-Powered Fraud Intelligence & Conversational Support for Wells Fargo
Run: streamlit run app.py
"""

import streamlit as st
import os
from dotenv import load_dotenv
from database.db_helpers import get_customer
from components.monitor import render_monitor
from components.chat import render_assistant

load_dotenv()

# Auto-seed database if it doesn't exist (required for Streamlit Cloud)
DB_PATH = os.path.join(os.path.dirname(__file__), "database", "wells_arc.db")
if not os.path.exists(DB_PATH):
    from database.seed_data import seed_database
    seed_database()
# ```

# ---

# **Change 2 — `.gitignore`**

# Find and delete this line:
# ```
# database/wells_arc.db

st.set_page_config(
    page_title="Wells Arc",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Global CSS — styling only, no content divs
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Tabs */
.stTabs [data-baseweb="tab-list"] { gap: 8px; margin-top: 8px; }
.stTabs [data-baseweb="tab"] {
    height: 46px; padding: 0 28px;
    border-radius: 8px; font-size: 15px; font-weight: 500;
    background: #f5f5f5;
}
.stTabs [aria-selected="true"] {
    background-color: #8B0000 !important;
    color: white !important;
}

/* Primary buttons */
.stButton > button[kind="primary"] {
    background-color: #8B0000 !important;
    border-color: #8B0000 !important;
    color: white !important;
    border-radius: 8px !important;
}
.stButton > button[kind="primary"]:hover {
    background-color: #6B0000 !important;
    border-color: #6B0000 !important;
}

/* All other buttons */
.stButton > button {
    border-radius: 8px !important;
    font-weight: 500 !important;
}

/* Metric values */
[data-testid="stMetricValue"] {
    font-size: 26px !important;
    font-weight: 700 !important;
}

/* Container cards */
[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 12px !important;
    padding: 4px !important;
}

/* Sidebar */
[data-testid="stSidebar"] { background: #F8F9FA; }
[data-testid="stSidebar"] .stMarkdown h2 { color: #8B0000; }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    defaults = {
        "customer": None,
        "logged_in": False,
        "switch_to_ai": False,
        "transaction_context": None,
        "prefill_message": "",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def render_login():
    # Header
    st.markdown("""
    <div style="background:#8B0000;padding:32px 40px;border-radius:16px;margin-bottom:32px;text-align:center;">
        <div style="font-size:48px;">🏦</div>
        <div style="color:white;font-size:32px;font-weight:700;margin-top:8px;">Wells Arc</div>
        <div style="color:rgba(255,255,255,0.8);font-size:15px;margin-top:6px;">
            AI-Powered Fraud Intelligence &amp; Conversational Support
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### Sign In to Your Account")
        st.caption("Enter your Wells Fargo account number to continue.")

        with st.form("login_form"):
            account_number = st.text_input(
                "Account Number",
                placeholder="e.g. WF-4521-8832",
            )
            submitted = st.form_submit_button(
                "Sign In →", use_container_width=True, type="primary"
            )

        if submitted:
            if not account_number:
                st.error("Please enter your account number.")
                return
            customer = get_customer(account_number.strip())
            if customer:
                st.session_state.customer = customer
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Account not found. Try WF-4521-8832 or WF-7743-2291")

        st.divider()
        st.markdown("**Demo accounts:**")
        st.code("WF-4521-8832  →  Sarah Mitchell")
        st.code("WF-7743-2291  →  James Rivera")


def render_sidebar(customer: dict):
    with st.sidebar:
        st.markdown("""
        <div style="background:#8B0000;border-radius:12px;padding:16px 20px;margin-bottom:16px;">
            <div style="color:white;font-size:20px;font-weight:700;">🏦 Wells Arc</div>
            <div style="color:rgba(255,255,255,0.8);font-size:12px;margin-top:4px;">Powered by Wells Fargo AI</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"**👤 {customer['name']}**")
        st.caption(f"Account: `{customer['account_number']}`")
        st.caption(f"Type: {customer['account_type']}")

        st.metric("Balance", f"${customer['balance']:,.2f}")
        st.metric("Alert Threshold", f"${customer['alert_threshold']:,.0f}")

        st.divider()
        st.markdown("**🔐 Security Status**")
        st.success("Account Protected")
        st.caption("Zero Liability covers all unauthorized transactions.")

        st.divider()
        st.markdown("**📞 24/7 Support**")
        st.code("1-800-869-3557")

        st.divider()
        if st.button("🚪 Sign Out", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


def main():
    init_session_state()

    if not st.session_state.logged_in:
        render_login()
        return

    customer = st.session_state.customer
    render_sidebar(customer)

    # Page header
    st.markdown(f"""
    <div style="background:#8B0000;padding:18px 28px;border-radius:12px;margin-bottom:8px;display:flex;align-items:center;justify-content:space-between;">
        <div>
            <div style="color:white;font-size:22px;font-weight:700;">🏦 Wells Arc</div>
            <div style="color:rgba(255,255,255,0.8);font-size:13px;margin-top:2px;">
                Welcome back, {customer['name']} &nbsp;·&nbsp; Account {customer['account_number']}
            </div>
        </div>
        <div style="color:rgba(255,255,255,0.6);font-size:12px;">AI-Powered Banking Intelligence</div>
    </div>
    """, unsafe_allow_html=True)

    switch_to_ai = st.session_state.get("switch_to_ai", False)
    if switch_to_ai:
        st.session_state.switch_to_ai = False

    tab1, tab2 = st.tabs(["📊 Smart Monitor", "💬 AI Assistant"])

    if switch_to_ai:
        with tab2:
            render_assistant(customer)
        with tab1:
            render_monitor(customer)
    else:
        with tab1:
            render_monitor(customer)
        with tab2:
            render_assistant(customer)


if __name__ == "__main__":
    main()
