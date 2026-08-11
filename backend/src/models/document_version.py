import uuid
from uuid import UUID

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from src.models.base import BaseModel


class DocumentVersion(BaseModel):
    __tablename__ = "document_versions"
    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "version",
            name="uq_document_version",
        ),
    )

    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id"),
        nullable=False,
    )

    version: Mapped[int] = mapped_column(
        nullable=False,
    )

    storage_key: Mapped[str] = mapped_column(
        nullable=False,
    )

    parsed_output: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    confidence_notes: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )
