from datetime import datetime
from typing import List, Optional

from .models import Assignment, AssignmentStatus, Chore, User
from .repositories import AssignmentRepository, ChoreRepository, UserRepository


class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def create_user(self, name: str, email: str) -> User:
        existing_user = self.user_repo.get_by_email(email)
        if existing_user:
            raise ValueError("User with this email already exists")

        return self.user_repo.create(name=name, email=email)

    def get_user(self, user_id: int) -> Optional[User]:
        return self.user_repo.get_by_id(user_id)

    def get_all_users(self) -> List[User]:
        return self.user_repo.get_all()

    def update_user(
        self, user_id: int, name: str = None, email: str = None
    ) -> Optional[User]:
        if email is not None:
            existing_user = self.user_repo.get_by_email(email)
            if existing_user and existing_user.id != user_id:
                raise ValueError("User with this email already exists")

        return self.user_repo.update(user_id, name, email)

    def delete_user(self, user_id: int) -> bool:
        return self.user_repo.delete(user_id)


class ChoreService:
    def __init__(self, chore_repo: ChoreRepository):
        self.chore_repo = chore_repo

    def create_chore(self, title: str, cadence: str) -> Chore:
        valid_cadences = ["daily", "weekly", "monthly", "yearly"]
        if cadence not in valid_cadences:
            raise ValueError(f"Invalid cadence. Must be one of: {valid_cadences}")

        return self.chore_repo.create(title=title, cadence=cadence)

    def get_chore(self, chore_id: int) -> Optional[Chore]:
        return self.chore_repo.get_by_id(chore_id)

    def get_all_chores(self) -> List[Chore]:
        return self.chore_repo.get_all()

    def update_chore(
        self, chore_id: int, title: str = None, cadence: str = None
    ) -> Optional[Chore]:
        if cadence is not None:
            valid_cadences = ["daily", "weekly", "monthly", "yearly"]
            if cadence not in valid_cadences:
                raise ValueError(f"Invalid cadence. Must be one of: {valid_cadences}")

        return self.chore_repo.update(chore_id, title, cadence)

    def delete_chore(self, chore_id: int) -> bool:
        return self.chore_repo.delete(chore_id)


class AssignmentService:
    def __init__(
        self,
        assignment_repo: AssignmentRepository,
        user_repo: UserRepository,
        chore_repo: ChoreRepository,
    ):
        self.assignment_repo = assignment_repo
        self.user_repo = user_repo
        self.chore_repo = chore_repo

    def create_assignment(
        self, user_id: int, chore_id: int, due_at: datetime
    ) -> Assignment:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        chore = self.chore_repo.get_by_id(chore_id)
        if not chore:
            raise ValueError("Chore not found")

        if due_at <= datetime.utcnow():
            raise ValueError("Due date must be in the future")

        return self.assignment_repo.create(user_id, chore_id, due_at)

    def get_assignment(self, assignment_id: int) -> Optional[Assignment]:
        return self.assignment_repo.get_by_id(assignment_id)

    def get_all_assignments(self) -> List[Assignment]:
        return self.assignment_repo.get_all()

    def get_user_assignments(self, user_id: int) -> List[Assignment]:
        return self.assignment_repo.get_by_user(user_id)

    def get_chore_assignments(self, chore_id: int) -> List[Assignment]:
        return self.assignment_repo.get_by_chore(chore_id)

    def get_assignments_by_status(self, status: AssignmentStatus) -> List[Assignment]:
        return self.assignment_repo.get_by_status(status)

    def get_overdue_assignments(self) -> List[Assignment]:
        return self.assignment_repo.get_overdue()

    def update_assignment_status(
        self, assignment_id: int, status: AssignmentStatus
    ) -> Optional[Assignment]:
        assignment = self.assignment_repo.get_by_id(assignment_id)
        if not assignment:
            return None

        if (
            assignment.due_at < datetime.utcnow()
            and status != AssignmentStatus.COMPLETED
        ):
            status = AssignmentStatus.OVERDUE

        return self.assignment_repo.update_status(assignment_id, status)

    def complete_assignment(self, assignment_id: int) -> Optional[Assignment]:
        return self.update_assignment_status(assignment_id, AssignmentStatus.COMPLETED)

    def delete_assignment(self, assignment_id: int) -> bool:
        return self.assignment_repo.delete(assignment_id)

    def get_statistics(self) -> dict:
        """Get statistics about assignments"""
        all_assignments = self.assignment_repo.get_all()
        overdue_assignments = self.assignment_repo.get_overdue()

        total_assignments = len(all_assignments)
        completed_assignments = len(
            [a for a in all_assignments if a.status == AssignmentStatus.COMPLETED]
        )
        pending_assignments = len(
            [a for a in all_assignments if a.status == AssignmentStatus.PENDING]
        )
        overdue_count = len(overdue_assignments)

        completion_rate = (
            (completed_assignments / total_assignments * 100)
            if total_assignments > 0
            else 0
        )

        return {
            "total_assignments": total_assignments,
            "completed_assignments": completed_assignments,
            "pending_assignments": pending_assignments,
            "overdue_assignments": overdue_count,
            "completion_rate": round(completion_rate, 2),
        }
