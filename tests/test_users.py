from fastapi.testclient import TestClient


class TestUsers:
    def test_get_users_empty(self, client: TestClient):
        response = client.get("/users")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_user_success(self, client: TestClient, sample_user):
        response = client.post("/users", json=sample_user)
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == sample_user["name"]
        assert data["email"] == sample_user["email"]
        assert "id" in data
        assert "created_at" in data

    def test_create_user_duplicate_email(self, client: TestClient, sample_user):
        client.post("/users", json=sample_user)

        response = client.post("/users", json=sample_user)
        assert response.status_code == 400
        body = response.json()
        assert "type" in body
        assert "title" in body
        assert "detail" in body
        assert "correlation_id" in body
        assert "already exists" in body["detail"].lower()

    def test_create_user_invalid_email(self, client: TestClient):
        invalid_user = {"name": "Test User", "email": "invalid-email"}
        response = client.post("/users", json=invalid_user)
        assert response.status_code == 422

    def test_get_user_by_id_success(self, client: TestClient, sample_user):
        create_response = client.post("/users", json=sample_user)
        user_id = create_response.json()["id"]

        response = client.get(f"/users/{user_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == user_id
        assert data["name"] == sample_user["name"]
        assert data["email"] == sample_user["email"]

    def test_get_user_by_id_not_found(self, client: TestClient):
        response = client.get("/users/999")
        assert response.status_code == 404
        body = response.json()
        assert "type" in body
        assert "title" in body
        assert "detail" in body
        assert "correlation_id" in body
        assert "not found" in body["detail"].lower()

    def test_update_user_success(self, client: TestClient, sample_user):
        create_response = client.post("/users", json=sample_user)
        user_id = create_response.json()["id"]

        update_data = {"name": "Updated Name", "email": "updated@example.com"}
        response = client.put(f"/users/{user_id}", json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["email"] == update_data["email"]

    def test_update_user_partial(self, client: TestClient, sample_user):
        create_response = client.post("/users", json=sample_user)
        user_id = create_response.json()["id"]

        update_data = {"name": "Updated Name Only"}
        response = client.put(f"/users/{user_id}", json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "Updated Name Only"
        assert data["email"] == sample_user["email"]

    def test_update_user_not_found(self, client: TestClient):
        update_data = {"name": "Updated Name"}
        response = client.put("/users/999", json=update_data)
        assert response.status_code == 404

    def test_delete_user_success(self, client: TestClient, sample_user):
        create_response = client.post("/users", json=sample_user)
        user_id = create_response.json()["id"]

        response = client.delete(f"/users/{user_id}")
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

        get_response = client.get(f"/users/{user_id}")
        assert get_response.status_code == 404

    def test_delete_user_not_found(self, client: TestClient):
        response = client.delete("/users/999")
        assert response.status_code == 404

    def test_get_users_with_data(self, client: TestClient):
        users_data = [
            {"name": "User 1", "email": "user1@example.com"},
            {"name": "User 2", "email": "user2@example.com"},
        ]

        for user_data in users_data:
            client.post("/users", json=user_data)

        response = client.get("/users")
        assert response.status_code == 200

        users = response.json()
        assert len(users) == 2
        assert users[0]["name"] in ["User 1", "User 2"]
        assert users[1]["name"] in ["User 1", "User 2"]
