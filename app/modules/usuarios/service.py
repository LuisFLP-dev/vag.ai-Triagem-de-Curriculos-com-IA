from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.database.models import User, UserRole, JobOpening, Application
from app.core.security import hash_password
from app.modules.usuarios.schemas import UserCreate, UserUpdate


def create_user(user_data: UserCreate, db: Session, current_user: User):
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Este e-mail já está em uso por outro usuário.")
    if not user_data.full_name.strip() or not user_data.password.strip():
        raise HTTPException(status_code=400, detail="Informe nome e senha válidos.")
    user = User(
        email=user_data.email,
        full_name=user_data.full_name.strip(),
        hashed_password=hash_password(user_data.password),
        role=user_data.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def list_users(db: Session, current_user: User):
    return db.query(User).all()


def get_user(user_id: int, db: Session, current_user: User):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return user


def update_user(user_id: int, user_update: UserUpdate, db: Session, current_user: User):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    if user_update.role and user_update.role != user.role:
        if user.id == current_user.id:
            raise HTTPException(status_code=400, detail="Não é possível alterar seu próprio papel.")
        if user.role == UserRole.RECRUTADOR and db.query(JobOpening).filter(JobOpening.recruiter_id == user.id).first():
            raise HTTPException(status_code=409, detail="Transfira as vagas deste recrutador antes de alterar seu papel.")

    if user_update.email and user_update.email != user.email:
        existing = db.query(User).filter(User.email == user_update.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Este e-mail já está em uso por outro usuário.")
        user.email = user_update.email

    if user_update.full_name:
        user.full_name = user_update.full_name
    if user_update.role:
        user.role = user_update.role
    if user_update.password:
        user.hashed_password = hash_password(user_update.password)

    db.commit()
    db.refresh(user)
    return user


def delete_user(user_id: int, db: Session, current_user: User):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Não é possível apagar a sua própria conta.")

    if db.query(JobOpening).filter(JobOpening.recruiter_id == user.id).first():
        raise HTTPException(status_code=409, detail="Transfira as vagas deste recrutador antes de excluí-lo.")
    if db.query(Application).filter(Application.candidate_id == user.id).first():
        raise HTTPException(status_code=409, detail="Este usuário possui candidaturas e não pode ser excluído para preservar o histórico.")

    db.delete(user)
    db.commit()
    return None
