"""Custom exception classes."""

from fastapi import HTTPException, status


class BaseAPIException(HTTPException):
    """Base exception class for API errors."""

    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: str = "An error occurred",
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class NotFoundError(BaseAPIException):
    """Resource not found exception."""

    def __init__(self, resource: str = "Resource", detail: str | None = None) -> None:
        detail = detail or f"{resource} not found"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class BadRequestError(BaseAPIException):
    """Bad request exception."""

    def __init__(self, detail: str = "Bad request") -> None:
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class UnauthorizedError(BaseAPIException):
    """Unauthorized exception."""

    def __init__(self, detail: str = "Not authenticated") -> None:
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class ForbiddenError(BaseAPIException):
    """Forbidden exception."""

    def __init__(self, detail: str = "Not enough permissions") -> None:
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class ConflictError(BaseAPIException):
    """Conflict exception (e.g., duplicate resource)."""

    def __init__(self, detail: str = "Resource conflict") -> None:
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class ValidationError(BaseAPIException):
    """Validation error exception."""

    def __init__(self, detail: str = "Validation error") -> None:
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)
