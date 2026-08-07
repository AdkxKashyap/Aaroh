"""
Role Model

Responsibility:
    Represents a user role.
"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel


class Role(BaseModel):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
    )
    """
    UserRole Model

    Responsibility:
        Represents the relationship between users and roles.
        Many-to-many relationship. One user can have multiple roles, and one role can be assigned to multiple users.
    """
    users = relationship(
        "UserRole",
        back_populates="role",
    )