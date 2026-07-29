import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from components import api_client  # noqa: E402

st.set_page_config(page_title="Learning Roadmap", page_icon="🗺️", layout="wide")

if not api_client.require_login():
    st.stop()

st.title("🗺️ Learning Roadmap")

if not st.session_state.get("resume_id"):
    st.info("Upload a resume first from the **Resume Upload** page.")
    st.stop()

roles_response = api_client.list_roles()
roles = roles_response.json() if roles_response.status_code == 200 else []
target_role = st.selectbox("Target role", roles)

if target_role and st.button("Build Roadmap", type="primary"):
    response = api_client.get_roadmap(st.session_state.resume_id, target_role)
    if response.status_code == 200:
        st.session_state.last_roadmap = response.json()
    else:
        st.error(response.json().get("detail", "Couldn't build roadmap."))

roadmap = st.session_state.get("last_roadmap")
if roadmap and roadmap["target_role"] == target_role:
    if not roadmap["roadmap"]:
        st.success("No missing skills for this role — you're fully covered!")
    for item in roadmap["roadmap"]:
        with st.expander(f"📘 {item['skill'].title()}  ·  {item['difficulty']}  ·  {item['estimated_time']}"):
            st.write(item["description"])
            st.write(f"**Why it matters:** {item['importance']}")

            col1, col2 = st.columns(2)
            with col1:
                st.write("**Free resources:**")
                for r in item["free_resources"]:
                    st.write(f"- {r}")
                st.write("**YouTube:**")
                for r in item["youtube"]:
                    st.write(f"- {r}")
            with col2:
                st.write("**Paid resources:**")
                for r in item["paid_resources"]:
                    st.write(f"- {r}")
                st.write("**Practice sites:**")
                for r in item["practice_sites"]:
                    st.write(f"- {r}")
