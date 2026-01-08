import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.deps import (
    CurrentUser,
    SessionDep,
    get_current_active_superuser,
)
from app.core.rate_limit import limiter
from app.models import (
    Message,
    UpdatePassword,
    UserCreate,
    UserPublic,
    UserRegister,
    UsersPublic,
    UserUpdate,
    UserUpdateMe,
)
from app.services import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UsersPublic,
)
def read_users(session: SessionDep, skip: int = 0, limit: int = 100) -> Any:
    """
    Retrieve users.
    """
    return UserService.get_users(session=session, skip=skip, limit=limit)


@router.post(
    "/", dependencies=[Depends(get_current_active_superuser)], response_model=UserPublic
)
def create_user(*, session: SessionDep, user_in: UserCreate) -> Any:
    """
    Create new user.
    """
    return UserService.create_user(session=session, user_in=user_in)


@router.patch("/me", response_model=UserPublic)
def update_user_me(
    *, session: SessionDep, user_in: UserUpdateMe, current_user: CurrentUser
) -> Any:
    """
    Update own user.
    """
    return UserService.update_user_me(
        session=session, user_in=user_in, current_user=current_user
    )


@router.patch("/me/password", response_model=Message)
def update_password_me(
    *, session: SessionDep, body: UpdatePassword, current_user: CurrentUser
) -> Any:
    """
    Update own password.
    """
    result = UserService.update_password_me(
        session=session,
        current_password=body.current_password,
        new_password=body.new_password,
        current_user=current_user,
    )
    return Message(message=result["message"])


@router.get("/me", response_model=UserPublic)
def read_user_me(current_user: CurrentUser) -> Any:
    """
    Get current user.
    """
    return UserService.get_current_user(current_user=current_user)


@router.delete("/me", response_model=Message)
def delete_user_me(session: SessionDep, current_user: CurrentUser) -> Any:
    """
    Delete own user.
    """
    result = UserService.delete_user_me(session=session, current_user=current_user)
    return Message(message=result["message"])


@router.post("/signup", response_model=UserPublic)
@limiter.limit("3/minute")
def register_user(
    request: Request, session: SessionDep, user_in: UserRegister
) -> Any:
    """
    Create new user without the need to be logged in.
    """
    # Convert UserRegister to UserCreate using model_dump()
    user_create = UserCreate.model_validate(user_in.model_dump())
    return UserService.register_user(session=session, user_in=user_create)


@router.get("/{user_id}", response_model=UserPublic)
def read_user_by_id(
    user_id: uuid.UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    """
    Get a specific user by id.
    """
    # If we reach here, current_user dependency has passed (user is authenticated and active)
    user = UserService.get_user_by_id(session=session, user_id=user_id)
    # Check access: user can see themselves, superuser can see anyone
    if not UserService.check_user_access(user=current_user, target_user_id=user_id):
        raise HTTPException(
            status_code=403,
            detail="The user doesn't have enough privileges",
        )
    return user


@router.patch(
    "/{user_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserPublic,
)
def update_user(
    *,
    session: SessionDep,
    user_id: uuid.UUID,
    user_in: UserUpdate,
) -> Any:
    """
    Update a user.
    """
    return UserService.update_user(session=session, user_id=user_id, user_in=user_in)


@router.delete("/{user_id}", dependencies=[Depends(get_current_active_superuser)])
def delete_user(
    session: SessionDep, current_user: CurrentUser, user_id: uuid.UUID
) -> Message:
    """
    Delete a user.
    """
    result = UserService.delete_user(
        session=session, user_id=user_id, current_user=current_user
    )
    return Message(message=result["message"])
