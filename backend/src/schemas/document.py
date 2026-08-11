"""
Document Schemas

Responsibility:
    Request and response models for document APIs.
"""

import uuid

from pydantic import BaseModel, ConfigDict
from src.enums.document_status import DocumentStatus


class CreateDocumentRequest(BaseModel):
    document_type: str
    content_hash: str | None = None
    storage_key: str | None = None


class DocumentResponse(BaseModel):
    id: uuid.UUID
    school_id: uuid.UUID
    uploaded_by: uuid.UUID
    document_type: str
    status: DocumentStatus
    content_hash: str
    current_version: int

    model_config = ConfigDict(from_attributes=True)


class DocumentVersionResponse(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    version: int
    storage_key: str

    model_config = ConfigDict(from_attributes=True)
