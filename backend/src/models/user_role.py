"""
UserRole Model

Responsibility:
    Maps users to roles.
"""

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel


class UserRole(BaseModel):
    __tablename__ = "user_roles"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    role_id: Mapped[UUID] = mapped_column(
        ForeignKey("roles.id"),
        nullable=False,
    )

    user = relationship(
        "User",
        back_populates="roles",
    )

    role = relationship(
        "Role",
        back_populates="users",
    )
