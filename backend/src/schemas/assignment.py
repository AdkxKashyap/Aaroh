"""
Assignment Schemas

Responsibility:
    Request and response models for assignment APIs.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from src.enums.assignment import AssignmentStatus


class CreateAssignmentRequest(BaseModel):
    title: str
    description: str
    due_date: datetime
    class_id: uuid.UUID


class AssignmentResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    due_date: datetime
    teacher_id: uuid.UUID
    class_id: uuid.UUID
    status: AssignmentStatus
    model_config = ConfigDict(
        from_attributes=True,
    )
