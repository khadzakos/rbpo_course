from datetime import datetime, timedelta

from fastapi.testclient import TestClient


class TestStatistics:
    def test_get_statistics_empty(self, client: TestClient):
        response = client.get("/statistics")
        assert response.status_code == 200

        data = response.json()
        assert "statistics" in data

        stats = data["statistics"]
        assert stats["total_assignments"] == 0
        assert stats["completed_assignments"] == 0
        assert stats["pending_assignments"] == 0
        assert stats["overdue_assignments"] == 0
        assert stats["completion_rate"] == 0

    def test_get_statistics_with_assignments(
        self, client: TestClient, sample_user, sample_chore
    ):
        user_response = client.post("/users", json=sample_user)
        user_id = user_response.json()["id"]

        chore_response = client.post("/chores", json=sample_chore)
        chore_id = chore_response.json()["id"]

        assignments_data = [
            {
                "user_id": user_id,
                "chore_id": chore_id,
                "due_at": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            },
            {
                "user_id": user_id,
                "chore_id": chore_id,
                "due_at": (datetime.utcnow() + timedelta(days=2)).isoformat(),
            },
            {
                "user_id": user_id,
                "chore_id": chore_id,
                "due_at": (datetime.utcnow() + timedelta(days=3)).isoformat(),
            },
        ]

        assignment_ids = []
        for assignment_data in assignments_data:
            response = client.post("/assignments", json=assignment_data)
            assignment_ids.append(response.json()["id"])

        client.put(f"/assignments/{assignment_ids[0]}", json={"status": "completed"})

        client.put(f"/assignments/{assignment_ids[1]}", json={"status": "in_progress"})

        response = client.get("/statistics")
        assert response.status_code == 200

        data = response.json()
        stats = data["statistics"]

        assert stats["total_assignments"] == 3
        assert stats["completed_assignments"] == 1
        assert stats["pending_assignments"] == 1
        assert stats["overdue_assignments"] == 0
        assert stats["completion_rate"] == 33.33  # 1/3 * 100

    def test_get_statistics_with_overdue_assignments(
        self, client: TestClient, sample_user, sample_chore
    ):
        user_response = client.post("/users", json=sample_user)
        user_id = user_response.json()["id"]

        chore_response = client.post("/chores", json=sample_chore)
        chore_id = chore_response.json()["id"]

        assignment1_data = {
            "user_id": user_id,
            "chore_id": chore_id,
            "due_at": (datetime.utcnow() + timedelta(days=1)).isoformat(),
        }

        assignment2_data = {
            "user_id": user_id,
            "chore_id": chore_id,
            "due_at": (datetime.utcnow() + timedelta(days=2)).isoformat(),
        }

        response1 = client.post("/assignments", json=assignment1_data)
        client.post("/assignments", json=assignment2_data)

        assignment1_id = response1.json()["id"]

        client.put(f"/assignments/{assignment1_id}", json={"status": "completed"})

        response = client.get("/statistics")
        assert response.status_code == 200

        data = response.json()
        stats = data["statistics"]

        assert stats["total_assignments"] == 2
        assert stats["completed_assignments"] == 1
        assert stats["pending_assignments"] == 1
        assert stats["overdue_assignments"] == 0

    def test_get_statistics_completion_rate_calculation(
        self, client: TestClient, sample_user, sample_chore
    ):
        user_response = client.post("/users", json=sample_user)
        user_id = user_response.json()["id"]

        chore_response = client.post("/chores", json=sample_chore)
        chore_id = chore_response.json()["id"]

        assignment_ids = []
        for i in range(4):
            assignment_data = {
                "user_id": user_id,
                "chore_id": chore_id,
                "due_at": (datetime.utcnow() + timedelta(days=i + 1)).isoformat(),
            }
            response = client.post("/assignments", json=assignment_data)
            assignment_ids.append(response.json()["id"])

        client.put(f"/assignments/{assignment_ids[0]}", json={"status": "completed"})
        client.put(f"/assignments/{assignment_ids[1]}", json={"status": "completed"})

        response = client.get("/statistics")
        assert response.status_code == 200

        data = response.json()
        stats = data["statistics"]

        assert stats["total_assignments"] == 4
        assert stats["completed_assignments"] == 2
        assert stats["completion_rate"] == 50.0  # 2/4 * 100

    def test_get_statistics_mixed_statuses(
        self, client: TestClient, sample_user, sample_chore
    ):
        user_response = client.post("/users", json=sample_user)
        user_id = user_response.json()["id"]

        chore_response = client.post("/chores", json=sample_chore)
        chore_id = chore_response.json()["id"]

        assignment_ids = []
        for i in range(5):
            assignment_data = {
                "user_id": user_id,
                "chore_id": chore_id,
                "due_at": (datetime.utcnow() + timedelta(days=i + 1)).isoformat(),
            }
            response = client.post("/assignments", json=assignment_data)
            assignment_ids.append(response.json()["id"])

        client.put(f"/assignments/{assignment_ids[0]}", json={"status": "completed"})
        client.put(f"/assignments/{assignment_ids[1]}", json={"status": "completed"})
        client.put(f"/assignments/{assignment_ids[2]}", json={"status": "in_progress"})
        client.put(f"/assignments/{assignment_ids[3]}", json={"status": "in_progress"})

        response = client.get("/statistics")
        assert response.status_code == 200

        data = response.json()
        stats = data["statistics"]

        assert stats["total_assignments"] == 5
        assert stats["completed_assignments"] == 2
        assert stats["pending_assignments"] == 1
        assert stats["completion_rate"] == 40.0  # 2/5 * 100

    def test_get_statistics_100_percent_completion(
        self, client: TestClient, sample_user, sample_chore
    ):
        user_response = client.post("/users", json=sample_user)
        user_id = user_response.json()["id"]

        chore_response = client.post("/chores", json=sample_chore)
        chore_id = chore_response.json()["id"]

        assignment_ids = []
        for i in range(3):
            assignment_data = {
                "user_id": user_id,
                "chore_id": chore_id,
                "due_at": (datetime.utcnow() + timedelta(days=i + 1)).isoformat(),
            }
            response = client.post("/assignments", json=assignment_data)
            assignment_ids.append(response.json()["id"])

        for assignment_id in assignment_ids:
            client.put(f"/assignments/{assignment_id}", json={"status": "completed"})

        response = client.get("/statistics")
        assert response.status_code == 200

        data = response.json()
        stats = data["statistics"]

        assert stats["total_assignments"] == 3
        assert stats["completed_assignments"] == 3
        assert stats["pending_assignments"] == 0
        assert stats["completion_rate"] == 100.0
