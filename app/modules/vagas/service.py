from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.database.models import User, UserRole, JobOpening, JobStatus
from app.modules.vagas.schemas import JobCreate, JobUpdate


def create_job(job_data: JobCreate, db: Session, current_user: User):
    if not job_data.requirements or len([r for r in job_data.requirements if r.strip()]) == 0:
        raise HTTPException(status_code=400, detail="A vaga precisa ter pelo menos um requisito cadastrado.")

    recruiter = db.query(User).filter(User.id == job_data.recruiter_id, User.role == UserRole.RECRUTADOR).first()
    if not recruiter:
        raise HTTPException(status_code=400, detail="Recrutador responsável inválido.")

    new_job = JobOpening(
        title=job_data.title,
        description=job_data.description,
        requirements=";".join(job_data.requirements),
        recruiter_id=job_data.recruiter_id,
        status=JobStatus.ABERTA
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    return new_job


def list_jobs(db: Session):
    return db.query(JobOpening).all()


def get_job(job_id: int, db: Session):
    job = db.query(JobOpening).filter(JobOpening.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Vaga não encontrada.")
    return job


def update_job(job_id: int, job_update: JobUpdate, db: Session, current_user: User):
    job = db.query(JobOpening).filter(JobOpening.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Vaga não encontrada.")

    if job_update.title:
        job.title = job_update.title
    if job_update.description:
        job.description = job_update.description
    if job_update.status:
        job.status = job_update.status
    if job_update.requirements:
        reqs = [r for r in job_update.requirements if r.strip()]
        if not reqs:
            raise HTTPException(status_code=400, detail="A vaga precisa ter pelo menos um requisito válido.")
        job.requirements = ";".join(reqs)

    if job_update.recruiter_id:
        recruiter = db.query(User).filter(User.id == job_update.recruiter_id, User.role == UserRole.RECRUTADOR).first()
        if not recruiter:
            raise HTTPException(status_code=400, detail="Recrutador responsável inválido.")
        job.recruiter_id = job_update.recruiter_id

    db.commit()
    db.refresh(job)
    return job


def delete_job(job_id: int, db: Session, current_user: User):
    job = db.query(JobOpening).filter(JobOpening.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Vaga não encontrada.")
    
    db.delete(job)
    db.commit()
    return None
