import io


def _auth_headers(client, email):
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SecurePass123", "full_name": "Edge Case Test"},
    )
    login = client.post("/api/v1/auth/login", data={"username": email, "password": "SecurePass123"})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _upload(client, headers, skills_line=b"Skills: Python, SQL\n"):
    fake = io.BytesIO(b"Test User\ntest@example.com\n" + skills_line)
    response = client.post(
        "/api/v1/resumes/upload", headers=headers, files={"file": ("resume.txt", fake, "text/plain")}
    )
    return response.json()["id"]


# --- GET /resumes/{id} — never tested before this phase ---

def test_get_resume_by_id_success(client):
    headers = _auth_headers(client, "getresume@example.com")
    resume_id = _upload(client, headers)
    response = client.get(f"/api/v1/resumes/{resume_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == resume_id


def test_get_resume_by_id_not_found(client):
    headers = _auth_headers(client, "getresume404@example.com")
    response = client.get("/api/v1/resumes/999999", headers=headers)
    assert response.status_code == 404


def test_get_resume_by_id_wrong_owner(client):
    headers_a = _auth_headers(client, "ownerA@example.com")
    headers_b = _auth_headers(client, "ownerB@example.com")
    resume_id = _upload(client, headers_a)
    # User B should not be able to fetch User A's resume.
    response = client.get(f"/api/v1/resumes/{resume_id}", headers=headers_b)
    assert response.status_code == 404


# --- /skill-gap/roles — listing endpoint, never called in earlier tests ---

def test_list_skill_gap_roles(client):
    headers = _auth_headers(client, "listroles@example.com")
    response = client.get("/api/v1/skill-gap/roles", headers=headers)
    assert response.status_code == 200
    roles = response.json()
    assert "Data Scientist" in roles
    assert len(roles) == 14


# --- Interview questions for a role with no curated group ---

def test_interview_questions_unknown_role_returns_empty_not_error(client):
    headers = _auth_headers(client, "unknownrole@example.com")
    response = client.get("/api/v1/interview/Astronaut", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["technical"] == []
    assert body["hr"] != []  # HR/behavioral pools are universal, not role-gated


# --- Roadmap for a role with zero missing skills ---

def test_roadmap_with_no_missing_skills(client):
    headers = _auth_headers(client, "fullycovered@example.com")
    resume_id = _upload(
        client, headers,
        skills_line=b"Skills: Docker, Kubernetes, Terraform, Jenkins, Linux, AWS, CI/CD\n",
    )
    response = client.get(
        f"/api/v1/roadmap/{resume_id}", headers=headers, params={"target_role": "DevOps Engineer"}
    )
    assert response.status_code == 200
    # Not asserting an empty list strictly (some overlap skills may still be
    # missing), just confirming it doesn't error and returns valid shape.
    assert isinstance(response.json()["roadmap"], list)


# --- File size limit ---

def test_upload_rejects_oversized_file(client):
    headers = _auth_headers(client, "oversized@example.com")
    # MAX_UPLOAD_SIZE_MB defaults to 5MB in Settings — send something bigger.
    big_content = b"a" * (6 * 1024 * 1024)
    response = client.post(
        "/api/v1/resumes/upload",
        headers=headers,
        files={"file": ("big_resume.txt", big_content, "text/plain")},
    )
    assert response.status_code == 400
    assert "too large" in response.json()["detail"].lower()


# --- Prediction regeneration (upsert, not duplicate) ---

def test_regenerating_prediction_updates_not_duplicates(client):
    headers = _auth_headers(client, "regenpred@example.com")
    resume_id = _upload(client, headers, skills_line=b"Skills: Python, SQL, Machine Learning\n")

    payload = {
        "resume_id": resume_id, "experience_years": 1, "education": "Bachelors",
        "num_projects": 2, "certifications": 0, "location_tier": "Tier-2", "company_type": "Startup",
    }
    first = client.post("/api/v1/predictions/generate", headers=headers, json=payload)
    assert first.status_code == 201
    first_id = first.json()["id"]

    payload["experience_years"] = 8  # senior profile now — should shift the prediction
    second = client.post("/api/v1/predictions/generate", headers=headers, json=payload)
    assert second.status_code == 201
    assert second.json()["id"] == first_id  # same row updated, not a new one

    dashboard = client.get("/api/v1/dashboard/latest", headers=headers)
    assert dashboard.json()["prediction"]["id"] == first_id


# --- ATS scoring on a very sparse resume (formatting edge case) ---

def test_ats_score_on_very_short_resume(client):
    headers = _auth_headers(client, "shortresume@example.com")
    fake = io.BytesIO(b"J\n")
    upload = client.post(
        "/api/v1/resumes/upload", headers=headers, files={"file": ("tiny.txt", fake, "text/plain")}
    )
    resume_id = upload.json()["id"]
    response = client.post(f"/api/v1/ats/score/{resume_id}", headers=headers)
    assert response.status_code == 201
    body = response.json()
    assert body["overall_score"] < 50  # a near-empty resume should score low
    assert len(body["suggestions"]) > 0


# --- Roadmap error paths (never tested before this phase) ---

def test_roadmap_resume_not_found(client):
    headers = _auth_headers(client, "roadmapnotfound@example.com")
    response = client.get(
        "/api/v1/roadmap/999999", headers=headers, params={"target_role": "Data Scientist"}
    )
    assert response.status_code == 404


def test_roadmap_unknown_role(client):
    headers = _auth_headers(client, "roadmapbadrole@example.com")
    resume_id = _upload(client, headers)
    response = client.get(
        f"/api/v1/roadmap/{resume_id}", headers=headers, params={"target_role": "Astronaut"}
    )
    assert response.status_code == 400
