import pytest
from app.auth.service import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_access_token,
    verify_password,
    verify_refresh_token,
)


class TestPasswordHashing:
    def test_hash_and_verify(self):
        password = "securepassword123"
        hashed = hash_password(password)
        assert hashed != password
        assert verify_password(password, hashed)

    def test_wrong_password_fails(self):
        hashed = hash_password("correct")
        assert not verify_password("wrong", hashed)


class TestTokens:
    def test_access_token_roundtrip(self):
        user_id = "test-user-id-123"
        token = create_access_token(user_id)
        assert verify_access_token(token) == user_id

    def test_refresh_token_roundtrip(self):
        user_id = "test-user-id-123"
        token = create_refresh_token(user_id)
        assert verify_refresh_token(token) == user_id

    def test_access_token_not_valid_as_refresh(self):
        token = create_access_token("user-123")
        assert verify_refresh_token(token) is None

    def test_refresh_token_not_valid_as_access(self):
        token = create_refresh_token("user-123")
        assert verify_access_token(token) is None

    def test_invalid_token_returns_none(self):
        assert verify_access_token("garbage-token") is None
        assert verify_refresh_token("garbage-token") is None


class TestAuthEndpoints:
    def test_register_success(self, client):
        response = client.post(
            "/api/auth/register",
            json={"email": "new@mirror.app", "name": "New User", "password": "password123"},
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_register_duplicate_email(self, client, test_user):
        response = client.post(
            "/api/auth/register",
            json={"email": test_user.email, "name": "Duplicate", "password": "password123"},
        )
        assert response.status_code == 409

    def test_login_success(self, client, test_user):
        response = client.post(
            "/api/auth/login",
            json={"email": "test@mirror.app", "password": "testpassword123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_login_wrong_password(self, client, test_user):
        response = client.post(
            "/api/auth/login",
            json={"email": "test@mirror.app", "password": "wrongpassword"},
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        response = client.post(
            "/api/auth/login",
            json={"email": "nobody@mirror.app", "password": "password"},
        )
        assert response.status_code == 401

    def test_refresh_token(self, client, test_user):
        # First login to get tokens
        login_resp = client.post(
            "/api/auth/login",
            json={"email": "test@mirror.app", "password": "testpassword123"},
        )
        refresh_token = login_resp.json()["refresh_token"]

        # Use refresh token
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_refresh_with_invalid_token(self, client):
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": "invalid-token"},
        )
        assert response.status_code == 401
