from enum import Enum

"""
Responsibility: This file defines the DocumentStatus enum, which represents the various statuses that a document can have in the system. Each status is represented as a string value.
The statuses include:
- UPLOADED: The document has been uploaded but not yet processed.
- PARSING: The document is currently being parsed.
- PARSED: The document has been successfully parsed.
- CLARIFICATION: The document requires clarification before further processing.
- AWAITING_APPROVAL: The document is awaiting approval from the relevant authority.
- APPROVED: The document has been approved and is ready for application.
- APPLIED: The document has been applied in the system.
This enum is used throughout the application to manage and track the state of documents as they move through the various stages of processing and approval.
"""


class DocumentStatus(str, Enum):
    UPLOADED = "UPLOADED"
    PARSING = "PARSING"
    PARSED = "PARSED"
    CLARIFICATION = "CLARIFICATION"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVED = "APPROVED"
    APPLIED = "APPLIED"
