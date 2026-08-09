import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from src.core.auth import require_role
from src.dependencies.services import get_submission_service
from src.enums.role import RoleName
from src.models.user import User
from src.schemas.submission import SubmissionResponse
from src.services.submission_service import SubmissionService

router = APIRouter(
    prefix="/submissions",
    tags=["Submissions"],
)


@router.post(
    "/{assignment_id}",
    response_model=SubmissionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_assignment(
    assignment_id: uuid.UUID,
    current_user: Annotated[
        User,
        Depends(require_role(RoleName.STUDENT)),
    ],
    submission_service: Annotated[
        SubmissionService,
        Depends(get_submission_service),
    ],
):
    """
    Submit an assignment for the authenticated student.
    """

    try:
        return await submission_service.submit_assignment(
            current_user=current_user,
            assignment_id=assignment_id,
        )

    except ValueError as ex:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ex),
        )
