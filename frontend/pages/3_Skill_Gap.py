import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from components import api_client, charts  # noqa: E402

st.set_page_config(page_title="Skill Gap", page_icon="🧩", layout="wide")

if not api_client.require_login():
    st.stop()

st.title("🧩 Skill Gap Analysis")

if not st.session_state.get("resume_id"):
    st.info("Upload a resume first from the **Resume Upload** page.")
    st.stop()

roles_response = api_client.list_roles()
roles = roles_response.json() if roles_response.status_code == 200 else []

target_role = st.selectbox("Target role", roles)

if target_role and st.button("Analyze", type="primary"):
    response = api_client.get_skill_gap(st.session_state.resume_id, target_role)
    if response.status_code == 200:
        result = response.json()
        st.session_state.last_skill_gap = result
    else:
        st.error(response.json().get("detail", "Couldn't analyze skill gap."))

result = st.session_state.get("last_skill_gap")
if result and result["target_role"] == target_role:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.plotly_chart(
            charts.skill_gap_donut(len(result["matching_skills"]), len(result["missing_skills"])),
            use_container_width=True,
        )
        st.metric("Readiness", f"{result['readiness_percent']}%")

    with col2:
        st.subheader("✅ Matching skills")
        st.write(", ".join(result["matching_skills"]) or "None yet")

        st.subheader("❌ Missing skills")
        st.write(", ".join(result["missing_skills"]) or "None — you're fully covered!")

        if result["missing_skills"]:
            st.subheader("📚 Suggested learning order")
            for i, skill in enumerate(result["learning_order"], start=1):
                st.write(f"{i}. {skill}")
            st.caption("See the **Roadmap** page for detailed resources on each of these.")
