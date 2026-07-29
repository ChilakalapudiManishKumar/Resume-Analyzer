"""
Entrypoint: landing page + login/register. Once logged in, the JWT lives
in st.session_state (shared across all pages/ in this multi-page app) —
each page's api_client call attaches it automatically.
"""
from pathlib import Path

import streamlit as st

from components import api_client

st.set_page_config(
    page_title="AI Career Intelligence Platform",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)


def load_css():
    css_path = Path(__file__).parent / "assets" / "style.css"
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


load_css()

if "access_token" not in st.session_state:
    st.session_state.access_token = None
    st.session_state.user_email = None
    st.session_state.full_name = None


def render_logged_in_home():
    st.markdown(f'<div class="hero-title">Welcome back, {st.session_state.full_name}</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Use the sidebar to navigate: Dashboard, Resume Upload, Skill Gap, Salary Insights, Roadmap, Interview Prep.</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("Log out"):
            for key in ("access_token", "user_email", "full_name"):
                st.session_state[key] = None
            st.rerun()

    st.info("Head to **Resume Upload** first if you haven't uploaded a resume yet, then check the **Dashboard**.")


def render_login_register():
    st.markdown('<div class="hero-title">AI Career Intelligence Platform</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-subtitle">Upload your resume to get an ATS score, predicted role & salary, '
        'a skill-gap analysis, a learning roadmap, and role-specific interview prep — all in one place.</div>',
        unsafe_allow_html=True,
    )

    login_tab, register_tab = st.tabs(["Log in", "Register"])

    with login_tab:
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Log in", use_container_width=True)

        if submitted:
            response = api_client.login(email, password)
            if response.status_code == 200:
                token = response.json()["access_token"]
                st.session_state.access_token = token
                me = api_client.get_current_user()
                if me.status_code == 200:
                    st.session_state.user_email = me.json()["email"]
                    st.session_state.full_name = me.json()["full_name"]
                st.rerun()
            else:
                detail = response.json().get("detail", "Login failed.")
                st.error(detail)

    with register_tab:
        with st.form("register_form"):
            full_name = st.text_input("Full name")
            reg_email = st.text_input("Email", key="reg_email")
            reg_password = st.text_input("Password (min 8 characters)", type="password", key="reg_password")
            reg_submitted = st.form_submit_button("Create account", use_container_width=True)

        if reg_submitted:
            response = api_client.register(reg_email, reg_password, full_name)
            if response.status_code == 201:
                st.success("Account created — now log in from the 'Log in' tab.")
            else:
                detail = response.json().get("detail", "Registration failed.")
                st.error(detail)


if api_client.is_logged_in():
    render_logged_in_home()
else:
    render_login_register()
