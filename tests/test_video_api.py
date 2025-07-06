import pytest


@pytest.mark.asyncio
async def test_upload_status_and_delete(client):
	await client.post("/auth/register", json={"login": "video", "password": "password123"})
	login_resp = await client.post("/auth/login", json={"login": "video", "password": "password123"})
	assert login_resp.status_code == 200
	token = login_resp.json()["access_token"]
	headers = {"Authorization": f"Bearer {token}"}

	data = {"name": "sample", "description": "desc"}
	files = {"file": ("sample.mp4", b"dummy", "video/mp4")}
	resp = await client.post("/video/upload", data=data, files=files, headers=headers)
	assert resp.status_code == 200
	body = resp.json()
	assert body["status"] == "accepted"
	video_id = body["id"]

	status_resp = await client.get(f"/video/{video_id}/status")
	assert status_resp.status_code == 200
	assert status_resp.json()["status"] == "accepted"

	del_resp = await client.delete(f"/video/{video_id}", headers=headers)
	assert del_resp.status_code == 204

	status_after_del = await client.get(f"/video/{video_id}/status")
	assert status_after_del.status_code == 404
