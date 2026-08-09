"""
Submission Model

Responsibility:
    Represents a student's submission for an assignment.

One Assignment can have many Submissions.
One Student can have many Submissions.

For the MVP:
    One student can have only one submission record
    per assignment. Resubmission updates that record.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from src.models.assignment import Assignment
from src.models.student import Student
from src.enums.submission import SubmissionStatus
from src.models.base import BaseModel


class Submission(BaseModel):
    __tablename__ = "submissions"

    __table_args__ = (
        UniqueConstraint(
            "assignment_id",
            "student_id",
            name="uq_submission_assignment_student",
        ),
    )

    assignment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assignments.id"),
        nullable=False,
    )

    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id"),
        nullable=False,
    )

    status: Mapped[SubmissionStatus] = mapped_column(
        default=SubmissionStatus.NOT_SUBMITTED,
        nullable=False,
    )

    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    assignment: Mapped["Assignment"] = relationship()

    student: Mapped["Student"] = relationship()