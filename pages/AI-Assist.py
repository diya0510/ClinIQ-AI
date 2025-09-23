# user_kb_chatbot.py
# -------------------------------------------------------------
# Dynamic per-user knowledge base with FAISS + RAG chatbot
# - One FAISS index per user (clean isolation)
# - Rebuild/refresh on report/profile updates
# - Streamlit UI: upload/update + chat
# -------------------------------------------------------------

from __future__ import annotations
import os
import json
from pathlib import Path
from typing import List, Dict, Optional

import streamlit as st
from dotenv import load_dotenv

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings, HuggingFaceEndpoint, ChatHuggingFace
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA

# If you already have db helpers
from config.db_connection import get_connection

# ---------------------------
# Config
# ---------------------------
load_dotenv()
BASE_INDEX_DIR = Path("faiss_indexes")  # each user will have faiss_indexes/user_<id>/
BASE_INDEX_DIR.mkdir(parents=True, exist_ok=True)

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

llm_hf = HuggingFaceEndpoint(
    repo_id="mistralai/Mistral-7B-Instruct-v0.3",
    task="text-generation",
)
CHAT_LLM = ChatHuggingFace(llm=llm_hf)
EMBEDDINGS = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
SPLITTER = RecursiveCharacterTextSplitter(chunk_size=750, chunk_overlap=120)

# ---------------------------
# DB helpers
# ---------------------------
conn = get_connection()
cursor = conn.cursor()

def get_user_health_profile(user_id: int) -> Optional[Dict[str, str]]:
    query = """
    SELECT weight, height, blood_group, blood_pressure, heart_rate, chronic_diseases,
           family_history, allergies, medications, diet, water_intake, sleep, smoking, alcohol
    FROM user_health_profile
    WHERE user_id = ?
    """
    cursor.execute(query, (user_id,))
    row = cursor.fetchone()
    if not row:
        return None
    keys = [
        'weight','height','blood_group','blood_pressure','heart_rate','chronic_diseases','family_history',
        'allergies','medications','diet','water_intake','sleep','smoking','alcohol'
    ]
    return dict(zip(keys, row))


def get_latest_report_summaries(user_id: int) -> Dict[str, str]:
    query = """
    SELECT r1.report_type, r1.report_data
    FROM reports r1
    INNER JOIN (
        SELECT report_type, MAX(report_date) AS max_date
        FROM reports
        WHERE user_id = ?
        GROUP BY report_type
    ) r2
    ON r1.report_type = r2.report_type AND r1.report_date = r2.max_date
    WHERE r1.user_id = ?
    """
    cursor.execute(query, (user_id, user_id))
    rows = cursor.fetchall()
    return {row[0]: row[1] for row in rows}

# ---------------------------
# FAISS per-user helpers
# ---------------------------

def _user_index_dir(user_id: int) -> Path:
    return BASE_INDEX_DIR / f"user_{user_id}"


def load_user_vectorstore(user_id: int) -> Optional[FAISS]:
    udir = _user_index_dir(user_id)
    if not udir.exists():
        return None
    try:
        vs = FAISS.load_local(str(udir), embeddings=EMBEDDINGS, allow_dangerous_deserialization=True)
        return vs
    except Exception:
        return None


def save_user_vectorstore(user_id: int, vectorstore: FAISS) -> None:
    udir = _user_index_dir(user_id)
    udir.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(udir))


# ---------------------------
# Building documents
# ---------------------------

def _profile_to_text(profile: Dict[str, str]) -> str:
    return "\n".join([f"{k.replace('_',' ').title()}: {v}" for k, v in profile.items() if v is not None])


def _summaries_to_text(summaries: Dict[str, str]) -> str:
    parts = [f"{k} Report Summary:\n{v}" for k, v in summaries.items()]
    return "\n\n".join(parts)


def build_user_documents(user_id: int) -> List[Document]:
    docs: List[Document] = []

    profile = get_user_health_profile(user_id)
    if profile:
        text = _profile_to_text(profile)
        docs.append(Document(page_content=text, metadata={"user_id": user_id, "type": "profile"}))

    summaries = get_latest_report_summaries(user_id)
    if summaries:
        text = _summaries_to_text(summaries)
        docs.append(Document(page_content=text, metadata={"user_id": user_id, "type": "reports"}))

    return docs


