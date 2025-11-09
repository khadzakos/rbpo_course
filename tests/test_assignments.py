from datetime import datetime, timedelta

from fastapi.testclient import TestClient


class TestAssignments:
    def test_get_assignments_empty(self, client: TestClient):
        response = client.get("/assignments")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_assignment_success(
        self, client: TestClient, sample_user, sample_chore, sample_assignment
    ):
        user_response = client.post("/users", json=sample_user)
        user_id = user_response.json()["id"]

        chore_response = client.post("/chores", json=sample_chore)
        chore_id = chore_response.json()["id"]

        assignment_data = {
            "user_id": user_id,
            "chore_id": chore_id,
            "due_at": sample_assignment["due_at"],
        }
        response = client.post("/assignments", json=assignment_data)
        assert response.status_code == 200

        data = response.json()
        assert data["user_id"] == user_id
        assert data["chore_id"] == chore_id
        assert data["status"] == "pending"
        assert "id" in data
        assert "created_at" in data

    def test_create_assignment_user_not_found(self, client: TestClient, sample_chore):
        chore_response = client.post("/chores", json=sample_chore)
        chore_id = chore_response.json()["id"]

        assignment_data = {
            "user_id": 999,
            "chore_id": chore_id,
            "due_at": (datetime.utcnow() + timedelta(days=1)).isoformat(),
        }
        response = client.post("/assignments", json=assignment_data)
        assert response.status_code == 400
        body = response.json()
        assert "type" in body
        assert "title" in body
        assert "detail" in body
        assert "correlation_id" in body
        assert "User not found" in body["detail"]

    def test_create_assignment_chore_not_found(self, client: TestClient, sample_user):
        user_response = client.post("/users", json=sample_user)
        user_id = user_response.json()["id"]

        assignment_data = {
            "user_id": user_id,
            "chore_id": 999,
            "due_at": (datetime.utcnow() + timedelta(days=1)).isoformat(),
        }
        response = client.post("/assignments", json=assignment_data)
        assert response.status_code == 400
        body = response.json()
        assert "type" in body
        assert "title" in body
        assert "detail" in body
        assert "correlation_id" in body
        assert "Chore not found" in body["detail"]

    def test_create_assignment_past_due_date(
        self, client: TestClient, sample_user, sample_chore
    ):
        user_response = client.post("/users", json=sample_user)
        user_id = user_response.json()["id"]

        chore_response = client.post("/chores", json=sample_chore)
        chore_id = chore_response.json()["id"]

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

    def test_get_assignment_by_id_success(
        self, client: TestClient, sample_user, sample_chore, sample_assignment
    ):
        """Тест получения назначения по ID"""
        user_response = client.post("/users", json=sample_user)
        user_id = user_response.json()["id"]

        chore_response = client.post("/chores", json=sample_chore)
        chore_id = chore_response.json()["id"]

        assignment_data = {
            "user_id": user_id,
            "chore_id": chore_id,
            "due_at": sample_assignment["due_at"],
        }
        create_response = client.post("/assignments", json=assignment_data)
        assignment_id = create_response.json()["id"]

        response = client.get(f"/assignments/{assignment_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == assignment_id
        assert data["user_id"] == user_id
        assert data["chore_id"] == chore_id
        assert data["status"] == "pending"

    def test_get_assignment_by_id_not_found(self, client: TestClient):
        response = client.get("/assignments/999")
        assert response.status_code == 404
        body = response.json()
        assert "type" in body
        assert "title" in body
        assert "detail" in body
        assert "correlation_id" in body
        assert "not found" in body["detail"].lower()

    def test_update_assignment_status_success(
        self, client: TestClient, sample_user, sample_chore, sample_assignment
    ):
        user_response = client.post("/users", json=sample_user)
        user_id = user_response.json()["id"]

        chore_response = client.post("/chores", json=sample_chore)
        chore_id = chore_response.json()["id"]

        assignment_data = {
            "user_id": user_id,
            "chore_id": chore_id,
            "due_at": sample_assignment["due_at"],
        }
        create_response = client.post("/assignments", json=assignment_data)
        assignment_id = create_response.json()["id"]

        update_data = {"status": "in_progress"}
        response = client.put(f"/assignments/{assignment_id}", json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "in_progress"

    def test_update_assignment_status_completed(
        self, client: TestClient, sample_user, sample_chore, sample_assignment
    ):
        user_response = client.post("/users", json=sample_user)
        user_id = user_response.json()["id"]

        chore_response = client.post("/chores", json=sample_chore)
        chore_id = chore_response.json()["id"]

        assignment_data = {
            "user_id": user_id,
            "chore_id": chore_id,
            "due_at": sample_assignment["due_at"],
        }
        create_response = client.post("/assignments", json=assignment_data)
        assignment_id = create_response.json()["id"]

        update_data = {"status": "completed"}
        response = client.put(f"/assignments/{assignment_id}", json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "completed"
        assert data["completed_at"] is not None

    def test_update_assignment_status_not_found(self, client: TestClient):
        update_data = {"status": "in_progress"}
        response = client.put("/assignments/999", json=update_data)
        assert response.status_code == 404

    def test_delete_assignment_success(
        self, client: TestClient, sample_user, sample_chore, sample_assignment
    ):
        user_response = client.post("/users", json=sample_user)
        user_id = user_response.json()["id"]

        chore_response = client.post("/chores", json=sample_chore)
        chore_id = chore_response.json()["id"]

        assignment_data = {
            "user_id": user_id,
            "chore_id": chore_id,
            "due_at": sample_assignment["due_at"],
        }
        create_response = client.post("/assignments", json=assignment_data)
        assignment_id = create_response.json()["id"]

        response = client.delete(f"/assignments/{assignment_id}")
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

        get_response = client.get(f"/assignments/{assignment_id}")
        assert get_response.status_code == 404

    def test_delete_assignment_not_found(self, client: TestClient):
        response = client.delete("/assignments/999")
        assert response.status_code == 404

    def test_get_assignments_with_data(
        self, client: TestClient, sample_user, sample_chore
    ):
        user_response = client.post("/users", json=sample_user)
        user_id = user_response.json()["id"]

        chore_response = client.post("/chores", json=sample_chore)
        chore_id = chore_response.json()["id"]

        for i in range(3):
            assignment_data = {
                "user_id": user_id,
                "chore_id": chore_id,
                "due_at": (datetime.utcnow() + timedelta(days=i + 1)).isoformat(),
            }
            client.post("/assignments", json=assignment_data)

        response = client.get("/assignments")
        assert response.status_code == 200

        assignments = response.json()
        assert len(assignments) == 3

        for assignment in assignments:
            assert assignment["user_id"] == user_id
            assert assignment["chore_id"] == chore_id
            assert assignment["status"] == "pending"

    def test_create_assignment_invalid_status(
        self, client: TestClient, sample_user, sample_chore, sample_assignment
    ):
        user_response = client.post("/users", json=sample_user)
        user_id = user_response.json()["id"]

        chore_response = client.post("/chores", json=sample_chore)
        chore_id = chore_response.json()["id"]

        assignment_data = {
            "user_id": user_id,
            "chore_id": chore_id,
            "due_at": sample_assignment["due_at"],
        }
        create_response = client.post("/assignments", json=assignment_data)
        assignment_id = create_response.json()["id"]

        update_data = {"status": "invalid_status"}
        response = client.put(f"/assignments/{assignment_id}", json=update_data)
        assert response.status_code == 422  # Validation error
