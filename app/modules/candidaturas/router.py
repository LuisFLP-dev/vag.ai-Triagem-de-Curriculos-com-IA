from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models import User, UserRole
from app.core.security import require_roles
from app.modules.candidaturas.schemas import ApplicationStatusUpdate


from app.modules.candidaturas import service


router = APIRouter()


@router.post("/vagas/{job_id}/candidatar")
def apply_to_job(
    job_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.CANDIDATO]))
):
    return service.apply_to_job(job_id=job_id, file=file, db=db, current_user=current_user)


@router.get("/minhas-candidaturas")
def list_my_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.CANDIDATO]))
):
    return service.list_my_applications(db=db, current_user=current_user)


@router.get("/vagas/{job_id}/candidatos")
def get_job_candidates(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.RECRUTADOR, UserRole.GERENTE_RH]))
):
    return service.get_job_candidates(job_id=job_id, db=db, current_user=current_user)


@router.patch("/candidaturas/{application_id}/status")
def update_application_status(
    application_id: int,
    payload: ApplicationStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.RECRUTADOR, UserRole.GERENTE_RH]))
):
    return service.update_application_status(application_id=application_id, payload=payload, db=db, current_user=current_user)
