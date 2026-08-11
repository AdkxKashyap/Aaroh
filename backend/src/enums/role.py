"""
Role Enum

Responsibility:
    Defines all supported application roles.

Use this enum instead of hardcoding role names.
"""

from enum import Enum


class RoleName(str, Enum):
    ADMIN = "ADMIN"
    TEACHER = "TEACHER"
    STUDENT = "STUDENT"
    GUARDIAN = "GUARDIAN"
    PARENT = "PARENT"
