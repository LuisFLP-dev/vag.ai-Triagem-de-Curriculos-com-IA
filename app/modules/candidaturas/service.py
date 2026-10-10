from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.database.models import User, UserRole, JobOpening, JobStatus, Application, ApplicationStatus
from app.modules.candidaturas.schemas import ApplicationStatusUpdate
from app.integrations.gemini import evaluate_resume_with_gemini


def apply_to_job(job_id: int, file: UploadFile, db: Session, current_user: User):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="O currículo deve ser um arquivo PDF.")

    job = db.query(JobOpening).filter(JobOpening.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Vaga não encontrada.")

    if job.status == JobStatus.CONCLUIDA:
        raise HTTPException(status_code=400, detail="Esta vaga já foi concluída e não aceita novas candidaturas.")

   
    existing_application = db.query(Application).filter(
        Application.job_id == job_id,
        Application.candidate_id == current_user.id
    ).first()
    if existing_application:
        raise HTTPException(status_code=400, detail="Você já se candidatou a esta vaga.")

    pdf_bytes = file.file.read()
    requirements_list = job.requirements.split(";")
    ai_result = evaluate_resume_with_gemini(pdf_bytes, requirements_list)

    application = Application(
        job_id=job.id,
        candidate_id=current_user.id,
        compatibility_score=ai_result["score"],
        ai_feedback=ai_result["reasoning"],
        status=ApplicationStatus.PENDENTE
    )
    db.add(application)
    db.commit()

    return {
        "message": "Candidatura realizada com sucesso!",
    }


def list_my_applications(db: Session, current_user: User):
    applications = db.query(Application).filter(Application.candidate_id == current_user.id).all()
    return [
        {
            "vaga_id": app.job_id,
            "titulo_vaga": app.job.title,
            "status_vaga": app.job.status,
            "status_candidatura": app.status,
            "data": app.created_at
        } for app in applications
    ]


def get_job_candidates(job_id: int, db: Session, current_user: User):
    job = db.query(JobOpening).filter(JobOpening.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Vaga não encontrada.")

    if current_user.role == UserRole.RECRUTADOR and job.recruiter_id != current_user.id:
        raise HTTPException(
            status_code=403, 
            detail="Acesso negado: Você não é o recrutador responsável por esta vaga."
        )

    applications = db.query(Application)\
        .filter(Application.job_id == job_id)\
        .order_by(Application.compatibility_score.desc())\
        .all()

    return [
        {
            "candidatura_id": app.id,
            "candidato_id": app.candidate_id,
            "candidato_nome": app.candidate.full_name,
            "candidato_email": app.candidate.email,
            "pontuacao_compatibilidade": app.compatibility_score,
            "parecer_ia": app.ai_feedback,
            "status_candidatura": app.status,
            "data_candidatura": app.created_at
        } for app in applications
    ]


def update_application_status(application_id: int, payload: ApplicationStatusUpdate, db: Session, current_user: User):
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Candidatura não encontrada.")

   
    if current_user.role == UserRole.RECRUTADOR and application.job.recruiter_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Acesso negado: Você não é o recrutador responsável por esta vaga."
        )

    if payload.status not in [ApplicationStatus.CONTRATADO, ApplicationStatus.REJEITADO]:
        raise HTTPException(
            status_code=400,
            detail="O status da candidatura deve ser alterado para 'CONTRATADO' ou 'REJEITADO'."
        )

    
    application.status = payload.status
    db.commit()
    db.refresh(application)

    return {
        "message": f"Candidato marcado como {payload.status.value} com sucesso.",
        "candidatura_id": application.id,
        "novo_status": application.status
    }
