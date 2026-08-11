import uuid

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base import BaseModel
from src.models.student import Student
from src.models.user import User


class GuardianLink(BaseModel):
    __tablename__ = "guardian_links"

    guardian_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id"),
        nullable=False,
    )

    guardian_user: Mapped["User"] = relationship()
    student: Mapped["Student"] = relationship()

    __table_args__ = (
        UniqueConstraint(
            "guardian_user_id",
            "student_id",
            name="uq_guardian_student",
        ),
    )
