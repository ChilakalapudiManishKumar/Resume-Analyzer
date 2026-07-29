import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from components import api_client, charts  # noqa: E402
from components.cards import metric_card  # noqa: E402

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

if not api_client.require_login():
    st.stop()

st.title("📊 Career Dashboard")

response = api_client.get_dashboard()

if response.status_code == 404:
    st.info("No resume uploaded yet — head to **Resume Upload** to get started.")
    st.stop()
elif response.status_code != 200:
    st.error("Couldn't load your dashboard. Try again in a moment.")
    st.stop()

data = response.json()
ats = data.get("ats_score")
prediction = data.get("prediction")

st.caption(f"Showing results for: **{data['original_filename']}**")

col1, col2, col3 = st.columns(3)
with col1:
    metric_card("ATS Score", f"{ats['overall_score']}/100" if ats else "—",
                "Run ATS scoring from Resume Upload" if not ats else "")
with col2:
    metric_card("Predicted Role", prediction["predicted_role"] if prediction else "—",
                f"{prediction['confidence']:.0%} confidence" if prediction else "Generate a prediction first")
with col3:
    metric_card("Salary (Avg)", f"{prediction['salary_avg']:.1f} LPA" if prediction else "—",
                f"Range: {prediction['salary_min']:.1f} - {prediction['salary_max']:.1f} LPA" if prediction else "")

st.divider()

if prediction:
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(charts.role_probability_bar(prediction["role_probabilities"]), use_container_width=True)
    with col2:
        st.plotly_chart(
            charts.salary_range_chart(prediction["salary_min"], prediction["salary_avg"], prediction["salary_max"]),
            use_container_width=True,
        )
else:
    st.warning("No prediction yet — go to **Resume Upload** and click 'Generate Prediction + ATS Score'.")

if ats:
    st.divider()
    max_scores = {"keywords": 30, "sections": 25, "action_verbs": 20, "formatting": 15, "contact_info": 10}
    st.plotly_chart(charts.ats_category_bar(ats["category_scores"], max_scores), use_container_width=True)

    if ats["suggestions"]:
        with st.expander("📋 Improvement suggestions"):
            for s in ats["suggestions"]:
                st.write(f"- {s}")
