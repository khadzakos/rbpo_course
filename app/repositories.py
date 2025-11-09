from datetime import datetime
from typing import List, Optional

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from .models import Assignment, AssignmentStatus, Chore, User


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, name: str, email: str) -> User:
        user = User(name=name, email=email)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.session.get(User, user_id)

    def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_all(self) -> List[User]:
        stmt = select(User)
        return list(self.session.execute(stmt).scalars().all())

    def update(
        self, user_id: int, name: str = None, email: str = None
    ) -> Optional[User]:
        user = self.get_by_id(user_id)
        if not user:
            return None

        if name is not None:
            user.name = name
        if email is not None:
            user.email = email

        self.session.commit()
        self.session.refresh(user)
        return user

    def delete(self, user_id: int) -> bool:
        user = self.get_by_id(user_id)
        if not user:
            return False

        self.session.delete(user)
        self.session.commit()
        return True


class ChoreRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, title: str, cadence: str) -> Chore:
        chore = Chore(title=title, cadence=cadence)
        self.session.add(chore)
        self.session.commit()
        self.session.refresh(chore)
        return chore

    def get_by_id(self, chore_id: int) -> Optional[Chore]:
        return self.session.get(Chore, chore_id)

    def get_all(self) -> List[Chore]:
        stmt = select(Chore)
        return list(self.session.execute(stmt).scalars().all())

    def update(
        self, chore_id: int, title: str = None, cadence: str = None
    ) -> Optional[Chore]:
        chore = self.get_by_id(chore_id)
        if not chore:
            return None

        if title is not None:
            chore.title = title
        if cadence is not None:
            chore.cadence = cadence

        self.session.commit()
        self.session.refresh(chore)
        return chore

    def delete(self, chore_id: int) -> bool:
        chore = self.get_by_id(chore_id)
        if not chore:
            return False

        self.session.delete(chore)
        self.session.commit()
        return True


class AssignmentRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, user_id: int, chore_id: int, due_at: datetime) -> Assignment:
        assignment = Assignment(user_id=user_id, chore_id=chore_id, due_at=due_at)
        self.session.add(assignment)
        self.session.commit()
        self.session.refresh(assignment)
        return assignment

    def get_by_id(self, assignment_id: int) -> Optional[Assignment]:
        return self.session.get(Assignment, assignment_id)

    def get_all(self) -> List[Assignment]:
        stmt = select(Assignment)
        return list(self.session.execute(stmt).scalars().all())

    def get_by_user(self, user_id: int) -> List[Assignment]:
        stmt = select(Assignment).where(Assignment.user_id == user_id)
        return list(self.session.execute(stmt).scalars().all())

    def get_by_chore(self, chore_id: int) -> List[Assignment]:
        stmt = select(Assignment).where(Assignment.chore_id == chore_id)
        return list(self.session.execute(stmt).scalars().all())

    def get_by_status(self, status: AssignmentStatus) -> List[Assignment]:
        stmt = select(Assignment).where(Assignment.status == status)
        return list(self.session.execute(stmt).scalars().all())

    def get_overdue(self) -> List[Assignment]:
        now = datetime.utcnow()
        stmt = select(Assignment).where(
            and_(
                Assignment.due_at < now, Assignment.status != AssignmentStatus.COMPLETED
            )
        )
        return list(self.session.execute(stmt).scalars().all())

    def update_status(
        self, assignment_id: int, status: AssignmentStatus
    ) -> Optional[Assignment]:
        assignment = self.get_by_id(assignment_id)
        if not assignment:
            return None

        assignment.status = status
        if status == AssignmentStatus.COMPLETED:
            assignment.completed_at = datetime.utcnow()

        self.session.commit()
        self.session.refresh(assignment)
        return assignment

    def delete(self, assignment_id: int) -> bool:
        assignment = self.get_by_id(assignment_id)
        if not assignment:
            return False

        self.session.delete(assignment)
        self.session.commit()
        return True
