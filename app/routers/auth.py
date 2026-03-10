import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    RegisterResponse,
    SendCodeRequest,
    SendCodeResponse,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import (
    authenticate_user,
    get_user_by_email,
    register_user,
)
from app.services.email_service import send_verification_code
from app.utils.jwt import create_access_token, decode_access_token

router = APIRouter(prefix="/auth", tags=["auth"])
bearer_scheme = HTTPBearer()
logger = logging.getLogger(__name__)


@router.post("/send-code", response_model=SendCodeResponse)
async def send_code(body: SendCodeRequest):
    """Send a 6-digit verification code to the given email address."""
    try:
        await send_verification_code(body.email)
    except Exception as exc:
        logger.error("Failed to send verification code to %s: %s", body.email, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to send verification code. Please try again later.",
        )
    return SendCodeResponse(message="Verification code sent. Please check your inbox.")


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user after verifying the email code."""
    try:
        user = await register_user(db, body.email, body.code, body.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return user


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate with email + password and return a JWT access token."""
    try:
        user = await authenticate_user(db, body.email, body.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    token = create_access_token(subject=user.email)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def get_me(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    """Return the currently authenticated user's profile."""
    email = decode_access_token(credentials.credentials)
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        )
    user = await get_user_by_email(db, email)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user
