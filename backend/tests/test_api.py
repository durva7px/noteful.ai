from fastapi.testclient import TestClient

from app.main import app


def test_health_reports_missing_keys():
    with TestClient(app) as client:
        body = client.get("/api/health").json()
    assert body["ok"] is True
    assert body["pinecone_configured"] is False


def test_upload_list_delete(sample_files):
    with TestClient(app) as client:
        with open(sample_files["pdf"], "rb") as f:
            res = client.post("/api/documents", files={"files": ("lecture.pdf", f, "application/pdf")})
        assert res.status_code == 202
        doc_id = res.json()[0]["id"]

        # TestClient runs the background task inline; without a Pinecone key it must fail clearly.
        listed = {d["id"]: d for d in client.get("/api/documents").json()}
        assert listed[doc_id]["status"] == "failed"
        assert "PINECONE_API_KEY" in listed[doc_id]["error"]

        assert client.delete(f"/api/documents/{doc_id}").status_code == 204
        assert doc_id not in {d["id"] for d in client.get("/api/documents").json()}


def test_rejects_unsupported_type():
    with TestClient(app) as client:
        res = client.post("/api/documents", files={"files": ("deck.ppt", b"data", "application/octet-stream")})
    assert res.status_code == 400
    assert "unsupported" in res.json()["detail"]


def test_chat_without_key_streams_error():
    with TestClient(app) as client:
        res = client.post("/api/chat", json={"question": "What is photosynthesis?"})
    assert "event: error" in res.text
    assert "PINECONE_API_KEY" in res.text
