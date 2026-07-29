def test_register_new_user(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "SecurePass123", "full_name": "Test User"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "test@example.com"
    assert "hashed_password" not in body  # must never leak into the response


def test_register_duplicate_email_rejected(client):
    payload = {"email": "dup@example.com", "password": "SecurePass123", "full_name": "Dup User"}
    client.post("/api/v1/auth/register", json=payload)
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409


def test_login_success_returns_token(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "login@example.com", "password": "SecurePass123", "full_name": "Login User"},
    )
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "login@example.com", "password": "SecurePass123"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_wrong_password_rejected(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "wrongpw@example.com", "password": "SecurePass123", "full_name": "User"},
    )
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "wrongpw@example.com", "password": "WrongPassword"},
    )
    assert response.status_code == 401


def test_protected_route_requires_token(client):
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401


def test_protected_route_with_valid_token(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "me@example.com", "password": "SecurePass123", "full_name": "Me User"},
    )
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "me@example.com", "password": "SecurePass123"},
    )
    token = login_response.json()["access_token"]

    response = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"
