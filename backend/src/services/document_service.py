"""
Document Service

Responsibility:
    Handles document lifecycle business logic.
"""

import hashlib
import uuid
from pathlib import Path

from src.config.settings import get_settings
from src.core.logger import logger
from src.db.transaction import transactional
from src.enums.document_status import DocumentStatus
from src.enums.document_type import DocumentType
from src.enums.role import RoleName
from src.models.document import Document
from src.models.document_version import DocumentVersion
from src.models.user import User
from src.repositories.document_repository import DocumentRepository
from src.repositories.document_version_repository import DocumentVersionRepository
from src.repositories.teacher_class_repository import TeacherClassRepository
from src.services.document_state_machine import DocumentStateMachine
from src.services.extraction_adapter import ExtractionAdapter
from src.services.storage import FileStorage, LocalFileStorage


class DocumentService:
    def __init__(
        self,
        document_repository: DocumentRepository,
        document_version_repository: DocumentVersionRepository,
        db,
        storage: FileStorage | None = None,
        teacher_class_repository: TeacherClassRepository | None = None,
    ):
        self.document_repository = document_repository
        self.document_version_repository = document_version_repository
        self.db = db
        self.storage = storage or LocalFileStorage()
        self.teacher_class_repository = teacher_class_repository

    def _sanitize_filename(self, filename: str) -> str:
        safe_name = Path(filename).name
        safe_name = safe_name.replace(" ", "_")
        safe_name = "".join(
            char for char in safe_name if char.isalnum() or char in {"_", "-", "."}
        )
        return safe_name or "upload"

    def _build_storage_key(
        self,
        school_id: uuid.UUID,
        document_type: str,
        content_hash: str,
        original_filename: str,
    ) -> str:
        sanitized_name = self._sanitize_filename(original_filename)
        return f"{school_id}/{document_type}/{content_hash}/{sanitized_name}"

    async def _store_upload(
        self,
        file_bytes: bytes,
        content_hash: str,
        storage_key: str | None,
    ) -> tuple[str, str]:
        stored_path = await self.storage.store(
            file_bytes=file_bytes,
            storage_key=storage_key,
        )

        return content_hash, stored_path

    def _validate_upload(self, file_bytes: bytes, original_filename: str) -> None:
        settings = get_settings()
        max_size = settings.MAX_UPLOAD_SIZE_BYTES
        allowed_extensions = {
            item.strip().lower()
            for item in settings.ALLOWED_UPLOAD_EXTENSIONS.split(",")
            if item.strip()
        }

        if not file_bytes:
            raise ValueError("Uploaded file is empty.")

        if len(file_bytes) > max_size:
            raise ValueError("Uploaded file exceeds the configured size limit.")

        suffix = Path(original_filename).suffix.lower()
        if suffix not in allowed_extensions:
            raise ValueError(
                f"Only the following file types are allowed: {', '.join(allowed_extensions)}."
            )

    def _normalize_role_names(self, current_user: User | None) -> set[str]:
        if current_user is None:
            return set()

        roles: set[str] = set()
        for user_role in getattr(current_user, "roles", []) or []:
            role_name = getattr(getattr(user_role, "role", None), "name", None)
            if role_name:
                roles.add(role_name)
        return roles

    async def _validate_document_type_and_authorization(
        self,
        document_type: DocumentType,
        current_user: User | None,
        class_id: uuid.UUID | None = None,
    ) -> None:
        if current_user is None:
            return

        if document_type == DocumentType.CLASS_ROSTER:
            if RoleName.ADMIN not in self._normalize_role_names(current_user):
                raise ValueError("Only admins can upload class rosters.")
            return

        if document_type == DocumentType.ASSIGNMENT_BRIEF:
            if RoleName.TEACHER not in self._normalize_role_names(current_user):
                raise ValueError("Only teachers can upload assignment briefs.")
            if class_id is None:
                raise ValueError("Assignment brief requires a class_id.")
            if self.teacher_class_repository is None:
                raise ValueError("Teacher class mapping repository is not configured.")

            teacher_id = getattr(current_user, "id", None)
            if teacher_id is None:
                raise ValueError("Authenticated teacher is required.")

            mapping = await self.teacher_class_repository.get(teacher_id, class_id)
            if mapping is None:
                raise ValueError("Teacher is not assigned to this class.")
            return

        raise ValueError("Unsupported document type.")

    async def create_document(
        self,
        school_id: uuid.UUID,
        uploaded_by: uuid.UUID,
        document_type: DocumentType | str,
        file=None,
        current_user: User | None = None,
        class_id: uuid.UUID | None = None,
        content_hash: str | None = None,
        storage_key: str | None = None,
        file_bytes: bytes | None = None,
        original_filename: str | None = None,
    ) -> Document:
        if file is not None:
            if file_bytes is None:
                file_bytes = await file.read()
            if original_filename is None:
                original_filename = getattr(file, "filename", None) or "upload"
        elif file_bytes is None and content_hash is None:
            raise ValueError("A file upload is required.")

        if original_filename is None:
            original_filename = "upload"

        should_validate_document_type = file is not None or file_bytes is not None
        normalized_document_type = document_type
        if should_validate_document_type:
            try:
                normalized_document_type = DocumentType(str(document_type).upper())
            except ValueError as exc:
                raise ValueError("Unsupported document type.") from exc

            await self._validate_document_type_and_authorization(
                normalized_document_type,
                current_user,
                class_id,
            )

        if file_bytes is not None:
            self._validate_upload(file_bytes, original_filename)
            content_hash = content_hash or hashlib.sha256(file_bytes).hexdigest()

        if storage_key is None and content_hash is not None:
            storage_key = self._build_storage_key(
                school_id=school_id,
                document_type=str(normalized_document_type),
                content_hash=content_hash,
                original_filename=original_filename,
            )

        if content_hash is None:
            raise ValueError("Document content hash is required.")

        logger.info(
            "Creating document",
            school_id=school_id,
            uploaded_by=uploaded_by,
            document_type=normalized_document_type,
            content_hash=content_hash,
        )
        # TODO: cache hashes to avoid db hit for duplicates
        existing = await self.document_repository.get_by_hash(school_id, content_hash)
        if existing is not None:
            logger.warning(
                "Duplicate document upload",
                school_id=school_id,
                content_hash=content_hash,
            )
            raise ValueError("Duplicate document detected for this school.")

        stored_storage_key = storage_key
        if file_bytes is not None:
            try:
                _, stored_storage_key = await self._store_upload(
                    file_bytes=file_bytes,
                    content_hash=content_hash,
                    storage_key=storage_key,
                )
            except Exception:
                logger.exception(
                    "Failed to store uploaded document",
                    school_id=school_id,
                    content_hash=content_hash,
                )
                raise

        document = Document(
            school_id=school_id,
            uploaded_by=uploaded_by,
            document_type=normalized_document_type,
            content_hash=content_hash,
            status=DocumentStatus.UPLOADED,
            current_version=1,
        )
        version = DocumentVersion(
            version=1,
            storage_key=stored_storage_key,
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

    async def get_document(
        self, document_id: uuid.UUID, current_user: User | None = None
    ) -> Document | None:
        doc = await self.document_repository.get_by_id(document_id)
        if doc is None:
            return None
        if current_user is not None and doc.school_id != current_user.school_id:
            raise ValueError("Access denied to this document.")
        return doc

    async def get_versions(
        self, document_id: uuid.UUID, current_user: User | None = None
    ) -> list[DocumentVersion]:
        document = await self.document_repository.get_by_id(document_id)
        if document is None:
            raise ValueError("Document not found.")
        if current_user is not None and document.school_id != current_user.school_id:
            raise ValueError("Access denied to this document.")
        return await self.document_version_repository.get_by_document(document_id)

    async def create_version(
        self,
        document_id: uuid.UUID,
        storage_key: str,
        current_user: User | None = None,
    ) -> DocumentVersion:
        document = await self.document_repository.get_by_id(document_id)
        if document is None:
            raise ValueError("Document not found.")
        if current_user is not None and document.school_id != current_user.school_id:
            raise ValueError("Access denied to this document.")
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

    async def prepare_for_parsing(
        self,
        document_id: uuid.UUID,
        current_user: User | None = None,
    ) -> str:
        document = await self.document_repository.get_by_id(document_id)
        if document is None:
            raise ValueError("Document not found.")
        if current_user is not None and document.school_id != current_user.school_id:
            raise ValueError("Access denied to this document.")

        latest_version = await self.document_version_repository.get_latest(document_id)
        if latest_version is None:
            raise ValueError("Document version not found.")

        file_bytes = await self.storage.read(latest_version.storage_key)
        if file_bytes is None:
            raise ValueError("Document content could not be read.")

        return ExtractionAdapter.prepare_parser_input(
            file_bytes,
            latest_version.storage_key,
        )

    async def extract_text(
        self,
        document_id: uuid.UUID,
        current_user: User | None = None,
    ) -> str:
        document = await self.document_repository.get_by_id(document_id)
        if document is None:
            raise ValueError("Document not found.")
        if current_user is not None and document.school_id != current_user.school_id:
            raise ValueError("Access denied to this document.")

        latest_version = await self.document_version_repository.get_latest(document_id)
        if latest_version is None:
            raise ValueError("Document version not found.")

        file_bytes = await self.storage.read(latest_version.storage_key)
        if file_bytes is None:
            raise ValueError("Document content could not be read.")

        return ExtractionAdapter.extract_text(file_bytes, latest_version.storage_key)

    async def transition_status(
        self,
        document_id: uuid.UUID,
        target_status: DocumentStatus,
        current_user: User | None = None,
    ) -> Document:
        document = await self.document_repository.get_by_id(document_id)
        if document is None:
            raise ValueError("Document not found.")
        if current_user is not None and document.school_id != current_user.school_id:
            raise ValueError("Access denied to this document.")

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

    async def begin_parsing(self, document_id, current_user: User) -> Document:
        return await self.transition_status(
            document_id=document_id,
            target_status=DocumentStatus.PARSING,
            current_user=current_user,
        )
