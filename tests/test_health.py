from fastapi.testclient import TestClient


class TestHealth:
    def test_health_ok(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_healthz_ok(self, client: TestClient):
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
