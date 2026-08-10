import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from src.core.auth import require_role
from src.dependencies.services import get_submission_service
from src.enums.role import RoleName
from src.models.user import User
from src.schemas.submission import RevisionRequest, SubmissionResponse
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


@router.get(
    "/assignment/{assignment_id}",
    response_model=list[SubmissionResponse],
)
async def get_assignment_submissions(
    assignment_id: uuid.UUID,
    current_user: Annotated[
        User,
        Depends(require_role(RoleName.TEACHER)),
    ],
    submission_service: Annotated[
        SubmissionService,
        Depends(get_submission_service),
    ],
):
    try:
        return await submission_service.get_assignment_submissions(
            current_user=current_user,
            assignment_id=assignment_id,
        )
    except ValueError as ex:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ex),
        )


@router.post(
    "/{submission_id}/review",
    response_model=SubmissionResponse,
)
async def start_review(
    submission_id: uuid.UUID,
    current_user: Annotated[
        User,
        Depends(require_role(RoleName.TEACHER)),
    ],
    submission_service: Annotated[
        SubmissionService,
        Depends(get_submission_service),
    ],
):
    try:
        return await submission_service.start_review(
            current_user=current_user,
            submission_id=submission_id,
        )
    except ValueError as ex:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ex),
        )


@router.post(
    "/{submission_id}/request-revision",
    response_model=SubmissionResponse,
)
async def request_revision(
    submission_id: uuid.UUID,
    request: RevisionRequest,
    current_user: Annotated[
        User,
        Depends(require_role(RoleName.TEACHER)),
    ],
    submission_service: Annotated[
        SubmissionService,
        Depends(get_submission_service),
    ],
):
    try:
        return await submission_service.request_revision(
            current_user=current_user,
            submission_id=submission_id,
            feedback=request.feedback,
        )
    except ValueError as ex:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ex),
        )


@router.post(
    "/{submission_id}/complete",
    response_model=SubmissionResponse,
)
async def complete_submission(
    submission_id: uuid.UUID,
    current_user: Annotated[
        User,
        Depends(require_role(RoleName.TEACHER)),
    ],
    submission_service: Annotated[
        SubmissionService,
        Depends(get_submission_service),
    ],
):
    try:
        return await submission_service.complete_submission(
            current_user=current_user,
            submission_id=submission_id,
        )
    except ValueError as ex:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ex),
        )