# ---------------------------
# Create / Rebuild / Upsert
# ---------------------------

def rebuild_user_kb(user_id: int) -> Optional[FAISS]:
    """Rebuilds the user's FAISS index from DB sources (profile + latest summaries)."""
    docs = build_user_documents(user_id)
    if not docs:
        return None

    # chunk docs
    chunks = SPLITTER.split_documents(docs)

    # create FAISS from scratch
    vs = FAISS.from_documents(chunks, EMBEDDINGS)
    save_user_vectorstore(user_id, vs)
    return vs


def upsert_free_text(user_id: int, texts: List[str], kind: str = "note") -> FAISS:
    """Adds arbitrary extra texts for the user (e.g., new report OCR text)."""
    vs = load_user_vectorstore(user_id)
    metadatas = [{"user_id": user_id, "type": kind} for _ in texts]
    docs = [Document(page_content=t, metadata=metadatas[i]) for i, t in enumerate(texts) if t and t.strip()]
    chunks = SPLITTER.split_documents(docs)

    if vs is None:
        vs = FAISS.from_documents(chunks, EMBEDDINGS)
    else:
        vs.add_documents(chunks)

    save_user_vectorstore(user_id, vs)
    return vs


# ---------------------------
# RAG: retriever + QA chain
# ---------------------------

def get_user_retriever(user_id: int):
    vs = load_user_vectorstore(user_id)
    if vs is None:
        # try to build from DB if nothing exists yet
        vs = rebuild_user_kb(user_id)
    if vs is None:
        return None
    return vs.as_retriever(search_kwargs={"k": 4})


def build_qa_chain(user_id: int):
    retriever = get_user_retriever(user_id)
    if retriever is None:
        return None
    chain = RetrievalQA.from_chain_type(
        llm=CHAT_LLM,
        retriever=retriever,
        return_source_documents=True,
        chain_type="stuff",
    )
    return chain


# ---------------------------
# Streamlit UI (embed in your existing app/page)
# ---------------------------

def ui_chat_and_kb(user_id: int):
    st.header("💬 Chat with your Health Data")

    # Refresh / rebuild KB from DB
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Rebuild Knowledge Base from DB"):
            vs = rebuild_user_kb(user_id)
            if vs is None:
                st.warning("No profile or report summaries found to build the KB.")
            else:
                st.success("Rebuilt your knowledge base from latest profile + reports.")

    with col2:
        with st.expander("➕ Add extra text (e.g., new report OCR/plain text)"):
            new_text = st.text_area("Paste text to add", height=180, placeholder="Paste extracted text from a new report...")
            if st.button("Add to KB"):
                if new_text.strip():
                    upsert_free_text(user_id, [new_text], kind="extra")
                    st.success("Added to your knowledge base.")
                else:
                    st.info("Nothing to add.")

    # Build/Load QA chain
    qa = build_qa_chain(user_id)
    if qa is None:
        st.info("Your knowledge base is empty. Please rebuild or add text.")
        return

    # Chat box
    st.subheader("Ask a question")
    query = st.text_input("Type your question about your reports, profile, or diet plan")
    if query:
        with st.spinner("Thinking..."):
            result = qa({"query": query})
        answer = result.get("result", "")
        sources: List[Document] = result.get("source_documents", [])

        st.markdown(f"**Answer:**\n\n{answer}")

        with st.expander("📚 Sources used"):
            for i, d in enumerate(sources, 1):
                m = d.metadata or {}
                st.markdown(f"**{i}.** *{m.get('type','doc')}* — `{m.get('user_id')}`\n\n{d.page_content[:400]}…")


# ---------------------------
# Example: how to mount into your current Streamlit page
# ---------------------------
if __name__ == "__main__":
    st.set_page_config(page_title="AI Assist", page_icon="🩺", layout="wide")

    # In your real app, user_id should come from session/auth
    user_id = st.session_state.get("user_id")
    if not user_id:
        st.warning("User not logged in. Please login to use the chatbot.")
    else:
        ui_chat_and_kb(user_id)
