"""
School Model

Responsibility:
    Represents a school in the system.

Relationships:
    One School -> Many Classes
"""

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base import BaseModel

if TYPE_CHECKING:
    from src.models.school_class import SchoolClass


class School(BaseModel):
    __tablename__ = "schools"

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )

    address: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    classes: Mapped[list["SchoolClass"]] = relationship(
        back_populates="school",
        cascade="all, delete-orphan",
    )
