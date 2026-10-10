from fastapi import HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database.models import User, UserRole
from app.core.security import hash_password, verify_password, create_access_token
from app.modules.auth.schemas import RegisterRequest


def register(user_data: RegisterRequest, db: Session):
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="E-mail já cadastrado.")
    
    hashed_pwd = hash_password(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_pwd,
        full_name=user_data.full_name,
        role=UserRole.CANDIDATO
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def login(form_data: OAuth2PasswordRequestForm, db: Session):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="E-mail ou senha incorretos.")
    
    access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}
