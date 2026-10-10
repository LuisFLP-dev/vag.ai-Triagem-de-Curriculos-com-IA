from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, ConfigDict
from app.database.models import UserRole, JobStatus, ApplicationStatus


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    candidate_id: int
    compatibility_score: float
    ai_feedback: str
    status: ApplicationStatus
    created_at: datetime
