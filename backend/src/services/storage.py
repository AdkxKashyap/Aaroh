"""
Storage abstractions for uploaded documents.

Responsibility:
    Provide a pluggable storage interface so uploads can be moved from local
    filesystem storage to cloud/object storage later without changing the
    document service flow.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class FileStorage(ABC):
    """Interface for document storage backends."""

    @abstractmethod
    async def store(self, *, file_bytes: bytes, storage_key: str) -> str:
        """Persist bytes and return the storage identifier/path."""

    @abstractmethod
    async def read(self, storage_key: str) -> bytes:
        """Read a stored file and return its raw bytes."""

    @abstractmethod
    async def delete(self, storage_key: str) -> None:
        """Remove an uploaded file from storage."""


class LocalFileStorage(FileStorage):
    """Local filesystem implementation used by default."""

    def __init__(self, base_dir: str | Path | None = None) -> None:
        self.base_dir = Path(
            base_dir or Path(__file__).resolve().parents[2] / "../uploads"
        )
        self.base_dir = self.base_dir.resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def store(self, *, file_bytes: bytes, storage_key: str) -> str:
        destination = self.base_dir / storage_key
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(file_bytes)
        return str(destination.relative_to(self.base_dir))

    async def read(self, storage_key: str) -> bytes:
        destination = self.base_dir / storage_key
        return destination.read_bytes()

    async def delete(self, storage_key: str) -> None:
        destination = self.base_dir / storage_key
        if destination.exists():
            destination.unlink()
