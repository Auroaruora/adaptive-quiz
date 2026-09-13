"""FastAPI application entry point."""

from fastapi import FastAPI

from app.routers import progress, quiz, users

app = FastAPI(
    title="Adaptive Quiz",
    description=(
        "Serves questions matched to a student's estimated ability, using "
        "a Rasch model that updates after every answer."
    ),
)

app.include_router(users.router)
app.include_router(quiz.router)
app.include_router(progress.router)


@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    """Reports that the service is up.

    Returns:
        A fixed payload, so a load balancer has something to poll.
    """
    return {"status": "ok"}
