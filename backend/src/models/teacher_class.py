"""
Teacher Class Mapping

Responsibility:
    Maps teachers to the classes they teach.

A teacher can teach multiple classes.
A class can have multiple teachers.
"""

import uuid

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from src.models.base import BaseModel


class TeacherClass(BaseModel):
    __tablename__ = "teacher_classes"

    __table_args__ = (
        UniqueConstraint(
            "teacher_id",
            "class_id",
            name="uq_teacher_class",
        ),
    )

    teacher_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        ondelete="CASCADE",
    )

    class_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("school_classes.id"),
        nullable=False,
        ondelete="CASCADE",
    )
