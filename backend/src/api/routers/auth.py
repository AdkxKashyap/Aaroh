"""
Authentication APIs

Note:
    Temporary hardcoded user.
    Will be replaced with database authentication
    in the Identity module.
"""

from fastapi import APIRouter, HTTPException, Depends

from src.core.auth import get_current_user
from src.core.security import (
    create_access_token,
    verify_password,
)
from src.schemas.auth import (
    LoginRequest,
    TokenResponse,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

DEMO_USER = "admin"
DEMO_PASSWORD_HASH = "$2b$12$iPSoLPzGYH.DYfFpY6VB0.JGAINWVebYkFQpbIS804OLhl8tmLRd6"  # Replace with hash_password("admin123")


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):

    if request.username != DEMO_USER or not verify_password(
        request.password,
        DEMO_PASSWORD_HASH,
    ):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(request.username)

    return {
        "access_token": token,
        "token_type": "bearer",
    }


@router.get("/me")
async def me(user: str = Depends(get_current_user)):
    return {"username": user}
