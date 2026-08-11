"""
Document Repository

Responsibility:
    Handles persistence operations for Document.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logger import logger
from src.models.document import Document


class DocumentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, document: Document) -> Document:
        """Persist a new document."""
        try:
            self.db.add(document)
            await self.db.flush()
            await self.db.refresh(document)
            return document
        except SQLAlchemyError:
            logger.exception("Failed to create document", document_id=document.id)
            raise

    async def get_by_id(self, document_id: uuid.UUID) -> Document | None:
        """Return a document by id."""
        try:
            result = await self.db.execute(
                select(Document).where(Document.id == document_id)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError:
            logger.exception("Failed to fetch document", document_id=document_id)
            raise

    async def get_by_hash(self, school_id: uuid.UUID, content_hash: str) -> Document | None:
        """Find an existing document with the same school and hash."""
        try:
            result = await self.db.execute(
                select(Document).where(
                    Document.school_id == school_id,
                    Document.content_hash == content_hash,
                )
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError:
            logger.exception(
                "Failed to fetch document by hash",
                school_id=school_id,
                content_hash=content_hash,
            )
            raise

    async def update(self, document: Document) -> Document:
        """Persist changes to an existing document."""
        try:
            await self.db.flush()
            await self.db.refresh(document)
            return document
        except SQLAlchemyError:
            logger.exception("Failed to update document", document_id=document.id)
            raise
