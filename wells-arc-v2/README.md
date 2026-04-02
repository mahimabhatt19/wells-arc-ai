# 🏦 Wells Arc

**AI-Powered Fraud Intelligence & Conversational Support, Built for Wells Fargo Customers**

Wells Arc is a full-stack AI banking assistant that gives customers real-time transaction monitoring and 24/7 conversational support — all within the existing Wells Fargo portal. No new app. No hold times. Just clarity and control.

---

## ✨ Features

### 🔴🟡🟢 Smart Transaction Monitor
- Real-time transaction flagging with a three-tier system
- **Red** — unauthorized or suspicious activity (immediate action required)
- **Yellow** — above customer's self-set threshold (review recommended)
- **Green** — normal, cleared transactions
- Customer-controlled alert threshold (adjustable slider)
- One-click actions: **Stop Transaction**, **Mark as Unauthorized**, **Dismiss**
- **Actions Taken** section — tracks every actioned transaction with a Wells Fargo confirmation message

### 💬 AI Assistant (RAG-Powered)
- Answers any banking question 24/7 using retrieval-augmented generation
- Explains flagged transactions in plain English
- Context-aware — automatically loads flagged transaction details from the Smart Monitor
- Smart escalation: connect with agent now, schedule a callback, or receive a PDF guide
- Powered by **Groq (Llama 3.3 70B)** + FAISS vector search

### 🤖 Hybrid Anomaly Detection
- **Rule-based engine** — catches suspicious merchants, odd hours, unusual locations, high-risk categories
- **Isolation Forest ML model** — learns from transaction patterns
- Combined 60/40 weighted scoring for high-accuracy, explainable classification

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit |
| AI Assistant | Groq API (Llama 3.3 70B Versatile) — Free |
| RAG Pipeline | FAISS + custom TF-IDF embeddings |
| Anomaly Detection | Scikit-learn Isolation Forest + Rule Engine |
| Database | SQLite |
| Language | Python 3.9+ |
| Deployment | Streamlit Cloud |

---

## 🚀 Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/mahimabhatt19/wells-arc.git
cd wells-arc
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up your API key
```bash
cp .env.example .env
```
Open `.env` and add your Groq API key:
```
GROQ_API_KEY=gsk_your-key-here
```
Get your **free** API key at [console.groq.com](https://console.groq.com) — no credit card required.

### 5. Seed the database
```bash
python database/seed_data.py
```

### 6. Run the app
```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 🔑 Demo Accounts

| Account Number | Customer | Alert Threshold |
|----------------|----------|----------------|
| `WF-4521-8832` | Sarah Mitchell | $500 |
| `WF-7743-2291` | James Rivera | $1,000 |

---

## 📁 Project Structure

```
wells-arc/
├── app.py                          # Streamlit entry point + routing
├── requirements.txt
├── .env.example                    # API key template
├── .gitignore
│
├── database/
│   ├── schema.sql                  # SQLite table definitions
│   ├── seed_data.py                # Synthetic transaction data generator
│   └── db_helpers.py               # All database operations
│
├── anomaly/
│   ├── rule_engine.py              # Rule-based flagging (merchant, location, time, amount)
│   └── ml_detector.py             # Isolation Forest + hybrid 60/40 scoring
│
├── assistant/
│   ├── rag_pipeline.py             # RAG + Groq API response generation
│   └── knowledge_base/
│       └── faq.txt                 # Wells Fargo FAQ knowledge base
│
└── components/
    ├── monitor.py                  # Smart Monitor tab UI
    └── chat.py                     # AI Assistant tab UI
```

---

## 🎯 Architecture

```
Transaction Data (SQLite)
        ↓
Anomaly Detection Engine
  ├── Rule Engine (merchant, location, time, amount)
  └── Isolation Forest ML Model
        ↓
Flag Classification (🔴 Red / 🟡 Yellow / 🟢 Green)
        ↓
Customer Portal (Streamlit)
  ├── Smart Monitor Tab
  │     ├── Summary metrics
  │     ├── Alert threshold control
  │     ├── Actions Taken tracker
  │     └── Transaction cards with Stop / Unauthorized / Dismiss / Ask AI
  └── AI Assistant Tab
        ├── FAISS Vector Search (knowledge base retrieval)
        └── Groq LLM (response generation)
```

---

## 🔒 Responsible AI

- **Human-in-the-loop** — live agents always available for escalation
- **Explainability** — every flag includes a plain-English reason
- **Privacy** — no sensitive data stored beyond the session
- **Zero Liability** — all unauthorized transactions covered under Wells Fargo policy
- **Bias audits** — rule engine is fully transparent and auditable

---

## 🌐 Deploy to Streamlit Cloud

1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repository
4. Add `GROQ_API_KEY` in the Secrets section
5. Deploy — your app gets a public shareable URL instantly

---

## 👩‍💻 Author

**Mahima Bhatt**
MS Computer Science | Texas A&M University
[LinkedIn](https://linkedin.com/in/mahima-bhatt-02223b190) · [GitHub](https://github.com/mahimabhatt19)

---

## 📄 License

MIT License — feel free to use this project as a reference or starting point.

---

*Built as part of the Wells Fargo x GCA Early Talent Competition*
