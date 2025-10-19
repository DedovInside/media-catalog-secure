from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_not_found_item():
    r = client.get("/items/999")
    assert r.status_code == 404
    body = r.json()
    # RFC 7807 структура
    assert "type" in body
    assert "status" in body
    assert "detail" in body
    assert "correlation_id" in body
    assert body["detail"] == "The requested resource could not be found"


def test_validation_error():
    r = client.post("/items", params={"name": ""})
    assert r.status_code == 422
    body = r.json()
    # RFC 7807 структура
    assert "type" in body
    assert "status" in body
    assert "detail" in body
    assert "correlation_id" in body
