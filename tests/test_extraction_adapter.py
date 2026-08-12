import asyncio
import sys
import uuid
from pathlib import Path
from types import SimpleNamespace

sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))

from src.services.document_service import DocumentService
from src.services.extraction_adapter import ExtractionAdapter


class FakeStorage:
    def __init__(self):
        self.files = {
            "school-1/CLASS_ROSTER/abc123/roster.txt": b"Title: Science Club\nSubject: Biology\n",
        }

    async def store(self, *, file_bytes: bytes, storage_key: str) -> str:
        self.files[storage_key] = file_bytes
        return storage_key

    async def read(self, storage_key: str) -> bytes:
        return self.files[storage_key]

    async def delete(self, storage_key: str) -> None:
        self.files.pop(storage_key, None)


class FakeDocumentRepository:
    def __init__(self, document):
        self.document = document

    async def get_by_id(self, document_id):
        return self.document if self.document.id == document_id else None


class FakeDocumentVersionRepository:
    def __init__(self, version):
        self.version = version

    async def get_latest(self, document_id):
        return self.version if self.version.document_id == document_id else None


def test_extraction_adapter_prepares_clean_parser_input():
    text = ExtractionAdapter.prepare_parser_input(
        b"Title: Science Lab Report\nSubject: Biology\n",
        "brief.txt",
    )

    assert "Title: Science Lab Report" in text
    assert "Subject: Biology" in text
    assert "\n" not in text


def test_document_service_prepare_for_parsing_reads_latest_version_and_extracts_text():
    document_id = uuid.uuid4()
    document = SimpleNamespace(
        id=document_id,
        school_id=uuid.uuid4(),
    )
    version = SimpleNamespace(
        document_id=document_id,
        storage_key="school-1/CLASS_ROSTER/abc123/roster.txt",
    )

    service = DocumentService(
        document_repository=FakeDocumentRepository(document),
        document_version_repository=FakeDocumentVersionRepository(version),
        db=None,
        storage=FakeStorage(),
    )

    result = asyncio.run(service.prepare_for_parsing(document_id))

    assert result == "Title: Science Club Subject: Biology"
