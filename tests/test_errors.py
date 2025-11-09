from fastapi.testclient import TestClient


class TestErrors:
    def test_user_not_found(self, client: TestClient):
        response = client.get("/users/999")
        assert response.status_code == 404
        body = response.json()
        assert "type" in body
        assert "title" in body
        assert "detail" in body
        assert "correlation_id" in body
        assert "not found" in body["detail"].lower()

    def test_chore_not_found(self, client: TestClient):
        response = client.get("/chores/999")
        assert response.status_code == 404
        body = response.json()
        assert "type" in body
        assert "title" in body
        assert "detail" in body
        assert "correlation_id" in body

    def test_assignment_not_found(self, client: TestClient):
        response = client.get("/assignments/999")
        assert response.status_code == 404
        body = response.json()
        assert "type" in body
        assert "title" in body
        assert "detail" in body
        assert "correlation_id" in body

    def test_validation_error_invalid_email(self, client: TestClient):
        invalid_user = {"name": "Test User", "email": "invalid-email"}
        response = client.post("/users", json=invalid_user)
        assert response.status_code == 422

    def test_validation_error_missing_fields(self, client: TestClient):
        incomplete_user = {"name": "Test User"}
        response = client.post("/users", json=incomplete_user)
        assert response.status_code == 422

    def test_business_logic_error_duplicate_email(self, client: TestClient):
        user_data = {"name": "Test User", "email": "test@example.com"}

        client.post("/users", json=user_data)

        response = client.post("/users", json=user_data)
        assert response.status_code == 400
        body = response.json()
        assert "type" in body
        assert "title" in body
        assert "detail" in body
        assert "correlation_id" in body
        assert "already exists" in body["detail"].lower()

    def test_business_logic_error_invalid_cadence(self, client: TestClient):
        invalid_chore = {"title": "Test Chore", "cadence": "invalid_cadence"}
        response = client.post("/chores", json=invalid_chore)
        assert response.status_code == 422

    def test_business_logic_error_past_due_date(
        self, client: TestClient, sample_user, sample_chore
    ):
        user_response = client.post("/users", json=sample_user)
        user_id = user_response.json()["id"]

        chore_response = client.post("/chores", json=sample_chore)
        chore_id = chore_response.json()["id"]

        from datetime import datetime, timedelta

        assignment_data = {
            "user_id": user_id,
            "chore_id": chore_id,
            "due_at": (datetime.utcnow() - timedelta(days=1)).isoformat(),
        }
        response = client.post("/assignments", json=assignment_data)
        assert response.status_code == 400
        body = response.json()
        assert "type" in body
        assert "title" in body
        assert "detail" in body
        assert "correlation_id" in body
        assert "Due date must be in the future" in body["detail"]

    def test_error_response_format(self, client: TestClient):
        response = client.get("/users/999")
        assert response.status_code == 404

        body = response.json()
        assert isinstance(body, dict)
        assert "type" in body
        assert "title" in body
        assert "detail" in body
        assert "correlation_id" in body
        assert "instance" in body
        assert "timestamp" in body
