from email.header import Header

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

from app.core.config import settings
from app.utils.verification import generate_code, store_code

_fast_mail: FastMail | None = None


def _encode_header_name(name: str) -> str:
    """RFC 2047-encode a display name that contains non-ASCII characters.

    fastapi-mail inserts MAIL_FROM_NAME verbatim into the ``From:`` header.
    Raw non-ASCII bytes in email headers violate RFC 2822 and are rejected by
    many SMTP servers (including QQ Mail).  This helper pre-encodes the name
    so the header stays RFC-compliant regardless of the language used.
    """
    try:
        name.encode("ascii")
        return name  # Already ASCII – no encoding needed
    except UnicodeEncodeError:
        return Header(name, "utf-8").encode()  # e.g. =?utf-8?b?...?=


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
            MAIL_FROM_NAME=_encode_header_name(settings.MAIL_FROM_NAME),
            MAIL_STARTTLS=settings.MAIL_STARTTLS,
            MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
            USE_CREDENTIALS=True,
        )
        _fast_mail = FastMail(config)
    return _fast_mail


async def send_verification_code(email: str) -> str:
    """Generate a verification code, e-mail it, then store it on success.

    The code is stored *after* the email is successfully sent so that a
    delivery failure never leaves an orphaned (invisible) code in memory.
    """
    code = generate_code()

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

    # Persist the code only after the email is confirmed sent.
    # store_code() is an in-memory dict write; it will not raise in practice,
    # but if it did, the exception propagates to the caller so the endpoint
    # returns an error rather than silently succeeding.
    store_code(email, code)
    return code
