import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from components import api_client  # noqa: E402

st.set_page_config(page_title="Resume Upload", page_icon="📄", layout="wide")

if not api_client.require_login():
    st.stop()

st.title("📄 Resume Upload")
st.caption("Upload a PDF, DOCX, or TXT resume. We'll extract your details, then you can generate your role & salary prediction.")

uploaded_file = st.file_uploader("Choose your resume", type=["pdf", "docx", "txt"])

if uploaded_file is not None and st.button("Upload & Parse", type="primary"):
    response = api_client.upload_resume(uploaded_file.getvalue(), uploaded_file.name)
    if response.status_code == 201:
        resume = response.json()
        st.session_state.resume_id = resume["id"]
        st.session_state.extracted_data = resume["extracted_data"]
        st.success(f"Uploaded '{resume['original_filename']}' successfully.")
    else:
        st.error(response.json().get("detail", "Upload failed."))

if st.session_state.get("resume_id"):
    st.divider()
    st.subheader("Extracted details (review before continuing)")
    data = st.session_state.extracted_data
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Name (auto-detected)", value=data.get("name") or "Not detected", disabled=True)
        st.text_input("Email (auto-detected)", value=data.get("email") or "Not detected", disabled=True)
    with col2:
        st.text_input("Phone (auto-detected)", value=data.get("phone") or "Not detected", disabled=True)
        st.write("**Skills detected:**", ", ".join(data.get("skills", [])) or "None detected")

    st.divider()
    st.subheader("A few details our parser can't reliably read from a resume")
    st.caption("These feed the role & salary prediction models — please fill them in accurately.")

    with st.form("prediction_inputs"):
        col1, col2, col3 = st.columns(3)
        with col1:
            experience_years = st.number_input("Years of experience", min_value=0.0, max_value=50.0, value=1.0, step=0.5)
            education = st.selectbox("Education level", ["Bachelors", "Masters", "PhD"])
        with col2:
            num_projects = st.number_input("Number of projects", min_value=0, max_value=100, value=3)
            certifications = st.number_input("Number of certifications", min_value=0, max_value=50, value=0)
        with col3:
            location_tier = st.selectbox("Location tier", ["Tier-1", "Tier-2", "Tier-3"],
                                          help="Tier-1: Bangalore/Hyderabad/Pune/Mumbai/Delhi-NCR etc.")
            company_type = st.selectbox("Target company type", ["Startup", "Product-based", "Service-based", "Enterprise"])

        generate = st.form_submit_button("Generate Prediction + ATS Score", type="primary", use_container_width=True)

    if generate:
        payload = {
            "resume_id": st.session_state.resume_id,
            "experience_years": experience_years,
            "education": education,
            "num_projects": num_projects,
            "certifications": certifications,
            "location_tier": location_tier,
            "company_type": company_type,
        }
        pred_response = api_client.generate_prediction(payload)
        ats_response = api_client.get_ats_score(st.session_state.resume_id)

        if pred_response.status_code == 201 and ats_response.status_code == 201:
            st.session_state.last_prediction = pred_response.json()
            st.session_state.last_ats = ats_response.json()
            st.success("Done — head to the Dashboard to see your results.")
            st.balloons()
        else:
            st.error("Something went wrong generating predictions. Check the backend logs.")
