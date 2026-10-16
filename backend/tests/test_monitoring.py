def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Welcome to DevTrack Todo API"
    assert body["docs_url"] == "/docs"


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_readiness_check_reports_database(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "connected"}


def test_readiness_check_fails_when_database_is_down(client):
    from app.database import get_db
    from app.main import app

    class BrokenSession:
        def execute(self, *args, **kwargs):
            raise ConnectionError("database unreachable")

    app.dependency_overrides[get_db] = lambda: BrokenSession()
    response = client.get("/ready")
    assert response.status_code == 503
    assert response.json()["status"] == "not ready"


def test_app_info(client):
    response = client.get("/api/info")
    assert response.status_code == 200
    assert response.json()["app"] == "DevTrack Todo"


def test_metrics_exposes_request_counters(client):
    client.get("/api/todos")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    text = response.text
    assert "devtrack_http_requests_total" in text
    assert "devtrack_http_request_duration_seconds_bucket" in text
    # Endpoint labels use the route template, not raw paths
    assert 'endpoint="/api/todos"' in text
