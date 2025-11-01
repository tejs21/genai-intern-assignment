"""
frontend/app.py
----------------
Streamlit frontend for the Post-Discharge Nephrology Assistant POC.

Implements a two-agent interface:
1. Receptionist Agent — identifies patient and retrieves discharge summary.
2. Clinical Agent — answers follow-up queries using RAG and optional web search.

Backend: Flask API (see backend/app.py)
"""

import os
import random
import requests
import streamlit as st

# ------------------------------------------------------------
# Backend Configuration
# ------------------------------------------------------------
# Default backend URL if not set via environment variable
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5000")

# ------------------------------------------------------------
# Streamlit Page Configuration
# ------------------------------------------------------------
st.set_page_config(page_title="Post-Discharge Nephrology Assistant", layout="centered")

st.title("Post-Discharge Nephrology Assistant — POC")
st.markdown("""
This Proof-of-Concept demonstrates a **two-agent clinical assistant** system:

- **Receptionist Agent:** Identifies the patient and retrieves their discharge summary.  
- **Clinical Agent:** Answers follow-up questions using Retrieval-Augmented Generation (RAG)
  and performs web search fallback if necessary.
""")

# ------------------------------------------------------------
# Session State Initialization
# ------------------------------------------------------------
if "session_id" not in st.session_state:
    st.session_state.session_id = "sess_" + str(random.randint(10000, 99999))
if "patient" not in st.session_state:
    st.session_state.patient = None
if "chat" not in st.session_state:
    st.session_state.chat = []

# ------------------------------------------------------------
# Sidebar Controls
# ------------------------------------------------------------
st.sidebar.header("Controls")
if st.sidebar.button("Reset Session"):
    """Resets current patient session and chat history."""
    st.session_state.patient = None
    st.session_state.chat = []
    st.experimental_rerun()

# ------------------------------------------------------------
# Receptionist Section
# ------------------------------------------------------------
st.markdown("---")
st.subheader("Receptionist Desk")
st.write("Please identify yourself using your **name or patient ID** (e.g., `P001`).")

with st.form("receptionist_form"):
    user_input = st.text_input("Enter your name or patient ID:")
    submitted = st.form_submit_button("Find Patient")

    if submitted:
        if not user_input:
            st.warning("Please enter a name or patient ID.")
        else:
            try:
                # Call backend /receptionist endpoint
                resp = requests.post(
                    f"{BACKEND_URL}/receptionist",
                    json={"message": user_input, "patient_name": user_input},
                    timeout=10
                )
                data = resp.json()
            except Exception as e:
                st.error(f"Backend call failed: {e}")
                data = {"text": "Backend not reachable."}

            # Store response in chat log
            st.session_state.chat.append({"from": "receptionist", "text": data.get("text")})

            # Store patient info if found
            if data.get("patient"):
                st.session_state.patient = data.get("patient")

# Display all messages so far
for msg in st.session_state.chat:
    if msg["from"] == "receptionist":
        st.info("Receptionist: " + msg["text"])
    else:
        st.success("Clinical: " + msg["text"])

# ------------------------------------------------------------
# Clinical Agent Section
# ------------------------------------------------------------
st.markdown("---")
st.subheader("Clinical Agent")
st.write("Ask follow-up medical questions (non-emergency).")

q = st.text_input("Your clinical question:")
if st.button("Ask Clinical Agent"):
    if not st.session_state.patient:
        st.warning("No patient selected. Please identify yourself above first.")
    elif not q:
        st.warning("Please enter a question.")
    else:
        try:
            # Call backend /clinical endpoint
            payload = {"patient_id": st.session_state.patient["patient_id"], "question": q}
            resp = requests.post(f"{BACKEND_URL}/clinical", json=payload, timeout=20)

            if resp.status_code == 200:
                data = resp.json()

                # Add message to session chat
                st.session_state.chat.append({"from": "clinical", "text": data.get("text")})

                # Display retrieved sources
                sources = data.get("sources", [])
                if sources:
                    st.markdown("#### Sources Used")
                    for i, s in enumerate(sources, 1):
                        st.markdown(f"**Reference Chunk {i} (score: {s.get('score', 0):.3f})**")
                        st.write(s.get('snippet', '')[:350] + "...")
            else:
                st.error(f"Clinical agent error: {resp.status_code} {resp.text}")

        except Exception as e:
            st.error(f"Backend request failed: {e}")

# ------------------------------------------------------------
# Disclaimer Footer
# ------------------------------------------------------------
st.markdown("---")
st.caption(
    "Disclaimer: This AI assistant is for educational purposes only. "
    "Always consult a qualified healthcare professional for medical advice."
)
