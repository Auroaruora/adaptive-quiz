"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import cors_origins
from app.routers import progress, quiz, topics, users

app = FastAPI(
    title="Adaptive Quiz",
    description=(
        "Serves questions matched to a student's estimated ability, using "
        "a Rasch model that updates after every answer."
    ),
)

# The frontend runs on its own origin, so the browser preflights every
# JSON POST. Only what the five endpoints use is allowed: no cookies are
# involved, since identity travels as a userId in the payload.
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(users.router)
app.include_router(topics.router)
app.include_router(quiz.router)
app.include_router(progress.router)


@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    """Reports that the service is up.

    Returns:
        A fixed payload, so a load balancer has something to poll.
    """
    return {"status": "ok"}
