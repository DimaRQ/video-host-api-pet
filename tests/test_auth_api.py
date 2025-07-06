import pytest


@pytest.mark.asyncio
async def test_register_and_duplicate(client):
    data = {"login": "user1", "password": "password123"}
    r = await client.post("/auth/register", json=data)
    assert r.status_code == 200
    body = r.json()
    assert body["login"] == data["login"]
    assert "id" in body
    assert "created_at" in body

    r = await client.post("/auth/register", json=data)
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_login_success(client):
    await client.post(
        "/auth/register", json={"login": "user2", "password": "password123"}
    )
    r = await client.post(
        "/auth/login", json={"login": "user2", "password": "password123"}
    )
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post(
        "/auth/register", json={"login": "user3", "password": "password123"}
    )
    r = await client.post("/auth/login", json={"login": "user3", "password": "wrong"})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_login_wrong_login(client):
    await client.post(
        "/auth/register", json={"login": "user4", "password": "password123"}
    )
    r = await client.post(
        "/auth/login", json={"login": "wronglogin", "password": "password123"}
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_login_nonexistent_user(client):
    r = await client.post(
        "/auth/login", json={"login": "nouser", "password": "password123"}
    )
    assert r.status_code == 404
