import asyncio
import hashlib
import sys
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))

from src.enums.document_status import DocumentStatus
from src.models.document import Document
from src.models.document_version import DocumentVersion
from src.services.document_service import DocumentService


class FakeDB:
    def __init__(self):
        self.info = {}
        self.commit_calls = 0
        self.rollback_calls = 0
        self._rollback_state = {}

    def in_transaction(self):
        return self.info.get("service_transaction_depth", 0) > 0

    async def commit(self):
        self.commit_calls += 1
        self.info["service_transaction_depth"] = 0
        for restore in self._rollback_state.values():
            restore(commit=True)

    async def rollback(self):
        self.rollback_calls += 1
        self.info["service_transaction_depth"] = 0
        for restore in self._rollback_state.values():
            restore(commit=False)

    async def flush(self):
        return None

    async def refresh(self, obj):
        return None

    def register_rollback_hook(self, key, hook):
        self._rollback_state[key] = hook


class FakeDocumentRepository:
    def __init__(self, db):
        self.db = db
        self.documents = {}
        self._snapshot = None
        self._transaction_active = False
        self.db.register_rollback_hook(id(self), self._rollback)

    def _rollback(self, commit=False):
        if not commit and self._snapshot is not None:
            self.documents = self._snapshot.copy()
        elif commit:
            self._snapshot = None
        else:
            self.documents = {}
        self._transaction_active = False

    async def create(self, document):
        if (
            self.db.info.get("service_transaction_depth", 0) > 0
            and not self._transaction_active
        ):
            self._transaction_active = True
            self._snapshot = dict(self.documents)

        if document.id is None:
            document.id = uuid.uuid4()
        self.documents[document.id] = document
        await self.db.flush()
        await self.db.refresh(document)
        return document

    async def get_by_id(self, document_id):
        return self.documents.get(document_id)

    async def get_by_hash(self, school_id, content_hash):
        for document in self.documents.values():
            if (
                document.school_id == school_id
                and document.content_hash == content_hash
            ):
                return document
        return None

    async def update(self, document):
        if (
            self.db.info.get("service_transaction_depth", 0) > 0
            and not self._transaction_active
        ):
            self._transaction_active = True
            self._snapshot = dict(self.documents)

        self.documents[document.id] = document
        await self.db.flush()
        await self.db.refresh(document)
        return document

    async def flush(self):
        return None

    async def refresh(self, document):
        return None


class FakeDocumentVersionRepository:
    def __init__(self, db):
        self.db = db
        self.versions = {}
        self.by_document = {}
        self._snapshot = None
        self._transaction_active = False
        self.db.register_rollback_hook(id(self), self._rollback)

    def _rollback(self, commit=False):
        if not commit and self._snapshot is not None:
            self.versions = self._snapshot[0].copy()
            self.by_document = self._snapshot[1].copy()
        elif commit:
            self._snapshot = None
        else:
            self.versions = {}
            self.by_document = {}
        self._transaction_active = False

    async def create(self, version):
        if (
            self.db.info.get("service_transaction_depth", 0) > 0
            and not self._transaction_active
        ):
            self._transaction_active = True
            self._snapshot = (
                dict(self.versions),
                {
                    document_id: list(versions)
                    for document_id, versions in self.by_document.items()
                },
            )

        if version.id is None:
            version.id = uuid.uuid4()
        self.versions[version.id] = version
        self.by_document.setdefault(version.document_id, []).append(version)
        await self.db.flush()
        await self.db.refresh(version)
        return version

    async def get_by_document(self, document_id):
        return sorted(
            self.by_document.get(document_id, []),
            key=lambda item: item.version,
        )

    async def get_latest(self, document_id):
        versions = self.get_by_document(document_id)
        return versions[-1] if versions else None

    async def flush(self):
        return None

    async def refresh(self, version):
        return None


class FakeTeacherClassRepository:
    def __init__(self, db):
        self.db = db
        self.mappings = {}

    async def get(self, teacher_id, class_id):
        return self.mappings.get((teacher_id, class_id))


@pytest.fixture
def document_service():
    db = FakeDB()
    document_repository = FakeDocumentRepository(db)
    version_repository = FakeDocumentVersionRepository(db)
    teacher_class_repository = FakeTeacherClassRepository(db)
    service = DocumentService(
        document_repository=document_repository,
        document_version_repository=version_repository,
        db=db,
        teacher_class_repository=teacher_class_repository,
    )
    return service, document_repository, version_repository, db


