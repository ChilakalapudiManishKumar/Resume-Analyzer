import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from components import api_client  # noqa: E402

st.set_page_config(page_title="Interview Prep", page_icon="🎤", layout="wide")

if not api_client.require_login():
    st.stop()

st.title("🎤 Interview Preparation")

roles_response = api_client.list_roles()
roles = roles_response.json() if roles_response.status_code == 200 else []

default_index = 0
last_prediction = st.session_state.get("last_prediction")
if last_prediction and last_prediction["predicted_role"] in roles:
    default_index = roles.index(last_prediction["predicted_role"])

role = st.selectbox("Role", roles, index=default_index)

if role and st.button("Load Questions", type="primary"):
    response = api_client.get_interview_questions(role)
    if response.status_code == 200:
        st.session_state.last_interview = response.json()
    else:
        st.error("Couldn't load questions.")

questions = st.session_state.get("last_interview")
if questions and questions["role"] == role:
    tabs = st.tabs(["Technical", "Coding", "HR", "Behavioral", "Scenario", "System Design"])
    categories = ["technical", "coding", "hr", "behavioral", "scenario", "system_design"]

    for tab, category in zip(tabs, categories):
        with tab:
            items = questions.get(category, [])
            if not items:
                st.caption("No questions in this category for this role.")
            for qa in items:
                with st.expander(qa["question"]):
                    st.write(qa["answer"])
