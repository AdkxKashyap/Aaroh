import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from src.enums.submission import SubmissionStatus


class SubmissionResponse(BaseModel):
    id: uuid.UUID
    assignment_id: uuid.UUID
    student_id: uuid.UUID
    status: SubmissionStatus
    submitted_at: datetime | None
    feedback: str | None = None
    assignment_name: str | None = None
    student_name: str | None = None
    class_name: str | None = None
    class_id: uuid.UUID | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class RevisionRequest(BaseModel):
    feedback: str
