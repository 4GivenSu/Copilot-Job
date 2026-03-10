from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

from app.core.config import settings
from app.utils.verification import generate_code, store_code

_fast_mail: FastMail | None = None


def _get_mail_client() -> FastMail:
    """Lazily create the FastMail client so the app can start without SMTP config."""
    global _fast_mail
    if _fast_mail is None:
        config = ConnectionConfig(
            MAIL_USERNAME=settings.MAIL_USERNAME,
            MAIL_PASSWORD=settings.MAIL_PASSWORD,
            MAIL_FROM=settings.MAIL_FROM,
            MAIL_PORT=settings.MAIL_PORT,
            MAIL_SERVER=settings.MAIL_SERVER,
            MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
            MAIL_STARTTLS=settings.MAIL_STARTTLS,
            MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
            USE_CREDENTIALS=True,
        )
        _fast_mail = FastMail(config)
    return _fast_mail


async def send_verification_code(email: str) -> str:
    """Generate a verification code, store it, and e-mail it to the user."""
    code = generate_code()
    store_code(email, code)

    message = MessageSchema(
        subject="Your verification code",
        recipients=[email],
        body=(
            f"<p>Your verification code is: <strong>{code}</strong></p>"
            f"<p>It expires in 5 minutes.</p>"
        ),
        subtype=MessageType.html,
    )
    await _get_mail_client().send_message(message)
    return code
