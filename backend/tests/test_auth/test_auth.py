import pytest
from app.auth.service import (
    create_access_token, create_refresh_token, hash_password,
    verify_access_token, verify_password, verify_refresh_token,
)


class TestPasswordHashing:
    def test_hash_and_verify(self):
        hashed = hash_password("securepassword123")
        assert verify_password("securepassword123", hashed)

    def test_wrong_password_fails(self):
        hashed = hash_password("correct")
        assert not verify_password("wrong", hashed)


class TestTokens:
    def test_access_token_roundtrip(self):
        token = create_access_token("test-id")
        assert verify_access_token(token) == "test-id"

    def test_refresh_token_roundtrip(self):
        token = create_refresh_token("test-id")
        assert verify_refresh_token(token) == "test-id"

    def test_access_not_valid_as_refresh(self):
        assert verify_refresh_token(create_access_token("x")) is None

    def test_refresh_not_valid_as_access(self):
        assert verify_access_token(create_refresh_token("x")) is None

    def test_invalid_token(self):
        assert verify_access_token("garbage") is None


class TestAuthEndpoints:
    @pytest.mark.asyncio
    async def test_register_success(self, client):
        resp = await client.post("/api/auth/register", json={
            "email": "new@mirror.app", "name": "New", "password": "pass123"
        })
        assert resp.status_code == 201
        assert "access_token" in resp.json()

    @pytest.mark.asyncio
    async def test_register_duplicate(self, client, test_user):
        resp = await client.post("/api/auth/register", json={
            "email": "test@mirror.app", "name": "Dup", "password": "pass123"
        })
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_login_success(self, client, test_user):
        resp = await client.post("/api/auth/login", json={
            "email": "test@mirror.app", "password": "testpassword123"
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client, test_user):
        resp = await client.post("/api/auth/login", json={
            "email": "test@mirror.app", "password": "wrong"
        })
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent(self, client):
        resp = await client.post("/api/auth/login", json={
            "email": "nobody@mirror.app", "password": "pass"
        })
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_token(self, client, test_user):
        login = await client.post("/api/auth/login", json={
            "email": "test@mirror.app", "password": "testpassword123"
        })
        refresh = login.json()["refresh_token"]
        resp = await client.post("/api/auth/refresh", json={"refresh_token": refresh})
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_refresh_invalid(self, client):
        resp = await client.post("/api/auth/refresh", json={"refresh_token": "bad"})
        assert resp.status_code == 401
