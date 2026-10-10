from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models import User, UserRole
from app.core.security import require_roles
from app.modules.usuarios.schemas import UserCreate, UserUpdate, UserResponse


from app.modules.usuarios import service


router = APIRouter()


@router.post("/usuarios", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.GERENTE_RH]))
):
    return service.create_user(user_data=user_data, db=db, current_user=current_user)


@router.get("/usuarios", response_model=List[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.GERENTE_RH]))
):
    return service.list_users(db=db, current_user=current_user)


@router.get("/usuarios/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.GERENTE_RH]))
):
    return service.get_user(user_id=user_id, db=db, current_user=current_user)


@router.put("/usuarios/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.GERENTE_RH]))
):
    return service.update_user(user_id=user_id, user_update=user_update, db=db, current_user=current_user)


@router.delete("/usuarios/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.GERENTE_RH]))
):
    return service.delete_user(user_id=user_id, db=db, current_user=current_user)
