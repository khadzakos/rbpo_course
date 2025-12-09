from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy.orm import Session

from .config import get_db
from .models import AssignmentStatus
from .repositories import AssignmentRepository, ChoreRepository, UserRepository
from .security import ERROR_TYPES, InputValidator, SecureHTTPException
from .services import AssignmentService, ChoreService, UserService


class UserCreate(BaseModel):
    name: str
    email: EmailStr

    @validator("name")
    def validate_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Name cannot be empty")
        if len(v) > 100:
            raise ValueError("Name too long (max 100 characters)")
        return InputValidator.sanitize_string(v, 100)

    @validator("email")
    def validate_email(cls, v):
        if not InputValidator.validate_email(v):
            raise ValueError("Invalid email format")
        return v.lower().strip()


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None

    @validator("name")
    def validate_name(cls, v):
        if v is not None:
            if len(v.strip()) == 0:
                raise ValueError("Name cannot be empty")
            if len(v) > 100:
                raise ValueError("Name too long (max 100 characters)")
            return InputValidator.sanitize_string(v, 100)
        return v

    @validator("email")
    def validate_email(cls, v):
        if v is not None:
            if not InputValidator.validate_email(v):
                raise ValueError("Invalid email format")
            return v.lower().strip()
        return v


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChoreCreate(BaseModel):
    title: str
    cadence: str

    @validator("title")
    def validate_title(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Title cannot be empty")
        if len(v) > 200:
            raise ValueError("Title too long (max 200 characters)")
        return InputValidator.sanitize_string(v, 200)

    @validator("cadence")
    def validate_cadence(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Cadence cannot be empty")
        if len(v) > 50:
            raise ValueError("Cadence too long (max 50 characters)")
        allowed_cadences = ["daily", "weekly", "monthly", "yearly", "once"]
        if v.lower() not in allowed_cadences:
            raise ValueError(
                f"Invalid cadence. Allowed values: {', '.join(allowed_cadences)}"
            )
        return v.lower().strip()


class ChoreUpdate(BaseModel):
    title: Optional[str] = None
    cadence: Optional[str] = None

    @validator("title")
    def validate_title(cls, v):
        if v is not None:
            if len(v.strip()) == 0:
                raise ValueError("Title cannot be empty")
            if len(v) > 200:
                raise ValueError("Title too long (max 200 characters)")
            return InputValidator.sanitize_string(v, 200)
        return v

    @validator("cadence")
    def validate_cadence(cls, v):
        if v is not None:
            if len(v.strip()) == 0:
                raise ValueError("Cadence cannot be empty")
            if len(v) > 50:
                raise ValueError("Cadence too long (max 50 characters)")
            allowed_cadences = ["daily", "weekly", "monthly", "yearly", "once"]
            if v.lower() not in allowed_cadences:
                raise ValueError(
                    f"Invalid cadence. Allowed values: {', '.join(allowed_cadences)}"
                )
            return v.lower().strip()
        return v


class ChoreResponse(BaseModel):
    id: int
    title: str
    cadence: str
    created_at: datetime

    class Config:
        from_attributes = True


class AssignmentCreate(BaseModel):
    user_id: int
    chore_id: int
    due_at: datetime


class AssignmentUpdate(BaseModel):
    status: AssignmentStatus


class AssignmentResponse(BaseModel):
    id: int
    user_id: int
    chore_id: int
    due_at: datetime
    status: AssignmentStatus
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    user_repo = UserRepository(db)
    return UserService(user_repo)


def get_chore_service(db: Session = Depends(get_db)) -> ChoreService:
    chore_repo = ChoreRepository(db)
    return ChoreService(chore_repo)


def get_assignment_service(db: Session = Depends(get_db)) -> AssignmentService:
    assignment_repo = AssignmentRepository(db)
    user_repo = UserRepository(db)
    chore_repo = ChoreRepository(db)
    return AssignmentService(assignment_repo, user_repo, chore_repo)


router = APIRouter()


@router.get("/", tags=["Root"], summary="Корневой эндпойнт API")
def root():
    """Корневой эндпойнт API"""
    return {
        "name": "Chore Tracker API",
        "version": "0.1.0",
        "status": "ok",
        "docs": "/docs",
        "health": "/health"
    }


@router.get("/health", tags=["Health"], summary="Проверка состояния API")
def health():
    """Проверка работоспособности API"""
    return {"status": "ok"}


@router.get(
    "/healthz",
    tags=["Health"],
    summary="Проверка состояния API (альтернативный endpoint)",
)
def healthz():
    """Проверка работоспособности API (альтернативный endpoint для CI/CD)"""
    return {"status": "ok"}


@router.get(
    "/statistics", tags=["Statistics"], summary="Получить статистику по назначениям"
)
def get_statistics(
    assignment_service: AssignmentService = Depends(get_assignment_service),
):
    """Получить статистику по всем назначениям:
    - общее количество
    - завершенные
    - просроченные
    - процент выполнения"""
    try:
        stats = assignment_service.get_statistics()
        return {"statistics": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users", response_model=List[UserResponse], tags=["Users"])
def get_users(user_service: UserService = Depends(get_user_service)):
    try:
        users = user_service.get_all_users()
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}", response_model=UserResponse, tags=["Users"])
def get_user(user_id: int, user_service: UserService = Depends(get_user_service)):
    try:
        user = user_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users", response_model=UserResponse, tags=["Users"])
def create_user(
    user_data: UserCreate, user_service: UserService = Depends(get_user_service)
):
    try:
        user = user_service.create_user(user_data.name, user_data.email)
        return user
    except ValueError as e:
        raise SecureHTTPException(
            error_type=ERROR_TYPES["validation_error"],
            title="Validation Error",
            detail=str(e),
            status_code=400,
        )
    except Exception:
        raise SecureHTTPException(
            error_type=ERROR_TYPES["internal_error"],
            title="Internal Server Error",
            detail="Failed to create user",
            status_code=500,
        )


@router.put("/users/{user_id}", response_model=UserResponse, tags=["Users"])
def update_user(
    user_id: int,
    user_data: UserUpdate,
    user_service: UserService = Depends(get_user_service),
):
    try:
        user = user_service.update_user(user_id, user_data.name, user_data.email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/users/{user_id}", tags=["Users"])
def delete_user(user_id: int, user_service: UserService = Depends(get_user_service)):
    try:
        success = user_service.delete_user(user_id)
        if not success:
            raise HTTPException(status_code=404, detail="User not found")
        return {"message": "User deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chores", response_model=List[ChoreResponse], tags=["Chores"])
def get_chores(chore_service: ChoreService = Depends(get_chore_service)):
    try:
        chores = chore_service.get_all_chores()
        return chores
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chores/{chore_id}", response_model=ChoreResponse, tags=["Chores"])
def get_chore(chore_id: int, chore_service: ChoreService = Depends(get_chore_service)):
    try:
        chore = chore_service.get_chore(chore_id)
        if not chore:
            raise HTTPException(status_code=404, detail="Chore not found")
        return chore
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chores", response_model=ChoreResponse, tags=["Chores"])
def create_chore(
    chore_data: ChoreCreate, chore_service: ChoreService = Depends(get_chore_service)
):
    try:
        chore = chore_service.create_chore(chore_data.title, chore_data.cadence)
        return chore
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/chores/{chore_id}", response_model=ChoreResponse, tags=["Chores"])
def update_chore(
    chore_id: int,
    chore_data: ChoreUpdate,
    chore_service: ChoreService = Depends(get_chore_service),
):
    try:
        chore = chore_service.update_chore(
            chore_id, chore_data.title, chore_data.cadence
        )
        if not chore:
            raise HTTPException(status_code=404, detail="Chore not found")
        return chore
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/chores/{chore_id}", tags=["Chores"])
def delete_chore(
    chore_id: int, chore_service: ChoreService = Depends(get_chore_service)
):
    try:
        success = chore_service.delete_chore(chore_id)
        if not success:
            raise HTTPException(status_code=404, detail="Chore not found")
        return {"message": "Chore deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/assignments", response_model=List[AssignmentResponse], tags=["Assignments"]
)
def get_assignments(
    assignment_service: AssignmentService = Depends(get_assignment_service),
):
    try:
        assignments = assignment_service.get_all_assignments()
        return assignments
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/assignments/{assignment_id}",
    response_model=AssignmentResponse,
    tags=["Assignments"],
)
def get_assignment(
    assignment_id: int,
    assignment_service: AssignmentService = Depends(get_assignment_service),
):
    try:
        assignment = assignment_service.get_assignment(assignment_id)
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        return assignment
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/assignments", response_model=AssignmentResponse, tags=["Assignments"])
def create_assignment(
    assignment_data: AssignmentCreate,
    assignment_service: AssignmentService = Depends(get_assignment_service),
):
    try:
        assignment = assignment_service.create_assignment(
            assignment_data.user_id, assignment_data.chore_id, assignment_data.due_at
        )
        return assignment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/assignments/{assignment_id}",
    response_model=AssignmentResponse,
    tags=["Assignments"],
)
def update_assignment(
    assignment_id: int,
    assignment_data: AssignmentUpdate,
    assignment_service: AssignmentService = Depends(get_assignment_service),
):
    try:
        assignment = assignment_service.update_assignment_status(
            assignment_id, assignment_data.status
        )
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        return assignment
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/assignments/{assignment_id}", tags=["Assignments"])
def delete_assignment(
    assignment_id: int,
    assignment_service: AssignmentService = Depends(get_assignment_service),
):
    try:
        success = assignment_service.delete_assignment(assignment_id)
        if not success:
            raise HTTPException(status_code=404, detail="Assignment not found")
        return {"message": "Assignment deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