def test_create_document_creates_document_and_initial_version(document_service):
    service, document_repository, version_repository, _ = document_service

    created = asyncio.run(
        service.create_document(
            school_id=uuid.uuid4(),
            uploaded_by=uuid.uuid4(),
            document_type="invoice",
            content_hash="hash-1",
            storage_key="storage-1",
        )
    )

    assert created.id is not None
    assert created.status == DocumentStatus.UPLOADED
    assert asyncio.run(document_repository.get_by_id(created.id)) is not None
    assert len(asyncio.run(version_repository.get_by_document(created.id))) == 1


def test_create_document_creates_initial_version_number_one(document_service):
    service, _, version_repository, _ = document_service

    created = asyncio.run(
        service.create_document(
            school_id=uuid.uuid4(),
            uploaded_by=uuid.uuid4(),
            document_type="invoice",
            content_hash="hash-2",
            storage_key="storage-2",
        )
    )

    versions = asyncio.run(version_repository.get_by_document(created.id))
    assert versions[0].version == 1


def test_new_document_starts_in_uploaded_state(document_service):
    service, _, _, _ = document_service

    created = asyncio.run(
        service.create_document(
            school_id=uuid.uuid4(),
            uploaded_by=uuid.uuid4(),
            document_type="invoice",
            content_hash="hash-3",
            storage_key="storage-3",
        )
    )

    assert created.status == DocumentStatus.UPLOADED


def test_create_document_uses_uploaded_bytes_for_hash_and_storage_key(document_service):
    service, _, _, _ = document_service

    file_bytes = b"class roster content"
    created = asyncio.run(
        service.create_document(
            school_id=uuid.uuid4(),
            uploaded_by=uuid.uuid4(),
            document_type="class_roster",
            file_bytes=file_bytes,
            original_filename="Roster.pdf",
        )
    )

    assert created.content_hash == hashlib.sha256(file_bytes).hexdigest()
    assert created.current_version == 1
    assert created.status == DocumentStatus.UPLOADED
    assert created.content_hash != ""


def test_duplicate_document_within_same_school_is_rejected(document_service):
    service, _, _, _ = document_service

    school_id = uuid.uuid4()
    asyncio.run(
        service.create_document(
            school_id=school_id,
            uploaded_by=uuid.uuid4(),
            document_type="invoice",
            content_hash="hash-duplicate",
            storage_key="storage-a",
        )
    )

    with pytest.raises(ValueError, match="Duplicate"):
        asyncio.run(
            service.create_document(
                school_id=school_id,
                uploaded_by=uuid.uuid4(),
                document_type="invoice",
                content_hash="hash-duplicate",
                storage_key="storage-b",
            )
        )


def test_same_hash_in_different_school_is_not_treated_as_duplicate(document_service):
    service, _, _, _ = document_service

    asyncio.run(
        service.create_document(
            school_id=uuid.uuid4(),
            uploaded_by=uuid.uuid4(),
            document_type="invoice",
            content_hash="shared-hash",
            storage_key="storage-a",
        )
    )

    created = asyncio.run(
        service.create_document(
            school_id=uuid.uuid4(),
            uploaded_by=uuid.uuid4(),
            document_type="invoice",
            content_hash="shared-hash",
            storage_key="storage-b",
        )
    )

    assert created.content_hash == "shared-hash"


def test_get_document_returns_requested_document(document_service):
    service, _, _, _ = document_service

    created = asyncio.run(
        service.create_document(
            school_id=uuid.uuid4(),
            uploaded_by=uuid.uuid4(),
            document_type="invoice",
            content_hash="hash-4",
            storage_key="storage-4",
        )
    )

    fetched = asyncio.run(service.get_document(created.id))

    assert fetched is not None
    assert fetched.id == created.id


def test_get_versions_returns_versions_for_document(document_service):
    service, _, _, _ = document_service

    created = asyncio.run(
        service.create_document(
            school_id=uuid.uuid4(),
            uploaded_by=uuid.uuid4(),
            document_type="invoice",
            content_hash="hash-5",
            storage_key="storage-5",
        )
    )

    versions = asyncio.run(service.get_versions(created.id))

    assert len(versions) == 1
    assert versions[0].version == 1


def test_create_version_creates_version_two_and_updates_current_version(
    document_service,
):
    service, _, _, _ = document_service

    created = asyncio.run(
        service.create_document(
            school_id=uuid.uuid4(),
            uploaded_by=uuid.uuid4(),
            document_type="invoice",
            content_hash="hash-6",
            storage_key="storage-6",
        )
    )

    version = asyncio.run(service.create_version(created.id, "storage-7"))

    assert version.version == 2
    refreshed = asyncio.run(service.get_document(created.id))
    assert refreshed.current_version == 2


