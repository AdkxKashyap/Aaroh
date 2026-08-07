"""
Role Enum

Responsibility:
    Defines all supported application roles.

Use this enum instead of hardcoding role names.
"""

from enum import StrEnum


class RoleName(StrEnum):
    ADMIN = "ADMIN"
    TEACHER = "TEACHER"
    STUDENT = "STUDENT"
    PARENT = "PARENT"
