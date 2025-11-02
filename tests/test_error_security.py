"""Security tests for error responses (ADR-001)"""

from fastapi.testclient import TestClient


class TestErrorSecurity:
    """Test error response security (NFR-13) with RFC 7807 compliance"""

    def test_not_found_error_rfc7807_format(self, client: TestClient):
        """Test 404 errors follow RFC 7807 format"""
        response = client.get("/media/999")
        assert response.status_code == 404

        error_data = response.json()

        # RFC 7807 required fields
        assert "type" in error_data
        assert "title" in error_data
        assert "status" in error_data
        assert "detail" in error_data
        assert "correlation_id" in error_data

        # Correct status
        assert error_data["status"] == 404
        assert error_data["title"] == "Not Found"

    def test_not_found_error_no_sensitive_disclosure(self, client: TestClient):
        """Test 404 errors don't reveal specific IDs or user data"""
        response = client.get("/media/999")
        assert response.status_code == 404

        error_data = response.json()

        # Safe generic message
        assert error_data["detail"] == "The requested resource could not be found"

        # No sensitive data disclosure
        assert "999" not in error_data["detail"]
        assert "id" not in error_data["detail"].lower()
        assert "user" not in error_data["detail"].lower()

    def test_duplicate_error_no_data_disclosure(self, client: TestClient):
        """Test duplicate errors don't reveal existing data"""
        # Create media
        media_data = {"title": "Secret Movie Title", "kind": "movie", "year": 2024}
        client.post("/media", json=media_data)

        # Try to create duplicate
        response = client.post("/media", json=media_data)
        assert response.status_code == 409

        error_data = response.json()

        # RFC 7807 format
        assert error_data["status"] == 409
        assert "correlation_id" in error_data

        # Safe generic message
        assert error_data["detail"] == "A resource with these properties already exists"

        # No data disclosure
        assert "Secret Movie Title" not in error_data["detail"]
        assert "2024" not in error_data["detail"]

    def test_validation_error_rfc7807_format(self, client: TestClient):
        """Test validation errors follow RFC 7807 format with safe details"""
        response = client.post("/media", json={"title": "", "kind": "movie", "year": 2024})
        assert response.status_code == 422

        # This will be handled by FastAPI's validation, but should be safe
        error_data = response.json()

        # Check it doesn't leak internal schema details
        error_text = str(error_data).lower()
        assert "pydantic" not in error_text
        assert "field required" not in error_text

    def test_error_correlation_id_format(self, client: TestClient):
        """Test correlation_id is proper UUID format"""
        response = client.get("/media/999")
        assert response.status_code == 404

        error_data = response.json()
        correlation_id = error_data["correlation_id"]

        # Should be UUID format
        assert len(correlation_id) == 36  # UUID length
        assert correlation_id.count("-") == 4  # UUID dashes

    # def test_large_payload_error_rfc7807(self):
    #    """Test large payload rejection with RFC 7807 format"""
    # This test will work when we implement request size limiting
    #    large_title = "x" * 1000  # Very long title
    #    media_data = {
    #        "title": large_title,
    #        "kind": "movie",
    #        "year": 2024,
    #        "description": "x" * 5000,  # Large description
    #    }

    # response = client.post("/media", json=media_data)
    # Currently this will pass validation, but when we add size limits:
    # assert response.status_code == 413
    # error_data = response.json()
    # assert error_data["detail"] == "Request payload exceeds maximum allowed size"


class TestErrorSecurityNegative:
    """Negative tests - what should NOT happen"""

    def test_no_stack_traces_in_errors(self, client: TestClient):
        """Negative test: no internal stack traces in any error"""
        response = client.get("/media/999")
        error_data = response.json()
        error_text = str(error_data).lower()

        # These should NOT appear
        assert "traceback" not in error_text
        assert 'file "' not in error_text
        assert "line " not in error_text
        assert "fastapi" not in error_text
        assert "pydantic" not in error_text
        assert "/app/" not in error_text  # No file paths

    def test_no_internal_details_in_any_error(self, client: TestClient):
        """Negative test: no internal implementation details"""
        # Test various error scenarios
        error_responses = [
            client.get("/media/99999"),  # Not found
            client.delete("/media/99999"),  # Not found
        ]

        for response in error_responses:
            error_data = response.json()
            error_text = str(error_data).lower()

            # No internal details should leak
            assert "database" not in error_text
            assert "sql" not in error_text
            assert "memory" not in error_text
            assert "_media_db" not in error_text
            assert "crud" not in error_text

    def test_consistent_error_structure(self, client: TestClient):
        """Test all errors have consistent RFC 7807 structure"""
        error_responses = [
            client.get("/media/999"),  # 404
            client.delete("/media/999"),  # 404
        ]

        for response in error_responses:
            error_data = response.json()

            # All should have RFC 7807 structure
            required_fields = ["type", "title", "status", "detail", "correlation_id"]
            for field in required_fields:
                assert field in error_data, f"Missing field: {field}"

            # Status should match HTTP status
            assert error_data["status"] == response.status_code
