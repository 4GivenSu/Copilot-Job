from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.routers.auth import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup (use Alembic for production migrations)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="User Auth System", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    # For production, replace "*" with a list of allowed origins,
    # e.g. allow_origins=["https://yourdomain.com"]
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

# Serve the frontend pages under /frontend
app.mount("/frontend", StaticFiles(directory="frontend", html=True), name="frontend")
