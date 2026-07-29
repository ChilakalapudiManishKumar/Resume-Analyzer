import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from components import api_client, charts  # noqa: E402
from components.cards import metric_card  # noqa: E402

st.set_page_config(page_title="Salary Insights", page_icon="💰", layout="wide")

if not api_client.require_login():
    st.stop()

st.title("💰 Salary Insights")

response = api_client.get_dashboard()
if response.status_code == 404:
    st.info("Upload a resume first from the **Resume Upload** page.")
    st.stop()
elif response.status_code != 200:
    st.error("Couldn't load salary data.")
    st.stop()

data = response.json()
prediction = data.get("prediction")

if not prediction:
    st.warning("No prediction yet — go to **Resume Upload** and click 'Generate Prediction + ATS Score'.")
    st.stop()

col1, col2, col3 = st.columns(3)
with col1:
    metric_card("Minimum", f"{prediction['salary_min']:.1f} LPA")
with col2:
    metric_card("Average (best estimate)", f"{prediction['salary_avg']:.1f} LPA")
with col3:
    metric_card("Maximum", f"{prediction['salary_max']:.1f} LPA")

st.plotly_chart(
    charts.salary_range_chart(prediction["salary_min"], prediction["salary_avg"], prediction["salary_max"]),
    use_container_width=True,
)

st.info(
    "This estimate is based on your skills, experience, education, project count, "
    "certifications, location tier, and target company type — trained on a model with "
    "an R² of 0.92 (typically within ~1-1.5 LPA of actual on held-out data)."
)
