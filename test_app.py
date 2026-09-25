from unittest.mock import patch
from app import alert_threshold, sanitize_input, app


def test_alert_threshold():
    assert alert_threshold() == 25


def test_sanitize_input_escapes_html():
    assert sanitize_input("<script>") == "&lt;script&gt;"


def test_health_endpoint_healthy():
    with patch("app.get_redis_client") as mock_client:
        mock_client.return_value.ping.return_value = True
        client = app.test_client()
        response = client.get("/health")
        assert response.status_code == 200
        assert response.get_json()["status"] == "ok"


def test_health_endpoint_unhealthy():
    with patch("app.get_redis_client") as mock_client:
        mock_client.return_value.ping.side_effect = Exception("err")
        client = app.test_client()
        response = client.get("/health")
        assert response.status_code == 503
        assert response.get_json()["status"] == "unhealthy"


def test_status_endpoint():
    client = app.test_client()
    response = client.get("/status")
    assert response.status_code == 200
    data = response.get_json()
    assert data["service"] == "projet-devops-groupe-demo"
    assert "deploy_color" in data
    assert "commit_sha" in data
