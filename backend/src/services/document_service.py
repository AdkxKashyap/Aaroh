"""
Document Service

Responsibility:
    Handles document lifecycle business logic.
"""

import uuid

from src.core.logger import logger
from src.db.transaction import transactional
from src.enums.document_status import DocumentStatus
from src.models.document import Document
from src.models.document_version import DocumentVersion
from src.repositories.document_repository import DocumentRepository
from src.repositories.document_version_repository import DocumentVersionRepository
from src.services.document_state_machine import DocumentStateMachine


class DocumentService:
    def __init__(
        self,
        document_repository: DocumentRepository,
        document_version_repository: DocumentVersionRepository,
        db,
    ):
        self.document_repository = document_repository
        self.document_version_repository = document_version_repository
        self.db = db

    async def create_document(
        self,
        school_id: uuid.UUID,
        uploaded_by: uuid.UUID,
        document_type: str,
        content_hash: str,
        storage_key: str,
    ) -> Document:
        logger.info(
            "Creating document",
            school_id=school_id,
            uploaded_by=uploaded_by,
            document_type=document_type,
            content_hash=content_hash,
        )

        existing = await self.document_repository.get_by_hash(school_id, content_hash)
        if existing is not None:
            logger.warning(
                "Duplicate document upload",
                school_id=school_id,
                content_hash=content_hash,
            )
            raise ValueError("Duplicate document detected for this school.")

        document = Document(
            school_id=school_id,
            uploaded_by=uploaded_by,
            document_type=document_type,
            content_hash=content_hash,
            status=DocumentStatus.UPLOADED,
            current_version=1,
        )
        version = DocumentVersion(
            version=1,
            storage_key=storage_key,
        )

        try:
            async with transactional(self.db):
                document = await self.document_repository.create(document)
                version.document_id = document.id
                version = await self.document_version_repository.create(version)

                logger.info(
                    "Document created",
                    document_id=document.id,
                    version_id=version.id,
                )

                return document
        except Exception:
            logger.exception(
                "Failed to create document",
                school_id=school_id,
                content_hash=content_hash,
            )
            raise

    async def get_document(self, document_id: uuid.UUID) -> Document | None:
        return await self.document_repository.get_by_id(document_id)

    async def get_versions(self, document_id: uuid.UUID) -> list[DocumentVersion]:
        document = await self.document_repository.get_by_id(document_id)
        if document is None:
            raise ValueError("Document not found.")
        return await self.document_version_repository.get_by_document(document_id)

    async def create_version(
        self,
        document_id: uuid.UUID,
        storage_key: str,
    ) -> DocumentVersion:
        document = await self.document_repository.get_by_id(document_id)
        if document is None:
            raise ValueError("Document not found.")

        next_version = document.current_version + 1
        version = DocumentVersion(
            document_id=document.id,
            version=next_version,
            storage_key=storage_key,
        )

        try:
            async with transactional(self.document_repository.db):
                version = await self.document_version_repository.create(version)
                document.current_version = next_version
                document = await self.document_repository.update(document)

                logger.info(
                    "Document version created",
                    document_id=document.id,
                    version=next_version,
                )

                return version
        except Exception:
            logger.exception(
                "Failed to create document version",
                document_id=document_id,
            )
            raise

    async def transition_status(
        self,
        document_id: uuid.UUID,
        target_status: DocumentStatus,
    ) -> Document:
        document = await self.document_repository.get_by_id(document_id)
        if document is None:
            raise ValueError("Document not found.")

        try:
            DocumentStateMachine.transition(document.status, target_status)
        except ValueError:
            logger.warning(
                "Invalid document transition",
                document_id=document.id,
                current_status=document.status,
                target_status=target_status,
            )
            raise ValueError("Invalid document transition.")

        document.status = target_status

        try:
            async with transactional(self.document_repository.db):
                document = await self.document_repository.update(document)

                logger.info(
                    "Document status transitioned",
                    document_id=document.id,
                    status=document.status,
                )

                return document
        except Exception:
            logger.exception(
                "Failed to transition document status",
                document_id=document.id,
                target_status=target_status,
            )
            raise
