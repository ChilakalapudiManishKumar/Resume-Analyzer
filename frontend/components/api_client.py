"""
Thin wrapper around the FastAPI backend — every page imports from here
instead of calling `requests` directly, so the auth header logic and
base URL live in exactly one place.
"""
import os

import requests
import streamlit as st

API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000/api/v1")


def _auth_headers() -> dict:
    token = st.session_state.get("access_token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def register(email: str, password: str, full_name: str) -> requests.Response:
    return requests.post(
        f"{API_BASE_URL}/auth/register",
        json={"email": email, "password": password, "full_name": full_name},
        timeout=10,
    )


def login(email: str, password: str) -> requests.Response:
    return requests.post(
        f"{API_BASE_URL}/auth/login",
        data={"username": email, "password": password},
        timeout=10,
    )


def get_current_user() -> requests.Response:
    return requests.get(f"{API_BASE_URL}/users/me", headers=_auth_headers(), timeout=10)


def upload_resume(file_bytes: bytes, filename: str) -> requests.Response:
    return requests.post(
        f"{API_BASE_URL}/resumes/upload",
        headers=_auth_headers(),
        files={"file": (filename, file_bytes)},
        timeout=30,
    )


def generate_prediction(payload: dict) -> requests.Response:
    return requests.post(
        f"{API_BASE_URL}/predictions/generate",
        headers=_auth_headers(),
        json=payload,
        timeout=15,
    )


def get_ats_score(resume_id: int) -> requests.Response:
    return requests.post(f"{API_BASE_URL}/ats/score/{resume_id}", headers=_auth_headers(), timeout=15)


def list_roles() -> requests.Response:
    return requests.get(f"{API_BASE_URL}/skill-gap/roles", headers=_auth_headers(), timeout=10)


def get_skill_gap(resume_id: int, target_role: str) -> requests.Response:
    return requests.get(
        f"{API_BASE_URL}/skill-gap/{resume_id}",
        headers=_auth_headers(),
        params={"target_role": target_role},
        timeout=10,
    )


def get_roadmap(resume_id: int, target_role: str) -> requests.Response:
    return requests.get(
        f"{API_BASE_URL}/roadmap/{resume_id}",
        headers=_auth_headers(),
        params={"target_role": target_role},
        timeout=10,
    )


def get_interview_questions(role: str) -> requests.Response:
    return requests.get(f"{API_BASE_URL}/interview/{role}", headers=_auth_headers(), timeout=10)


def get_dashboard() -> requests.Response:
    return requests.get(f"{API_BASE_URL}/dashboard/latest", headers=_auth_headers(), timeout=10)


def is_logged_in() -> bool:
    return bool(st.session_state.get("access_token"))


def require_login() -> bool:
    """Call at the top of every page. Returns False (and shows a message)
    if the user isn't logged in, so the page can `st.stop()`."""
    if not is_logged_in():
        st.warning("Please log in from the main page first.")
        return False
    return True
