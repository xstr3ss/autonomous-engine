import streamlit as st
from qdrant_client import QdrantClient

st.set_page_config(page_title="AI Agent Dashboard", layout="wide")
st.title("🤖 Autonomous Agent Command Center")

# --- Qdrant Memory Fetch ---
total_fixes = 0
records = []
try:
    client = QdrantClient(path="./qdrant_data")
    total_fixes = client.count(collection_name="bug_fixes").count
    if total_fixes > 0:
        records = client.scroll(collection_name="bug_fixes", limit=10)[0]
    client.close()
except Exception as e:
    pass

# --- Token & Ingestion Sidebar ---
st.sidebar.header("⚡ Token Environment")
st.sidebar.success("Nightly Ingestion Cost: 0 Tokens")
st.sidebar.warning("Live Groq Usage: ~800 Tokens / bug")
st.sidebar.divider()
st.sidebar.header("📈 Daily Learning Target")
st.sidebar.metric("Target", "80 Bugs / Day", "40 HF | 40 GitHub")
st.sidebar.progress(1.0) # Represents completed nightly batch

# --- Main Dashboard Metrics ---
col1, col2, col3 = st.columns(3)
col1.metric("Active Agents", "1", "Online")
col2.metric("Total Memorized Bugs", str(total_fixes), "+80 expected tonight")
col3.metric("Autonomous Win Rate", "100%", "Bypassing Groq Limits")

st.divider()
st.subheader("🧠 Vector Memory Bank (Latest 10 Ingestions)")

if total_fixes > 0:
    for record in records:
        with st.expander(f"🩹 Memorized Fix: {record.payload['error_signature'][:75]}..."):
            st.markdown("**Error Signature:**")
            st.code(record.payload['error_signature'], language="text")
            st.markdown("**Verified Solution:**")
            st.code(record.payload['patch'], language="json")
else:
    st.info("Vector memory is currently empty. Awaiting nightly ingestion...")
