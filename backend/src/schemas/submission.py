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

    model_config = ConfigDict(
        from_attributes=True,
    )
