"""
School Class Model

Responsibility:
    Represents a class/grade inside a school.

Examples:
    Grade 1
    Grade 5-A
    Class 10-B

Relationships:
    Many Classes -> One School
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base import BaseModel

if TYPE_CHECKING:
    from src.models.school import School


class SchoolClass(BaseModel):
    __tablename__ = ("school_classes",)
    __table_args__ = (
        UniqueConstraint(
            "school_id",
            "name",
            name="uq_school_class_name",
        ),
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    school_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("schools.id"),
        nullable=False,
    )

    school: Mapped["School"] = relationship(
        back_populates="classes",
    )
