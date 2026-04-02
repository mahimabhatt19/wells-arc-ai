"""
Wells Arc - AI Assistant Component
Conversational banking support with RAG + Claude API.
"""

import streamlit as st
from database.db_helpers import get_chat_history, save_chat_message, clear_chat_history
from assistant.rag_pipeline import get_ai_response

QUICK_QUESTIONS = [
    "How do I dispute a transaction?",
    "What is Wells Fargo's fraud protection policy?",
    "How do I reset my password?",
    "How do I set up direct deposit?",
    "How do I avoid monthly fees?",
    "How do I open a new account?",
]


def render_resolution_options(suffix: str = ""):
    st.markdown("""
    <div style="background:#F8F9FA;border:1px solid #E0E0E0;border-radius:10px;padding:12px 16px;margin:8px 0;">
        <div style="font-size:13px;font-weight:600;color:#1a1a1a;margin-bottom:8px;">Need more help? Choose an option:</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📞 Connect with agent", use_container_width=True, key=f"connect_agent_{suffix}"):
            st.success("✅ Connecting you with a Wells Fargo agent. Average wait: 2 minutes.")
    with col2:
        if st.button("📅 Schedule callback", use_container_width=True, key=f"schedule_cb_{suffix}"):
            st.info("📅 A Wells Fargo agent will call you back within 2 hours.")
    with col3:
        if st.button("📄 Get PDF guide", use_container_width=True, key=f"get_pdf_{suffix}"):
            st.info("📄 A step-by-step guide has been sent to your registered email.")


def render_assistant(customer: dict):
    st.markdown("## 💬 Wells Arc AI Assistant")
    st.caption("Ask me anything about your account, transactions, or banking. Available 24/7.")

    # Transaction context banner
    transaction_context = st.session_state.get("transaction_context")
    if transaction_context:
        st.markdown(f"""
        <div style="background:#FCEBEB;border:1.5px solid #E24B4A;border-radius:10px;
        padding:10px 16px;margin-bottom:12px;font-size:13px;">
            🔴 <strong>Flagged transaction loaded:</strong> {transaction_context['merchant_name']}
            — ${transaction_context['amount']:,.2f} ({transaction_context['timestamp'][:16]})
        </div>
        """, unsafe_allow_html=True)

        if st.button("✕ Clear context", key="clear_ctx"):
            st.session_state.transaction_context = None
            st.rerun()

    st.divider()

    # Quick questions
    st.markdown("**Quick questions:**")
    cols = st.columns(3)
    for i, question in enumerate(QUICK_QUESTIONS):
        with cols[i % 3]:
            if st.button(question, key=f"quick_{i}", use_container_width=True):
                st.session_state.prefill_message = question

    st.divider()

    # Chat history
    chat_history = get_chat_history(customer["id"])

    for msg in chat_history:
        if msg["role"] == "user":
            with st.chat_message("user", avatar="👤"):
                st.markdown(msg["message"])
        else:
            with st.chat_message("assistant", avatar="🏦"):
                st.markdown(msg["message"])

    # Show resolution options if last AI message suggests escalation
    if chat_history and chat_history[-1]["role"] == "assistant":
        escalation_phrases = ["connect", "agent", "callback", "pdf", "guide", "cannot", "unfortunately"]
        if any(p in chat_history[-1]["message"].lower() for p in escalation_phrases):
            render_resolution_options(suffix="history")

    # Input
    prefill = st.session_state.pop("prefill_message", "")
    user_input = st.chat_input(
        placeholder="Ask anything — dispute a charge, understand a fee, navigate the portal..."
    )

    if prefill and not user_input:
        user_input = prefill

    if user_input:
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)
        save_chat_message(customer["id"], "user", user_input)

        with st.spinner("Wells Arc is thinking..."):
            response = get_ai_response(
                query=user_input,
                customer_name=customer["name"],
                chat_history=chat_history,
                transaction_context=transaction_context,
            )

        with st.chat_message("assistant", avatar="🏦"):
            st.markdown(response)
        save_chat_message(customer["id"], "assistant", response)

        escalation_phrases = ["connect", "agent", "callback", "pdf", "guide", "cannot", "unfortunately"]
        if any(p in response.lower() for p in escalation_phrases):
            render_resolution_options(suffix="response")

        st.rerun()

    # Clear chat
    if chat_history:
        st.divider()
        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("🗑️ Clear chat", key="clear_chat"):
                clear_chat_history(customer["id"])
                st.session_state.transaction_context = None
                st.rerun()
