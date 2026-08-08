from enum import Enum

"""
Assignment Status Enum
Responsibility:
    Defines all supported assignment statuses.
"""


class AssignmentStatus(str, Enum):
    DRAFT = "DRAFT"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
