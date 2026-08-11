import sys
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))

from src.enums.role import RoleName
from src.models.guardian_links import GuardianLink
from src.models.student import Student
from src.models.user import User
from src.schemas.student import StudentResponse
from src.services.guardian_service import GuardianService


class FakeUserRepository:
    def __init__(self, users=None):
        self.users = users or {}

    async def get_by_id(self, user_id):
        return self.users.get(user_id)

    async def get_by_id_with_roles(self, user_id):
        return self.users.get(user_id)

    async def update(self, user):
        self.users[user.id] = user
        return user


class FakeDB:
    def __init__(self):
        self.info = {}

    def in_transaction(self):
        return False

    async def commit(self):
        return None

    async def rollback(self):
        return None


class FakeStudentRepository:
    def __init__(self, students=None):
        self.students = students or {}

    async def get_by_id(self, student_id):
        return self.students.get(student_id)


class FakeGuardianLinkRepository:
    def __init__(self, links=None):
        self.links = list(links or [])
        self.created = []

    async def create(self, guardian_user_id, student_id):
        link = GuardianLink(
            guardian_user_id=guardian_user_id,
            student_id=student_id,
        )
        self.created.append(link)
        self.links.append(link)
        return link

    async def exists(self, guardian_user_id, student_id):
        return any(
            link.guardian_user_id == guardian_user_id and link.student_id == student_id
            for link in self.links
        )

    async def get_by_student_id(self, student_id):
        return next(
            (link for link in self.links if link.student_id == student_id),
            None,
        )

    async def get_students_by_guardian(self, guardian_user_id):
        return [
            SimpleNamespace(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                school_id=uuid.uuid4(),
                class_id=uuid.uuid4(),
                user=SimpleNamespace(username="student_user"),
                school=SimpleNamespace(name="Demo School"),
                school_class=SimpleNamespace(name="Class 1"),
            )
            for link in self.links
            if link.guardian_user_id == guardian_user_id
        ]


class FakeRoleRepository:
    def __init__(self, roles=None):
        self.roles = roles or {}

    async def get_by_name(self, name):
        return self.roles.get(name)

    async def assign_role(self, user, role):
        return None


@pytest.fixture
def guardian_service():
    user_repo = FakeUserRepository()
    student_repo = FakeStudentRepository()
    link_repo = FakeGuardianLinkRepository()
    role_repo = FakeRoleRepository()
    service = GuardianService(
        user_repository=user_repo,
        student_repository=student_repo,
        guardian_link_repository=link_repo,
        role_repository=role_repo,
        db=FakeDB(),
    )
    return service, user_repo, student_repo, link_repo, role_repo


def test_link_guardian_to_student_creates_link(guardian_service):
    service, user_repo, student_repo, link_repo, _ = guardian_service

    guardian_user = User(
        username="guardian", email="guardian@example.com", password_hash="x"
    )
    guardian_user.id = uuid.uuid4()
    guardian_user.school_id = uuid.uuid4()
    guardian_user.__dict__["roles"] = [
        SimpleNamespace(role=SimpleNamespace(name=RoleName.GUARDIAN))
    ]
    user_repo.users[guardian_user.id] = guardian_user

    student = Student(
        user_id=uuid.uuid4(), school_id=guardian_user.school_id, class_id=uuid.uuid4()
    )
    student.id = uuid.uuid4()
    student_repo.students[student.id] = student

    created = __import__("asyncio").run(
        service.link_guardian_to_student(
            guardian_user.id,
            student.id,
            current_user=guardian_user,
        )
    )

    assert created.guardian_user_id == guardian_user.id
    assert created.student_id == student.id
    assert len(link_repo.created) == 1


def test_link_guardian_to_student_rejects_non_guardian(guardian_service):
    service, user_repo, student_repo, _, _ = guardian_service

    guardian_user = User(
        username="student_user", email="student@example.com", password_hash="x"
    )
    guardian_user.id = uuid.uuid4()
    guardian_user.__dict__["roles"] = [
        SimpleNamespace(role=SimpleNamespace(name=RoleName.STUDENT))
    ]
    user_repo.users[guardian_user.id] = guardian_user

    student = Student(
        user_id=uuid.uuid4(), school_id=uuid.uuid4(), class_id=uuid.uuid4()
    )
    student.id = uuid.uuid4()
    student_repo.students[student.id] = student

    with pytest.raises(ValueError, match="must be a guardian"):
        __import__("asyncio").run(
            service.link_guardian_to_student(
                guardian_user.id,
                student.id,
                current_user=guardian_user,
            )
        )


