"""Creating students."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import schemas
from app.db.models import User
from app.db.session import get_session

router = APIRouter(tags=["users"])


@router.post(
    "/users",
    response_model=schemas.UserOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    body: schemas.UserCreate,
    session: AsyncSession = Depends(get_session),
) -> User:
    """Creates a student.

    There is no authentication in this project, so a display name is all
    that is stored and names are not required to be unique.

    Args:
        body: The name to show for this student.
        session: Injected database session.

    Returns:
        The created student, including the assigned id.
    """
    user = User(display_name=body.display_name.strip())
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
