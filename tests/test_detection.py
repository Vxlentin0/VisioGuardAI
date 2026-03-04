"""Integration tests for the /api/v1/detect endpoint."""

import pytest


class TestDetectEndpoint:
    def test_successful_detection(self, client, valid_image_bytes, auth_headers):
        resp = client.post(
            "/api/v1/detect",
            files={"file": ("test.jpg", valid_image_bytes, "image/jpeg")},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "detections" in body
        assert "caption" in body
        assert isinstance(body["detections"], list)
        assert len(body["detections"]) == 1
        assert body["detections"][0]["label"] == "person"
        assert body["caption"] == "a person standing in a room"

    def test_returns_rate_limit_headers(self, client, valid_image_bytes, auth_headers):
        resp = client.post(
            "/api/v1/detect",
            files={"file": ("test.jpg", valid_image_bytes, "image/jpeg")},
            headers=auth_headers,
        )
        assert "X-RateLimit-Limit" in resp.headers
        assert "X-RateLimit-Remaining" in resp.headers
        assert "X-RateLimit-Reset" in resp.headers

    def test_returns_request_id(self, client, valid_image_bytes, auth_headers):
        resp = client.post(
            "/api/v1/detect",
            files={"file": ("test.jpg", valid_image_bytes, "image/jpeg")},
            headers=auth_headers,
        )
        assert "X-Request-ID" in resp.headers

    def test_forwards_client_request_id(self, client, valid_image_bytes, auth_headers):
        auth_headers["X-Request-ID"] = "my-trace-id"
        resp = client.post(
            "/api/v1/detect",
            files={"file": ("test.jpg", valid_image_bytes, "image/jpeg")},
            headers=auth_headers,
        )
        assert resp.headers["X-Request-ID"] == "my-trace-id"

    def test_returns_processing_time(self, client, valid_image_bytes, auth_headers):
        resp = client.post(
            "/api/v1/detect",
            files={"file": ("test.jpg", valid_image_bytes, "image/jpeg")},
            headers=auth_headers,
        )
        assert "X-Processing-Time-Ms" in resp.headers
        assert float(resp.headers["X-Processing-Time-Ms"]) >= 0

    def test_missing_api_key(self, client, valid_image_bytes):
        resp = client.post(
            "/api/v1/detect",
            files={"file": ("test.jpg", valid_image_bytes, "image/jpeg")},
        )
        assert resp.status_code == 403
        assert resp.json()["detail"]["code"] == "MISSING_API_KEY"

    def test_invalid_api_key(self, client, valid_image_bytes):
        resp = client.post(
            "/api/v1/detect",
            files={"file": ("test.jpg", valid_image_bytes, "image/jpeg")},
            headers={"X-API-Key": "bad-key"},
        )
        assert resp.status_code == 403
        assert resp.json()["detail"]["code"] == "INVALID_API_KEY"

    def test_unsupported_content_type(self, client, auth_headers):
        resp = client.post(
            "/api/v1/detect",
            files={"file": ("test.txt", b"not an image", "text/plain")},
            headers=auth_headers,
        )
        assert resp.status_code == 415
        assert resp.json()["detail"]["code"] == "UNSUPPORTED_MEDIA_TYPE"

    def test_empty_file(self, client, auth_headers):
        resp = client.post(
            "/api/v1/detect",
            files={"file": ("empty.jpg", b"", "image/jpeg")},
            headers=auth_headers,
        )
        assert resp.status_code == 400
        assert resp.json()["detail"]["code"] == "EMPTY_FILE"


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "healthy"}

    def test_health_no_auth_required(self, client):
        """Health check must be accessible without an API key."""
        resp = client.get("/health")
        assert resp.status_code == 200
