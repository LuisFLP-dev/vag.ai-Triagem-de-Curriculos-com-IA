from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models import User, UserRole
from app.core.security import require_roles
from app.modules.vagas.schemas import JobCreate, JobUpdate, JobResponse


from app.modules.vagas import service


router = APIRouter()


@router.post("/vagas", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(
    job_data: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.GERENTE_RH]))
):
    return service.create_job(job_data=job_data, db=db, current_user=current_user)


@router.get("/vagas", response_model=List[JobResponse])
def list_jobs(db: Session = Depends(get_db)):
    return service.list_jobs(db=db)


@router.get("/vagas/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    return service.get_job(job_id=job_id, db=db)


@router.put("/vagas/{job_id}", response_model=JobResponse)
def update_job(
    job_id: int,
    job_update: JobUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.GERENTE_RH]))
):
    return service.update_job(job_id=job_id, job_update=job_update, db=db, current_user=current_user)


@router.delete("/vagas/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.GERENTE_RH]))
):
    return service.delete_job(job_id=job_id, db=db, current_user=current_user)
