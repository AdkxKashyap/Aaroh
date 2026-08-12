from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from src.enums.document_type import DocumentType


class ParserError(ValueError):
    """Base exception for parser-boundary failures."""


@dataclass
class ParsedDocument:
    document_type: DocumentType
    data: dict[str, Any]
    confidence: float = 1.0
    ambiguities: list[str] = field(default_factory=list)
    missing_fields: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_type": (
                self.document_type.value
                if isinstance(self.document_type, DocumentType)
                else self.document_type
            ),
            "data": self.data,
            "confidence": self.confidence,
            "ambiguities": list(self.ambiguities),
            "missing_fields": list(self.missing_fields),
            "warnings": list(self.warnings),
        }


class DocumentParser:
    """Base interface for document parsers.

    The parser boundary does not write to persistent storage; it only produces
    structured output from extracted document text.
    """

    document_type: DocumentType

    def parse(self, extracted_text: str) -> ParsedDocument:
        raise NotImplementedError


class AssignmentBriefParser(DocumentParser):
    document_type = DocumentType.ASSIGNMENT_BRIEF

    def parse(self, extracted_text: str) -> ParsedDocument:
        text = (extracted_text or "").strip()
        if not text:
            raise ParserError("Assignment brief content is empty.")

        normalized = "\n".join(
            line.strip() for line in text.splitlines() if line.strip()
        )
        payload: dict[str, Any] = {
            "title": None,
            "subject": None,
            "instructions": None,
            "due_date": None,
            "target_class": None,
            "attachments": [],
            "constraints": [],
        }
        ambiguities: list[str] = []
        missing_fields: list[str] = []

        for line in normalized.splitlines():
            if ":" not in line:
                continue
            key, value = [part.strip() for part in line.split(":", 1)]
            key_lower = key.lower()
            value_clean = value.strip()

            if not value_clean:
                continue

            if key_lower in {"title", "assignment"}:
                payload["title"] = value_clean
            elif key_lower == "subject":
                payload["subject"] = value_clean
            elif key_lower in {"instructions", "instruction"}:
                payload["instructions"] = value_clean
            elif key_lower in {"due date", "deadline", "due"}:
                payload["due_date"] = value_clean
                try:
                    datetime.strptime(value_clean, "%Y-%m-%d")
                except ValueError:
                    ambiguities.append(
                        "Due date is not in a standard YYYY-MM-DD format."
                    )
            elif key_lower in {"target class", "class", "target"}:
                payload["target_class"] = value_clean
            elif key_lower in {"attachment", "attachments"}:
                payload["attachments"] = [
                    item.strip() for item in value_clean.split(",") if item.strip()
                ]
            elif key_lower in {"constraint", "constraints"}:
                payload["constraints"] = [
                    item.strip() for item in value_clean.split(",") if item.strip()
                ]

        if payload["title"] is None:
            missing_fields.append("title")
        if payload["subject"] is None:
            missing_fields.append("subject")
        if payload["instructions"] is None:
            missing_fields.append("instructions")
        if payload["due_date"] is None:
            missing_fields.append("due_date")

        if missing_fields:
            ambiguities.append(
                "Missing required assignment brief fields: " + ", ".join(missing_fields)
            )

        warnings = list(ambiguities)

        return ParsedDocument(
            document_type=self.document_type,
            data=payload,
            confidence=0.9 if not missing_fields else 0.5,
            ambiguities=ambiguities,
            missing_fields=missing_fields,
            warnings=warnings,
        )


