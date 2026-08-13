from enum import Enum


class Actions(str, Enum):
    """Enum representing various actions that can be performed in the system."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    MISSING_INFORMATION = "missing_information"
    SUCCESS = "success"
