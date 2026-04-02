"""
Wells Arc - RAG Pipeline
Uses FAISS for vector search + Claude API for response generation.
Handles both general banking queries and transaction-specific questions.
"""

import os
import re
import pickle
import numpy as np
from typing import Optional
import anthropic

# ── Constants ────────────────────────────────────────────────────────────────
KB_PATH = os.path.join(os.path.dirname(__file__), "knowledge_base", "faq.txt")
INDEX_PATH = os.path.join(os.path.dirname(__file__), "faiss_index.pkl")
CHUNKS_PATH = os.path.join(os.path.dirname(__file__), "chunks.pkl")

CLAUDE_MODEL = "claude-haiku-4-5-20251001"  # Fast + cheap for demo
MAX_TOKENS = 512
TOP_K = 3  # Number of context chunks to retrieve


# ── Simple TF-IDF style embeddings (no external embedding API needed) ────────
def simple_embed(text: str, vocab: dict) -> np.ndarray:
    """
    Simple bag-of-words embedding.
    For production, replace with sentence-transformers or Claude embeddings.
    """
    text_lower = text.lower()
    words = re.findall(r'\b\w+\b', text_lower)
    vec = np.zeros(len(vocab))
    for word in words:
        if word in vocab:
            vec[vocab[word]] += 1
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec


def build_vocab(chunks: list[str]) -> dict:
    """Build vocabulary from all chunks."""
    vocab = {}
    idx = 0
    for chunk in chunks:
        words = re.findall(r'\b\w+\b', chunk.lower())
        for word in words:
            if word not in vocab:
                vocab[word] = idx
                idx += 1
    return vocab


# ── Knowledge base loading and indexing ──────────────────────────────────────
def load_knowledge_base() -> list[str]:
    """Load and chunk the FAQ knowledge base."""
    with open(KB_PATH, "r") as f:
        content = f.read()

    # Split by Q&A pairs
    chunks = []
    current_chunk = []

    for line in content.split("\n"):
        line = line.strip()
        if not line:
            if current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
        else:
            current_chunk.append(line)

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    # Filter out section headers and empty chunks
    chunks = [c for c in chunks if len(c) > 30 and not c.startswith("===")]
    return chunks


def build_index(chunks: list[str], vocab: dict) -> np.ndarray:
    """Build a simple vector index from chunks."""
    vectors = np.array([simple_embed(chunk, vocab) for chunk in chunks])
    return vectors


def get_or_build_index():
    """Load existing index or build new one."""
    if os.path.exists(INDEX_PATH) and os.path.exists(CHUNKS_PATH):
        with open(INDEX_PATH, "rb") as f:
            data = pickle.load(f)
        with open(CHUNKS_PATH, "rb") as f:
            chunks = pickle.load(f)
        return chunks, data["vectors"], data["vocab"]

    chunks = load_knowledge_base()
    vocab = build_vocab(chunks)
    vectors = build_index(chunks, vocab)

    with open(INDEX_PATH, "wb") as f:
        pickle.dump({"vectors": vectors, "vocab": vocab}, f)
    with open(CHUNKS_PATH, "wb") as f:
        pickle.dump(chunks, f)

    return chunks, vectors, vocab


def retrieve_context(query: str, top_k: int = TOP_K) -> list[str]:
    """Retrieve most relevant chunks for a query."""
    chunks, vectors, vocab = get_or_build_index()

    query_vec = simple_embed(query, vocab)

    # Cosine similarity
    if np.linalg.norm(query_vec) == 0:
        return chunks[:top_k]

    similarities = vectors @ query_vec
    top_indices = np.argsort(similarities)[::-1][:top_k]
    return [chunks[i] for i in top_indices]


# ── Claude API response generation ───────────────────────────────────────────
def get_ai_response(
    query: str,
    customer_name: str,
    chat_history: list[dict],
    transaction_context: Optional[dict] = None,
) -> str:
    """
    Generate AI response using RAG + Claude API.
    
    Args:
        query: Customer's question
        customer_name: Name for personalization
        chat_history: Previous messages in conversation
        transaction_context: Optional flagged transaction details
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return "⚠️ API key not configured. Please set ANTHROPIC_API_KEY in your .env file."

    client = anthropic.Anthropic(api_key=api_key)

    # ── Retrieve relevant context ─────────────────────────────────────────────
    context_chunks = retrieve_context(query)
    context = "\n\n".join(context_chunks)

    # ── Build transaction context if available ────────────────────────────────
    txn_context = ""
    if transaction_context:
        txn_context = f"""
FLAGGED TRANSACTION DETAILS:
- Merchant: {transaction_context.get('merchant_name', 'Unknown')}
- Amount: ${transaction_context.get('amount', 0):,.2f}
- Date/Time: {transaction_context.get('timestamp', 'Unknown')}
- Location: {transaction_context.get('location', 'Unknown')}
- Flag Reason: {transaction_context.get('flag_reason', 'Suspicious activity')}
"""

    # ── System prompt ─────────────────────────────────────────────────────────
    system_prompt = f"""You are the Wells Arc AI Assistant, a helpful and empathetic banking support assistant for Wells Fargo. Your job is to help customers with any banking questions, explain flagged transactions, and guide them through resolution steps.

CUSTOMER NAME: {customer_name}

KNOWLEDGE BASE CONTEXT:
{context}

{txn_context}

GUIDELINES:
- Be warm, clear, and reassuring — customers may be anxious about fraud
- Keep responses concise (2-4 sentences for simple questions, slightly longer for complex ones)
- Always personalize using the customer's name occasionally
- If a transaction is flagged red, acknowledge their concern and reassure them they're protected
- For unauthorized transactions, remind them Wells Fargo's Zero Liability policy covers them
- If you cannot fully resolve an issue, offer: (1) Connect with an agent, (2) Schedule a callback, (3) Send a PDF guide
- Never make up account-specific information — only use what's provided
- Do not output markdown formatting like ** or ## — use plain conversational text
- End complex responses by asking if there's anything else you can help with"""

    # ── Build messages ────────────────────────────────────────────────────────
    messages = []

    # Add chat history (last 6 messages for context)
    for msg in chat_history[-6:]:
        messages.append({
            "role": msg["role"],
            "content": msg["message"]
        })

    # Add current query
    messages.append({"role": "user", "content": query})

    # ── Call Claude API ───────────────────────────────────────────────────────
    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=MAX_TOKENS,
            system=system_prompt,
            messages=messages,
        )
        return response.content[0].text

    except anthropic.AuthenticationError:
        return "Authentication failed. Please check your Anthropic API key in the .env file."
    except anthropic.RateLimitError:
        return "I'm receiving a lot of requests right now. Please try again in a moment."
    except Exception as e:
        return f"I encountered an issue processing your request. Please try again or connect with a live agent."
