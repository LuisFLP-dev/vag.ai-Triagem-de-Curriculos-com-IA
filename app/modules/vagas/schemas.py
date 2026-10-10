from typing import Annotated, List, Optional
from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from app.database.models import JobStatus


NonBlankText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Requirements = Annotated[List[NonBlankText], Field(min_length=1)]


class JobCreate(BaseModel):
    title: NonBlankText
    description: NonBlankText
    requirements: Requirements
    recruiter_id: int


class JobUpdate(BaseModel):
    title: Optional[NonBlankText] = None
    description: Optional[NonBlankText] = None
    requirements: Optional[Requirements] = None
    status: Optional[JobStatus] = None
    recruiter_id: Optional[int] = None


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    requirements: str
    status: JobStatus
    recruiter_id: int
