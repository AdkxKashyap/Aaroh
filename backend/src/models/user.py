"""
User Model

Responsibility:
    Stores application users.
"""

from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base import BaseModel

from src.models.school import School


class User(BaseModel):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )
    """
    UserRole Model

    Responsibility:
        Represents the relationship between users and roles.
        Many-to-many relationship. One user can have multiple roles, and one role can be assigned to multiple users.
    """
    roles = relationship(
        "UserRole",
        back_populates="user",
    )

    """
    School this user belongs to.

    NULL:
        User has not registered/joined a school yet.
    """

    school_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("schools.id"),
        nullable=True,
    )
    """
    No relationship added for now.
    """
    school: Mapped["School | None"] = relationship()
