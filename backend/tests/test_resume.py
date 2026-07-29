import io

from app.services.resume_parser import extract_structured_data


def _auth_headers(client, email="resumeuser@example.com"):
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SecurePass123", "full_name": "Resume User"},
    )
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "SecurePass123"},
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_extract_structured_data_finds_email_phone_skills():
    sample_text = """John Doe
    Email: john.doe@example.com
    Phone: +91 98765 43210

    Skills: Python, SQL, Machine Learning, Docker
    Education: B.Tech in Computer Science, XYZ University
    """
    result = extract_structured_data(sample_text)
    assert result["email"] == "john.doe@example.com"
    assert "python" in result["skills"]
    assert "sql" in result["skills"]
    assert "docker" in result["skills"]
    assert result["name"] == "John Doe"


def test_upload_txt_resume_end_to_end(client):
    headers = _auth_headers(client)
    fake_resume = io.BytesIO(
        b"Jane Smith\njane.smith@example.com\nSkills: Python, FastAPI, PostgreSQL\n"
    )
    response = client.post(
        "/api/v1/resumes/upload",
        headers=headers,
        files={"file": ("resume.txt", fake_resume, "text/plain")},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["original_filename"] == "resume.txt"
    assert "python" in body["extracted_data"]["skills"]


def test_upload_rejects_unsupported_extension(client):
    headers = _auth_headers(client, email="badfile@example.com")
    fake_file = io.BytesIO(b"not a real resume")
    response = client.post(
        "/api/v1/resumes/upload",
        headers=headers,
        files={"file": ("resume.exe", fake_file, "application/octet-stream")},
    )
    assert response.status_code == 400


def test_upload_requires_auth(client):
    fake_resume = io.BytesIO(b"Some Name\nemail@example.com\n")
    response = client.post(
        "/api/v1/resumes/upload",
        files={"file": ("resume.txt", fake_resume, "text/plain")},
    )
    assert response.status_code == 401
