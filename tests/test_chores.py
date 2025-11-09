from fastapi.testclient import TestClient


class TestChores:
    def test_get_chores_empty(self, client: TestClient):
        response = client.get("/chores")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_chore_success(self, client: TestClient, sample_chore):
        response = client.post("/chores", json=sample_chore)
        assert response.status_code == 200

        data = response.json()
        assert data["title"] == sample_chore["title"]
        assert data["cadence"] == sample_chore["cadence"]
        assert "id" in data
        assert "created_at" in data

    def test_create_chore_invalid_cadence(self, client: TestClient):
        invalid_chore = {"title": "Test Chore", "cadence": "invalid_cadence"}
        response = client.post("/chores", json=invalid_chore)
        assert response.status_code == 422

    def test_create_chore_missing_fields(self, client: TestClient):
        incomplete_chore = {"title": "Test Chore"}
        response = client.post("/chores", json=incomplete_chore)
        assert response.status_code == 422

    def test_get_chore_by_id_success(self, client: TestClient, sample_chore):
        create_response = client.post("/chores", json=sample_chore)
        chore_id = create_response.json()["id"]

        response = client.get(f"/chores/{chore_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == chore_id
        assert data["title"] == sample_chore["title"]
        assert data["cadence"] == sample_chore["cadence"]

    def test_get_chore_by_id_not_found(self, client: TestClient):
        response = client.get("/chores/999")
        assert response.status_code == 404
        body = response.json()
        assert "type" in body
        assert "title" in body
        assert "detail" in body
        assert "correlation_id" in body
        assert "not found" in body["detail"].lower()

    def test_update_chore_success(self, client: TestClient, sample_chore):
        create_response = client.post("/chores", json=sample_chore)
        chore_id = create_response.json()["id"]

        update_data = {"title": "Updated Chore", "cadence": "weekly"}
        response = client.put(f"/chores/{chore_id}", json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["cadence"] == update_data["cadence"]

    def test_update_chore_partial(self, client: TestClient, sample_chore):
        create_response = client.post("/chores", json=sample_chore)
        chore_id = create_response.json()["id"]

        update_data = {"title": "Updated Title Only"}
        response = client.put(f"/chores/{chore_id}", json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["title"] == "Updated Title Only"
        assert data["cadence"] == sample_chore["cadence"]

    def test_update_chore_invalid_cadence(self, client: TestClient, sample_chore):
        create_response = client.post("/chores", json=sample_chore)
        chore_id = create_response.json()["id"]

        update_data = {"cadence": "invalid_cadence"}
        response = client.put(f"/chores/{chore_id}", json=update_data)
        assert response.status_code == 422

    def test_update_chore_not_found(self, client: TestClient):
        update_data = {"title": "Updated Title"}
        response = client.put("/chores/999", json=update_data)
        assert response.status_code == 404

    def test_delete_chore_success(self, client: TestClient, sample_chore):
        create_response = client.post("/chores", json=sample_chore)
        chore_id = create_response.json()["id"]

        response = client.delete(f"/chores/{chore_id}")
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

        get_response = client.get(f"/chores/{chore_id}")
        assert get_response.status_code == 404

    def test_delete_chore_not_found(self, client: TestClient):
        response = client.delete("/chores/999")
        assert response.status_code == 404

    def test_get_chores_with_data(self, client: TestClient):
        chores_data = [
            {"title": "Daily Task", "cadence": "daily"},
            {"title": "Weekly Task", "cadence": "weekly"},
            {"title": "Monthly Task", "cadence": "monthly"},
        ]

        for chore_data in chores_data:
            client.post("/chores", json=chore_data)

        response = client.get("/chores")
        assert response.status_code == 200

        chores = response.json()
        assert len(chores) == 3

        titles = [chore["title"] for chore in chores]
        assert "Daily Task" in titles
        assert "Weekly Task" in titles
        assert "Monthly Task" in titles

    def test_create_chore_all_valid_cadences(self, client: TestClient):
        valid_cadences = ["daily", "weekly", "monthly", "yearly"]

        for cadence in valid_cadences:
            chore_data = {"title": f"Test {cadence.title()} Task", "cadence": cadence}
            response = client.post("/chores", json=chore_data)
            assert response.status_code == 200
            assert response.json()["cadence"] == cadence
