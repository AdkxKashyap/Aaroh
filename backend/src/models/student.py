"""
Student Model

Responsibility:
    Represents a student within a school.

A Student is linked to:
    - one User account
    - one School
    - one SchoolClass
"""

import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.school import School
from src.models.school_class import SchoolClass
from src.models.user import User
from src.models.base import BaseModel


class Student(BaseModel):
    __tablename__ = "students"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        unique=True,
    )

    school_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("schools.id"),
        nullable=False,
    )

    class_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("school_classes.id"),
        nullable=False,
    )

    user: Mapped["User"] = relationship()

    school: Mapped["School"] = relationship()

    school_class: Mapped["SchoolClass"] = relationship()
    