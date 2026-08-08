"""
Assignment Model

Responsibility:
    Represents an assignment created by a teacher.

MVP:
    - Targets one class
    - Created by one teacher

Future:
    - Individual student assignments
    - Group assignments
    - Approval workflow
    - Assignment state machine
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base import BaseModel
from src.models.school_class import SchoolClass
from src.models.user import User


class Assignment(BaseModel):
    __tablename__ = "assignments"

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    due_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    teacher_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    class_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("school_classes.id"),
        nullable=False,
    )

    teacher: Mapped["User"] = relationship(
        foreign_keys=[teacher_id],
    )

    school_class: Mapped["SchoolClass"] = relationship(
        foreign_keys=[class_id],
    )
