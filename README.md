# User Authentication System

A full-stack user authentication system built with **FastAPI**, **SQLAlchemy (async)**, **MySQL**, **JWT**, and **bcrypt**, with email verification via **fastapi-mail**.

## Project Structure

```
app/
├── main.py               # FastAPI app factory: CORS, routers, lifespan startup
├── database.py           # Async SQLAlchemy engine, session factory, Base
├── core/
│   └── config.py         # Pydantic-settings config loaded from .env
├── models/
│   └── user.py           # User ORM model (id, email, password_hash, is_active, created_at)
├── schemas/
│   └── auth.py           # Pydantic request/response schemas
├── routers/
│   └── auth.py           # API routes: /auth/send-code, /auth/register, /auth/login, /auth/me
├── services/
│   ├── email_service.py  # fastapi-mail: sends 6-digit verification code emails
│   └── auth_service.py   # Business logic: register_user, authenticate_user
└── utils/
    ├── security.py       # bcrypt password hash / verify helpers
    ├── jwt.py            # JWT create / decode helpers
    └── verification.py   # In-memory TTL-based verification code store

frontend/
├── register.html         # Register page (email → send code → verify → set password)
└── login.html            # Login page (email + password → JWT token display)

.env.example              # Template for environment variables
requirements.txt          # Python dependencies
```

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your MySQL credentials, JWT secret, and SMTP settings
```

### 3. Create the MySQL database

```sql
CREATE DATABASE auth_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4. Run the server

```bash
uvicorn app.main:app --reload
```

Tables are created automatically on startup. Open `http://localhost:8000/docs` for the interactive API documentation.

### 5. Access the frontend

- Register: `http://localhost:8000/frontend/register.html`
- Login:    `http://localhost:8000/frontend/login.html`

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/send-code` | Send a 6-digit email verification code |
| POST | `/auth/register`  | Register (requires verification code + password ≥ 8 chars) |
| POST | `/auth/login`     | Login and receive a JWT access token |
| GET  | `/auth/me`        | Get current user info (Bearer token required) |

### Example Requests

**Send verification code**
```bash
curl -X POST http://localhost:8000/auth/send-code \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com"}'
```

**Register**
```bash
curl -X POST http://localhost:8000/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com", "code": "123456", "password": "MySecret1"}'
```

**Login**
```bash
curl -X POST http://localhost:8000/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com", "password": "MySecret1"}'
# Returns: {"access_token": "<JWT>", "token_type": "bearer"}
```

**Get current user**
```bash
curl http://localhost:8000/auth/me \
     -H "Authorization: Bearer <JWT>"
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Async MySQL URL (`mysql+aiomysql://user:pass@host/db`) |
| `SECRET_KEY` | JWT signing secret — **must** be set |
| `ALGORITHM` | JWT algorithm (default: `HS256`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token TTL in minutes (default: `30`) |
| `MAIL_USERNAME` | SMTP username |
| `MAIL_PASSWORD` | SMTP password |
| `MAIL_FROM` | Sender email address |
| `MAIL_PORT` | SMTP port (default: `587`) |
| `MAIL_SERVER` | SMTP host (default: `smtp.gmail.com`) |
| `MAIL_STARTTLS` | Use STARTTLS (default: `True`) |
| `MAIL_SSL_TLS` | Use SSL/TLS (default: `False`) |

## Security Notes

- Passwords are hashed with **bcrypt** — plain-text passwords are never stored.
- JWT tokens expire after `ACCESS_TOKEN_EXPIRE_MINUTES` minutes.
- Verification codes expire after **5 minutes** and are single-use.
- The in-memory verification code store is process-local; replace with Redis for production deployments with multiple workers.
- Restrict `allow_origins` in `app/main.py` to your actual domain in production.