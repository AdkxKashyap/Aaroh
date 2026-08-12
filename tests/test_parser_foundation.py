import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))

from src.enums.document_type import DocumentType
from src.services.document_parser import (
    AssignmentBriefParser,
    DocumentParserRegistry,
    RosterParser,
)


def test_parser_registry_selects_assignment_brief_parser():
    parser = DocumentParserRegistry.get_parser(DocumentType.ASSIGNMENT_BRIEF)

    assert isinstance(parser, AssignmentBriefParser)


def test_assignment_brief_parser_extracts_required_fields():
    content = (
        "Title: Science Lab Report\n"
        "Subject: Biology\n"
        "Instructions: Submit in one week.\n"
        "Due date: 2026-09-15\n"
        "Target class: Grade 8B"
    )

    parsed = AssignmentBriefParser().parse(content)

    assert parsed.document_type == DocumentType.ASSIGNMENT_BRIEF
    assert parsed.data["title"] == "Science Lab Report"
    assert parsed.data["subject"] == "Biology"
    assert parsed.data["due_date"] == "2026-09-15"
    assert parsed.data["instructions"] == "Submit in one week."
    assert parsed.missing_fields == []
    assert parsed.warnings == []


def test_roster_parser_detects_duplicate_rows():
    content = "Name,Class\nAva,7A\nAva,7A\nMilo,7A"

    parsed = RosterParser().parse(content)

    assert parsed.document_type == DocumentType.CLASS_ROSTER
    assert len(parsed.data["rows"]) == 3
    assert any("duplicate" in message.lower() for message in parsed.ambiguities)
    assert any("duplicate" in message.lower() for message in parsed.warnings)


def test_roster_parser_normalizes_alias_headers_and_marks_missing_required_fields():
    content = "Student Name,Parent,Notes\nAva,555-0101,Ready\nMilo,555-0102,Ready"

    parsed = RosterParser().parse(content)

    assert parsed.data["rows"][0]["name"] == "Ava"
    assert parsed.data["rows"][0]["parent_contact"] == "555-0101"
    assert "class" in parsed.missing_fields
    assert any(
        "Missing required roster columns" in message for message in parsed.ambiguities
    )
