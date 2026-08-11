"""
Document Version Repository

Responsibility:
    Handles persistence operations for DocumentVersion.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logger import logger
from src.models.document_version import DocumentVersion


class DocumentVersionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, version: DocumentVersion) -> DocumentVersion:
        """Persist a new document version."""
        try:
            self.db.add(version)
            await self.db.flush()
            await self.db.refresh(version)
            return version
        except SQLAlchemyError:
            logger.exception("Failed to create document version", version_id=version.id)
            raise

    async def get_by_document(self, document_id: uuid.UUID) -> list[DocumentVersion]:
        """Return all versions for a document ordered by version number."""
        try:
            result = await self.db.execute(
                select(DocumentVersion)
                .where(DocumentVersion.document_id == document_id)
                .order_by(DocumentVersion.version.asc())
            )
            return list(result.scalars().all())
        except SQLAlchemyError:
            logger.exception("Failed to fetch document versions", document_id=document_id)
            raise

    async def get_latest(self, document_id: uuid.UUID) -> DocumentVersion | None:
        """Return the latest version for a document."""
        try:
            result = await self.db.execute(
                select(DocumentVersion)
                .where(DocumentVersion.document_id == document_id)
                .order_by(DocumentVersion.version.desc())
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError:
            logger.exception("Failed to fetch latest document version", document_id=document_id)
            raise
