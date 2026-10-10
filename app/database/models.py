from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Enum as SQLEnum, ForeignKey, Text, Float, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database.connection import Base


class UserRole(str, Enum):
    GERENTE_RH = "GERENTE_RH"
    RECRUTADOR = "RECRUTADOR"
    CANDIDATO = "CANDIDATO"


class JobStatus(str, Enum):
    ABERTA = "ABERTA"
    CONCLUIDA = "CONCLUIDA"


class ApplicationStatus(str, Enum):
    PENDENTE = "PENDENTE"
    CONTRATADO = "CONTRATADO"
    REJEITADO = "REJEITADO"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False)
    full_name = Column(String, nullable=False)


class JobOpening(Base):
    __tablename__ = "job_openings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    requirements = Column(Text, nullable=False)
    status = Column(SQLEnum(JobStatus), default=JobStatus.ABERTA)
    recruiter_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    recruiter = relationship("User")
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("job_openings.id"), nullable=False)
    candidate_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    compatibility_score = Column(Float, nullable=False)
    ai_feedback = Column(Text, nullable=False)
    status = Column(SQLEnum(ApplicationStatus), default=ApplicationStatus.PENDENTE, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("JobOpening", back_populates="applications")
    candidate = relationship("User")

    __table_args__ = (
        UniqueConstraint('job_id', 'candidate_id', name='_candidate_job_uc'),
    )
