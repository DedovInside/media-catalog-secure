from fastapi.testclient import TestClient


def test_not_found_item(client: TestClient):
    r = client.get("/items/999")
    assert r.status_code == 404
    body = r.json()
    # RFC 7807 структура
    assert "type" in body
    assert "status" in body
    assert "detail" in body
    assert "correlation_id" in body
    assert body["detail"] == "The requested resource could not be found"


def test_validation_error(client: TestClient):
    """Test validation error with correct Content-Type"""
    # Добавляем Content-Type header
    r = client.post(
        "/items",
        json={"name": ""},  # Используем json parameter
        headers={"Content-Type": "application/json"},
    )

    # Теперь дойдёт до validation
    assert r.status_code == 422
    body = r.json()
    # RFC 7807 структура
    assert "type" in body
    assert "status" in body
    assert "detail" in body
    assert "correlation_id" in body


def test_content_type_validation_error(client: TestClient):
    """NEW: Test Content-Type middleware blocking"""
    # Тест специально для Content-Type middleware
    r = client.post("/items", data='{"name": "test"}')  # БЕЗ Content-Type
    assert r.status_code == 415
    body = r.json()

    # RFC 7807 структура
    assert "type" in body
    assert "status" in body
    assert "detail" in body
    assert "correlation_id" in body
    assert "Content-Type must be one of: application/json" in body["detail"]
