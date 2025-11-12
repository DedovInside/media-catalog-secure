class TestXSSProtection:
    """Test XSS attack prevention - comprehensive coverage"""

    def test_xss_payload_stored_as_plain_text(self, client):
        """Test XSS payload is stored and returned as plain text"""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "</title><script>alert('xss')</script>",
            "';DROP TABLE media;--",  # SQL + XSS combo
        ]

        created_ids = []

        for payload in xss_payloads:
            response = client.post("/media", json={"title": payload, "kind": "movie", "year": 2024})

            # Should accept as plain text
            assert response.status_code == 201
            media = response.json()
            assert media["title"] == payload  # Stored as-is (plain text)
            created_ids.append(media["id"])

        # Verify all payloads returned safely
        for i, payload in enumerate(xss_payloads):
            response = client.get(f"/media/{created_ids[i]}")
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/json"

            media = response.json()
            assert media["title"] == payload  # Still plain text in JSON

    def test_no_html_rendering_endpoints(self, client):
        """Verify API only returns JSON (no HTML endpoints)"""
        # Test all endpoints return application/json
        endpoints = [
            ("GET", "/media"),
            ("GET", "/health"),
        ]

        for method, path in endpoints:
            response = client.request(method, path)
            if response.status_code < 400:
                assert "application/json" in response.headers.get("content-type", "")


class TestContentTypeSecurity:
    """Test Content-Type validation (ADR-003)"""

    def test_json_content_type_accepted(self, client):
        """Test application/json is accepted"""
        response = client.post(
            "/media",
            json={"title": "Test Movie", "kind": "movie", "year": 2024},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 201

    def test_html_content_type_rejected(self, client):
        """Test HTML Content-Type is rejected"""
        response = client.post(
            "/media",
            content="<html><body>test</body></html>",
            headers={"Content-Type": "text/html"},
        )
        assert response.status_code == 415
        error = response.json()
        assert "Content-Type must be one of: application/json" in error["detail"]

    def test_xml_content_type_rejected(self, client):
        """Test XML Content-Type is rejected"""
        response = client.post(
            "/media",
            content='<?xml version="1.0"?><media><title>test</title></media>',
            headers={"Content-Type": "application/xml"},
        )
        assert response.status_code == 415

    def test_missing_content_type_rejected(self, client):
        """Test missing Content-Type is rejected"""
        response = client.post("/media", content='{"title": "test", "kind": "movie", "year": 2024}')
        assert response.status_code == 415


class TestXSSNegativeScenarios:
    """Negative tests - what should NOT happen"""

    def test_no_script_execution_in_responses(self, client):
        """Verify script tags in data don't execute"""
        dangerous_titles = [
            "<script>document.location='http://evil.com'</script>",
            "<iframe src='javascript:alert(1)'></iframe>",
            "onmouseover=alert('xss')",
        ]

        for title in dangerous_titles:
            # Create media with dangerous title
            response = client.post("/media", json={"title": title, "kind": "movie", "year": 2024})

            media_id = response.json()["id"]

            # Get media - should return as plain text in JSON
            get_response = client.get(f"/media/{media_id}")
            get_data = get_response.json()

            # Should be plain string, not executable code
            assert get_data["title"] == title
            assert get_response.headers["content-type"] == "application/json"

            # No HTML parsing should occur
            assert "<script>" not in get_response.headers.get("content-type", "")

            # Delete materials
            delete_response = client.delete(f"/media/{media_id}")
            assert delete_response.status_code == 204

            # Checking
            final_get_response = client.get(f"/media/{media_id}")
            assert final_get_response.status_code == 404
