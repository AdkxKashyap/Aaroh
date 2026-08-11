import uuid
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.enums.document_status import DocumentStatus
from src.models.base import BaseModel
from src.models.document_version import DocumentVersion


class Document(BaseModel):
    __tablename__ = "documents"

    school_id: Mapped[UUID] = mapped_column(
        ForeignKey("schools.id"),
        nullable=False,
    )

    uploaded_by: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    document_type: Mapped[str] = mapped_column(
        nullable=False,
    )

    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus),
        nullable=False,
        default=DocumentStatus.UPLOADED,
    )

    content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    current_version: Mapped[int] = mapped_column(
        nullable=False,
        default=1,
    )

    versions: Mapped[list["DocumentVersion"]] = relationship(
        "DocumentVersion",
        cascade="save-update, merge",
    )