def test_previous_versions_remain_available(document_service):
    service, _, _, _ = document_service

    created = asyncio.run(
        service.create_document(
            school_id=uuid.uuid4(),
            uploaded_by=uuid.uuid4(),
            document_type="invoice",
            content_hash="hash-7",
            storage_key="storage-8",
        )
    )

    asyncio.run(service.create_version(created.id, "storage-9"))
    versions = asyncio.run(service.get_versions(created.id))

    assert len(versions) == 2
    assert versions[0].version == 1
    assert versions[1].version == 2


def test_create_version_for_nonexistent_document_fails(document_service):
    service, _, _, _ = document_service

    with pytest.raises(ValueError, match="not found"):
        asyncio.run(service.create_version(uuid.uuid4(), "storage-10"))


def test_valid_state_transition_succeeds(document_service):
    service, _, _, _ = document_service

    created = asyncio.run(
        service.create_document(
            school_id=uuid.uuid4(),
            uploaded_by=uuid.uuid4(),
            document_type="invoice",
            content_hash="hash-8",
            storage_key="storage-11",
        )
    )

    updated = asyncio.run(service.transition_status(created.id, DocumentStatus.PARSING))

    assert updated.status == DocumentStatus.PARSING


def test_invalid_state_transition_fails(document_service):
    service, _, _, _ = document_service

    created = asyncio.run(
        service.create_document(
            school_id=uuid.uuid4(),
            uploaded_by=uuid.uuid4(),
            document_type="invoice",
            content_hash="hash-9",
            storage_key="storage-12",
        )
    )

    with pytest.raises(ValueError, match="transition"):
        asyncio.run(service.transition_status(created.id, DocumentStatus.APPROVED))


def test_create_document_is_atomic(document_service):
    service, document_repository, version_repository, _ = document_service

    class FailingVersionRepo(FakeDocumentVersionRepository):
        async def create(self, version):
            raise RuntimeError("boom")

    service.document_version_repository = FailingVersionRepo(
        service.document_version_repository.db
    )

    with pytest.raises(RuntimeError):
        asyncio.run(
            service.create_document(
                school_id=uuid.uuid4(),
                uploaded_by=uuid.uuid4(),
                document_type="invoice",
                content_hash="hash-10",
                storage_key="storage-13",
            )
        )

    assert len(document_repository.documents) == 0
    assert len(version_repository.versions) == 0


def test_create_version_is_atomic(document_service):
    service, document_repository, version_repository, _ = document_service

    class FailingDocumentRepo(FakeDocumentRepository):
        async def update(self, document):
            raise RuntimeError("boom")

    service.document_repository = FailingDocumentRepo(service.document_repository.db)

    created = asyncio.run(
        service.create_document(
            school_id=uuid.uuid4(),
            uploaded_by=uuid.uuid4(),
            document_type="invoice",
            content_hash="hash-11",
            storage_key="storage-14",
        )
    )

    with pytest.raises(RuntimeError):
        asyncio.run(service.create_version(created.id, "storage-15"))

    assert len(version_repository.versions) == 1


def test_repositories_do_not_commit_independently(document_service):
    service, _, _, db = document_service

    asyncio.run(
        service.create_document(
            school_id=uuid.uuid4(),
            uploaded_by=uuid.uuid4(),
            document_type="invoice",
            content_hash="hash-12",
            storage_key="storage-16",
        )
    )

    assert db.commit_calls == 1


def test_assignment_brief_requires_teacher_assignment(document_service):
    service, _, _, _ = document_service

    class FakeUploadFile:
        filename = "Brief.pdf"

        async def read(self):
            return b"assignment brief"

    current_user = SimpleNamespace(
        id=uuid.uuid4(),
        school_id=uuid.uuid4(),
        roles=[SimpleNamespace(role=SimpleNamespace(name="TEACHER"))],
    )

    with pytest.raises(ValueError, match="assigned to this class"):
        asyncio.run(
            service.create_document(
                school_id=current_user.school_id,
                uploaded_by=current_user.id,
                document_type="assignment_brief",
                file=FakeUploadFile(),
                current_user=current_user,
                class_id=uuid.uuid4(),
            )
        )


def test_unsupported_document_type_is_rejected(document_service):
    service, _, _, _ = document_service

    class FakeUploadFile:
        filename = "Brief.pdf"

        async def read(self):
            return b"assignment brief"

    current_user = SimpleNamespace(
        id=uuid.uuid4(),
        school_id=uuid.uuid4(),
        roles=[SimpleNamespace(role=SimpleNamespace(name="ADMIN"))],
    )

    with pytest.raises(ValueError, match="Unsupported document type"):
        asyncio.run(
            service.create_document(
                school_id=current_user.school_id,
                uploaded_by=current_user.id,
                document_type="invoice",
                file=FakeUploadFile(),
                current_user=current_user,
            )
        )
