"""
Auth edge cases not covered by the happy-path tests in test_auth.py:
invalid/malformed/tampered tokens, and a token for a user that no longer
exists (e.g. deleted account) — all should be rejected as 401, not crash.
"""
from app.core.security import create_access_token, decode_access_token


def test_decode_invalid_token_returns_none():
    assert decode_access_token("not.a.valid.jwt") is None


def test_decode_tampered_token_returns_none():
    token = create_access_token(subject=1)
    tampered = token[:-2] + "xx"
    assert decode_access_token(tampered) is None


def test_protected_route_rejects_malformed_token(client):
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer not.a.valid.jwt"},
    )
    assert response.status_code == 401


def test_protected_route_rejects_token_for_deleted_user(client):
    # Craft a token for a user id that was never created.
    token = create_access_token(subject=999999)
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401


def test_protected_route_rejects_no_bearer_prefix(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "noprefix@example.com", "password": "SecurePass123", "full_name": "No Prefix"},
    )
    login = client.post(
        "/api/v1/auth/login", data={"username": "noprefix@example.com", "password": "SecurePass123"}
    )
    token = login.json()["access_token"]
    # Missing "Bearer " prefix should be rejected by OAuth2PasswordBearer.
    response = client.get("/api/v1/users/me", headers={"Authorization": token})
    assert response.status_code == 401
