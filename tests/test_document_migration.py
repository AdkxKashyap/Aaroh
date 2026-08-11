import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, text

sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))

from src.config.settings import get_settings


def _load_backend_env() -> None:
    env_path = Path(__file__).resolve().parents[1] / "backend" / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key, value)


_load_backend_env()


def test_documents_timestamp_columns_have_defaults():
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", ""))

    with engine.connect() as conn:
        result = conn.execute(text("""
                SELECT table_name, column_name, column_default
                FROM information_schema.columns
                WHERE table_name IN ('documents', 'document_versions')
                  AND column_name IN ('created_at', 'updated_at')
                ORDER BY table_name, column_name
                """))
        defaults = {
            (row.table_name, row.column_name): row.column_default
            for row in result.mappings()
        }

    assert defaults[("documents", "created_at")] is not None
    assert defaults[("documents", "updated_at")] is not None
    assert defaults[("document_versions", "created_at")] is not None
    assert defaults[("document_versions", "updated_at")] is not None