class RosterParser(DocumentParser):
    document_type = DocumentType.CLASS_ROSTER

    _HEADER_ALIASES = {
        "name": {"name", "student", "student_name", "full_name", "student name"},
        "username": {"username", "user_name", "login", "student_username"},
        "email": {"email", "email_address", "student_email"},
        "password": {"password", "pass", "temporary_password", "student_password"},
        "class": {
            "class",
            "class_name",
            "classroom",
            "student_class",
            "grade",
            "grade_class",
            "grade/class",
        },
        "parent_contact": {
            "parent_contact",
            "guardian_contact",
            "parent",
            "guardian",
            "parent_name",
            "guardian_name",
            "phone",
            "contact",
            "parent_phone",
            "guardian_phone",
        },
        "notes": {"notes", "optional_notes", "note", "comments", "comment", "remarks"},
    }

    @classmethod
    def _normalize_header(cls, value: str) -> str:
        normalized = "".join(
            ch.lower()
            for ch in value.strip()
            if ch.isalnum() or ch in {"_", "/", "-", " "}
        )
        normalized = normalized.replace("-", "_")
        normalized = normalized.replace("/", "_")
        normalized = " ".join(normalized.split())
        normalized = normalized.replace(" ", "_")
        return normalized

    @classmethod
    def _header_field_name(cls, raw_header: str) -> str | None:
        normalized = cls._normalize_header(raw_header)
        for canonical, aliases in cls._HEADER_ALIASES.items():
            if normalized in aliases or normalized == canonical:
                return canonical
        return None

    def parse(self, extracted_text: str) -> ParsedDocument:
        text = (extracted_text or "").strip()
        if not text:
            raise ParserError("Roster content is empty.")

        rows = list(csv.reader(io.StringIO(text)))
        if not rows or len(rows) < 2:
            raise ParserError("Roster content does not contain a recognizable table.")

        header = [cell.strip() for cell in rows[0]]
        if not header:
            raise ParserError("Roster header is missing.")

        header_map: dict[str, int] = {}
        for index, cell in enumerate(header):
            field_name = self._header_field_name(cell)
            if field_name is not None:
                header_map[field_name] = index

        required_fields = ["name", "class", "username", "email", "password"]
        missing_fields = [
            field_name for field_name in required_fields if field_name not in header_map
        ]

        normalized_rows: list[dict[str, str]] = []
        ambiguities: list[str] = []
        seen_pair_keys: set[tuple[str, str]] = set()

        for row_index, row in enumerate(rows[1:], start=2):
            if not row or not any(cell.strip() for cell in row):
                continue

            payload = {
                "name": "",
                "username": "",
                "email": "",
                "password": "",
                "grade_class": "",
                "parent_contact": "",
                "notes": "",
            }

            for field_name, column_index in header_map.items():
                if column_index >= len(row):
                    continue
                value = row[column_index].strip()
                if field_name == "name":
                    payload["name"] = value
                elif field_name == "username":
                    payload["username"] = value
                elif field_name == "email":
                    payload["email"] = value
                elif field_name == "password":
                    payload["password"] = value
                elif field_name == "class":
                    payload["grade_class"] = value
                elif field_name == "parent_contact":
                    payload["parent_contact"] = value
                elif field_name == "notes":
                    payload["notes"] = value

            if not payload["name"]:
                ambiguities.append(f"Missing student name on row {row_index}.")
            if not payload["grade_class"]:
                ambiguities.append(f"Missing class/grade on row {row_index}.")
            if not payload["username"]:
                ambiguities.append(f"Missing username on row {row_index}.")
            if not payload["email"]:
                ambiguities.append(f"Missing email on row {row_index}.")
            if not payload["password"]:
                ambiguities.append(f"Missing password on row {row_index}.")

            composite_key = (
                payload["name"].strip().lower(),
                payload["grade_class"].strip().lower(),
            )
            if payload["name"] and payload["grade_class"]:
                if composite_key in seen_pair_keys:
                    ambiguities.append(
                        f"Duplicate roster row for '{payload['name']}' in class '{payload['grade_class']}' on row {row_index}."
                    )
                seen_pair_keys.add(composite_key)

            if not payload["parent_contact"]:
                ambiguities.append(
                    f"Missing parent/guardian contact on row {row_index}."
                )

            normalized_rows.append(payload)

        if not normalized_rows:
            raise ParserError("Roster content does not contain any student rows.")

        if missing_fields:
            ambiguities.append(
                "Missing required roster columns: " + ", ".join(missing_fields)
            )

        warnings = list(ambiguities)

        data = {
            "rows": normalized_rows,
            "students": normalized_rows,
        }

        return ParsedDocument(
            document_type=self.document_type,
            data=data,
            confidence=0.95 if not ambiguities else 0.7,
            ambiguities=ambiguities,
            missing_fields=missing_fields,
            warnings=warnings,
        )


class DocumentParserRegistry:
    """Factory for selecting a parser based on document type."""

    _PARSERS: dict[DocumentType, type[DocumentParser]] = {
        DocumentType.ASSIGNMENT_BRIEF: AssignmentBriefParser,
        DocumentType.CLASS_ROSTER: RosterParser,
    }

    @classmethod
    def get_parser(cls, document_type: DocumentType | str) -> DocumentParser:
        key = (
            DocumentType(document_type)
            if isinstance(document_type, str)
            else document_type
        )
        parser_cls = cls._PARSERS.get(key)
        if parser_cls is None:
            raise ParserError(
                f"No parser registered for document type: {document_type}"
            )
        return parser_cls()
