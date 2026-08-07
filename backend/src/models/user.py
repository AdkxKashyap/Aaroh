"""
User Model

Responsibility:
    Stores application users.
"""

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel


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