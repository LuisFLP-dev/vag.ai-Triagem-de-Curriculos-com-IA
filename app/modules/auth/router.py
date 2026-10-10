from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.security import get_current_user
from app.database.models import User
from app.database.connection import get_db
from app.modules.auth.schemas import RegisterRequest, Token
from app.modules.usuarios.schemas import UserResponse


from app.modules.auth import service


router = APIRouter()


@router.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: RegisterRequest, db: Session = Depends(get_db)):
    return service.register(user_data=user_data, db=db)


@router.post("/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    return service.login(form_data=form_data, db=db)


@router.get("/auth/me", response_model=UserResponse)
def current_profile(current_user: User = Depends(get_current_user)):
    """Perfil atual consultado no banco pela dependencia de autenticacao."""
    return current_user
