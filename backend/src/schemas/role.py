"""
Role Schemas

Responsibility:
    Request/Response models for Role APIs.
"""

import uuid

from pydantic import BaseModel, ConfigDict


class CreateRoleRequest(BaseModel):
    name: str
    description: str | None = None


class AssignRoleRequest(BaseModel):
    role_id: uuid.UUID


class RoleResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None

    model_config = ConfigDict(from_attributes=True)
