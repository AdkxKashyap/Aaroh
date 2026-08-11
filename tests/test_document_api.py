import asyncio
import sys
import uuid
from pathlib import Path
from types import SimpleNamespace

sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))

from src.api.routers.document import create_document, get_document, get_document_versions
from src.models.document import Document
from src.models.document_version import DocumentVersion


class FakeDocumentService:
    def __init__(self):
        self.document = Document(
            id=uuid.uuid4(),
            school_id=uuid.uuid4(),
            uploaded_by=uuid.uuid4(),
            document_type="invoice",
            content_hash="hash-1",
            status="UPLOADED",
            current_version=1,
        )
        self.versions = [
            DocumentVersion(
                id=uuid.uuid4(),
                document_id=self.document.id,
                version=1,
                storage_key="storage-1",
            )
        ]

    async def create_document(self, **kwargs):
        return self.document

    async def get_document(self, document_id):
        return self.document if document_id == self.document.id else None

    async def get_versions(self, document_id):
        return self.versions if document_id == self.document.id else []


def test_create_document_endpoint():
    fake_service = FakeDocumentService()

    current_user = SimpleNamespace(id=uuid.uuid4(), school_id=uuid.uuid4())
    response = asyncio.run(
        create_document(
            request=SimpleNamespace(
                document_type="invoice",
                content_hash="hash-1",
                storage_key="storage-1",
            ),
            current_user=current_user,
            document_service=fake_service,
        )
    )

    assert response.document_type == "invoice"


def test_get_document_endpoint():
    fake_service = FakeDocumentService()
    current_user = SimpleNamespace(id=uuid.uuid4(), school_id=fake_service.document.school_id)

    response = asyncio.run(
        get_document(
            document_id=fake_service.document.id,
            current_user=current_user,
            document_service=fake_service,
        )
    )

    assert response.id == fake_service.document.id


def test_get_versions_endpoint():
    fake_service = FakeDocumentService()
    current_user = SimpleNamespace(id=uuid.uuid4(), school_id=fake_service.document.school_id)

    response = asyncio.run(
        get_document_versions(
            document_id=fake_service.document.id,
            current_user=current_user,
            document_service=fake_service,
        )
    )

    assert len(response) == 1
