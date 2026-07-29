import io


def _auth_headers(client, email="phase4user@example.com"):
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SecurePass123", "full_name": "Phase4 User"},
    )
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "SecurePass123"},
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _upload_ml_resume(client, headers):
    fake_resume = io.BytesIO(
        b"Jane Doe\njane.doe@example.com\n9876543210\n"
        b"Skills: Python, Scikit-learn, TensorFlow, Machine Learning, Deep Learning, SQL\n"
        b"Education: B.Tech Computer Science, ABC University\n"
        b"Projects: Built and deployed a churn-prediction model, led a small analytics team.\n"
    )
    response = client.post(
        "/api/v1/resumes/upload",
        headers=headers,
        files={"file": ("resume.txt", fake_resume, "text/plain")},
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_generate_prediction_end_to_end(client):
    headers = _auth_headers(client)
    resume_id = _upload_ml_resume(client, headers)

    response = client.post(
        "/api/v1/predictions/generate",
        headers=headers,
        json={
            "resume_id": resume_id,
            "experience_years": 2.5,
            "education": "Masters",
            "num_projects": 5,
            "certifications": 1,
            "location_tier": "Tier-1",
            "company_type": "Product-based",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["predicted_role"] in {"Machine Learning Engineer", "Data Scientist", "AI Engineer"}
    assert 0 <= body["confidence"] <= 1
    assert body["salary_min"] <= body["salary_avg"] <= body["salary_max"]


def test_generate_prediction_rejects_missing_resume(client):
    headers = _auth_headers(client, email="noresume@example.com")
    response = client.post(
        "/api/v1/predictions/generate",
        headers=headers,
        json={
            "resume_id": 9999,
            "experience_years": 1,
            "education": "Bachelors",
            "num_projects": 1,
            "certifications": 0,
            "location_tier": "Tier-2",
            "company_type": "Startup",
        },
    )
    assert response.status_code == 404


def test_ats_score_end_to_end(client):
    headers = _auth_headers(client, email="atsuser@example.com")
    resume_id = _upload_ml_resume(client, headers)

    response = client.post(f"/api/v1/ats/score/{resume_id}", headers=headers)
    assert response.status_code == 201
    body = response.json()
    assert 0 <= body["overall_score"] <= 100
    assert set(body["category_scores"].keys()) == {
        "keywords", "sections", "action_verbs", "formatting", "contact_info"
    }


def test_skill_gap_end_to_end(client):
    headers = _auth_headers(client, email="skillgapuser@example.com")
    resume_id = _upload_ml_resume(client, headers)

    response = client.get(
        f"/api/v1/skill-gap/{resume_id}",
        headers=headers,
        params={"target_role": "Machine Learning Engineer"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["target_role"] == "Machine Learning Engineer"
    assert "python" in body["matching_skills"]
    assert isinstance(body["missing_skills"], list)


def test_skill_gap_rejects_unknown_role(client):
    headers = _auth_headers(client, email="badrole@example.com")
    resume_id = _upload_ml_resume(client, headers)

    response = client.get(
        f"/api/v1/skill-gap/{resume_id}",
        headers=headers,
        params={"target_role": "Astronaut"},
    )
    assert response.status_code == 400


def test_roadmap_end_to_end(client):
    headers = _auth_headers(client, email="roadmapuser@example.com")
    resume_id = _upload_ml_resume(client, headers)

    response = client.get(
        f"/api/v1/roadmap/{resume_id}",
        headers=headers,
        params={"target_role": "Cloud Engineer"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["target_role"] == "Cloud Engineer"
    for item in body["roadmap"]:
        assert item["skill"]
        assert item["estimated_time"]


def test_interview_questions_end_to_end(client):
    headers = _auth_headers(client, email="interviewuser@example.com")
    response = client.get("/api/v1/interview/Data Scientist", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body["technical"]) > 0
    assert len(body["hr"]) > 0
    assert len(body["behavioral"]) > 0


def test_dashboard_latest_end_to_end(client):
    headers = _auth_headers(client, email="dashboarduser@example.com")
    resume_id = _upload_ml_resume(client, headers)
    client.post(f"/api/v1/ats/score/{resume_id}", headers=headers)
    client.post(
        "/api/v1/predictions/generate",
        headers=headers,
        json={
            "resume_id": resume_id,
            "experience_years": 3,
            "education": "Bachelors",
            "num_projects": 4,
            "certifications": 2,
            "location_tier": "Tier-1",
            "company_type": "Startup",
        },
    )

    response = client.get("/api/v1/dashboard/latest", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["resume_id"] == resume_id
    assert body["ats_score"] is not None
    assert body["prediction"] is not None


def test_dashboard_no_resume_yet(client):
    headers = _auth_headers(client, email="emptydashboard@example.com")
    response = client.get("/api/v1/dashboard/latest", headers=headers)
    assert response.status_code == 404