def test_get_linked_students_returns_only_guardian_students(guardian_service):
    service, _, _, link_repo, _ = guardian_service

    student_a = Student(
        user_id=uuid.uuid4(), school_id=uuid.uuid4(), class_id=uuid.uuid4()
    )
    student_b = Student(
        user_id=uuid.uuid4(), school_id=uuid.uuid4(), class_id=uuid.uuid4()
    )
    student_a.id = uuid.uuid4()
    student_b.id = uuid.uuid4()

    link_repo.links = [
        SimpleNamespace(guardian_user_id=uuid.uuid4(), student_id=student_a.id),
        SimpleNamespace(guardian_user_id=uuid.uuid4(), student_id=student_b.id),
    ]

    guardian_id = uuid.uuid4()
    link_repo.links.append(
        SimpleNamespace(guardian_user_id=guardian_id, student_id=student_a.id)
    )

    students = __import__("asyncio").run(service.get_linked_students(guardian_id))

    assert len(students) == 1
    assert students[0].username == "student_user"


def test_get_linked_students_returns_populated_student_response():
    user_repo = FakeUserRepository()
    student_repo = FakeStudentRepository()
    role_repo = FakeRoleRepository()

    class FakeGuardianLinkRepo:
        async def get_students_by_guardian(self, guardian_user_id):
            student = Student(
                user_id=uuid.uuid4(),
                school_id=uuid.uuid4(),
                class_id=uuid.uuid4(),
            )
            student.id = uuid.uuid4()
            student.user = SimpleNamespace(username="student_user")
            student.school = SimpleNamespace(name="Demo School")
            student.school_class = SimpleNamespace(name="Class 1")
            return [student]

    service = GuardianService(
        user_repository=user_repo,
        student_repository=student_repo,
        guardian_link_repository=FakeGuardianLinkRepo(),
        role_repository=role_repo,
        db=FakeDB(),
    )

    result = __import__("asyncio").run(service.get_linked_students(uuid.uuid4()))

    assert isinstance(result[0], StudentResponse)
    assert result[0].username == "student_user"
    assert result[0].school_name == "Demo School"
    assert result[0].class_name == "Class 1"
    assert result[0].student_name == "student_user"


def test_create_guardian_assigns_school_and_role(guardian_service):
    service, user_repo, _, _, role_repo = guardian_service

    admin_user = User(username="admin", email="admin@example.com", password_hash="x")
    admin_user.id = uuid.uuid4()
    admin_user.school_id = uuid.uuid4()
    user_repo.users[admin_user.id] = admin_user

    guardian_role = SimpleNamespace(name=RoleName.GUARDIAN)
    role_repo.roles[RoleName.GUARDIAN] = guardian_role

    class FakeUserService:
        def __init__(self, repository):
            self.repository = repository

        async def register_user(self, username, email, password):
            user = User(username=username, email=email, password_hash="x")
            user.id = uuid.uuid4()
            self.repository.users[user.id] = user
            return user

    created = __import__("asyncio").run(
        service.create_guardian(
            current_user=admin_user,
            username="guardian_new",
            email="guardian_new@example.com",
            password="secret",
            user_service=FakeUserService(user_repo),
        )
    )

    assert created.school_id == admin_user.school_id


def test_link_guardian_to_student_rejects_different_school(guardian_service):
    service, user_repo, student_repo, _, _ = guardian_service

    guardian_user = User(
        username="guardian", email="guardian@example.com", password_hash="x"
    )
    guardian_user.id = uuid.uuid4()
    guardian_user.school_id = uuid.uuid4()
    guardian_user.__dict__["roles"] = [
        SimpleNamespace(role=SimpleNamespace(name=RoleName.GUARDIAN))
    ]
    user_repo.users[guardian_user.id] = guardian_user

    student = Student(
        user_id=uuid.uuid4(), school_id=uuid.uuid4(), class_id=uuid.uuid4()
    )
    student.id = uuid.uuid4()
    student_repo.students[student.id] = student

    with pytest.raises(ValueError, match="same school"):
        __import__("asyncio").run(
            service.link_guardian_to_student(
                guardian_user.id,
                student.id,
                current_user=guardian_user,
            )
        )


def test_link_guardian_to_student_rejects_existing_guardian(guardian_service):
    service, user_repo, student_repo, link_repo, _ = guardian_service

    guardian_user = User(
        username="guardian", email="guardian@example.com", password_hash="x"
    )
    guardian_user.id = uuid.uuid4()
    guardian_user.school_id = uuid.uuid4()
    guardian_user.__dict__["roles"] = [
        SimpleNamespace(role=SimpleNamespace(name=RoleName.GUARDIAN))
    ]
    user_repo.users[guardian_user.id] = guardian_user

    student = Student(
        user_id=uuid.uuid4(), school_id=guardian_user.school_id, class_id=uuid.uuid4()
    )
    student.id = uuid.uuid4()
    student_repo.students[student.id] = student

    link_repo.links.append(
        SimpleNamespace(guardian_user_id=uuid.uuid4(), student_id=student.id)
    )

    with pytest.raises(ValueError, match="already has a guardian"):
        __import__("asyncio").run(
            service.link_guardian_to_student(
                guardian_user.id,
                student.id,
                current_user=guardian_user,
            )
        )
