"""FastAPI application entry point."""

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root() -> dict[str, str]:
    """Return a simple hello-world payload.

    Returns:
        A greeting message.
    """
    return {"message": "Hello, world!"}
