import os
import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:7860").rstrip("/")
st.set_page_config(page_title="AuroraStay", page_icon="🏨", layout="wide")
st.title("🏨 AuroraStay — Policy Assistant")
st.write("Ask a hotel policy question and inspect the supporting sources.")
st.caption("Internal POC. Approved reference questions receive all four quality scores. "
           "New questions require manual verification when no independent reference is available.")
with st.sidebar:
    st.header("Parameters")
    k = st.slider("Chunks to retrieve", 1, 10, 3)
    temperature = st.slider("Temperature", 0.0, 1.0, 0.0, 0.1)
    max_tokens = st.slider("Maximum answer tokens", 64, 2048, 512, 64)
mode = st.radio("Response mode", ["Answer + Relevant Chunks", "Answer only"], horizontal=True)
with st.form("policy_question"):
    query = st.text_input("Your question", placeholder="What are the cancellation rules for an Advance Purchase booking?")
    submitted = st.form_submit_button("Submit", type="primary")
if submitted:
    if not query.strip():
        st.warning("Please enter a question.")
    else:
        endpoint = "/v1/answer" if mode == "Answer only" else "/v1/answer_with_relevant_chunks"
        try:
            with st.spinner("Retrieving policies and checking the draft…"):
                response = requests.post(BACKEND_URL + endpoint, json={
                    "query": query.strip(), "k": k, "temperature": temperature,
                    "top_p": 1.0, "max_tokens": max_tokens}, timeout=(10, 300))
                response.raise_for_status()
                result = response.json()
            if result["route"] == "AUTO ANSWER":
                st.success("AUTO ANSWER")
            else:
                st.warning("MANUAL LOOKUP — verify the draft against source policies before use.")
            st.subheader("Draft answer" if result["route"] != "AUTO ANSWER" else "Answer")
            st.write(result["answer"])
            st.caption(result["reason"])
            with st.expander("Quality scores"):
                st.json(result["scores"])
                st.json(result["judge_reasons"])
            for i, chunk in enumerate(result.get("relevant_chunks", []), 1):
                with st.expander(f"Source S{i}"):
                    st.text(chunk)
        except (requests.RequestException, ValueError, KeyError):
            st.error("Unable to obtain a complete response. Use manual lookup and check the backend service.")
