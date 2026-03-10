from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.utils.security import hash_password, verify_password
from app.utils.verification import verify_code


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def register_user(db: AsyncSession, email: str, code: str, password: str) -> User:
    """Validate the verification code and create a new active user."""
    if not verify_code(email, code):
        raise ValueError("Invalid or expired verification code.")

    existing = await get_user_by_email(db, email)
    if existing:
        raise ValueError("Email is already registered.")

    user = User(
        email=email,
        password_hash=hash_password(password),
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    """Verify credentials and return the user, or raise ValueError on failure."""
    user = await get_user_by_email(db, email)
    if not user or not verify_password(password, user.password_hash):
        raise ValueError("Invalid email or password.")
    if not user.is_active:
        raise ValueError("Account is not active.")
    return user
