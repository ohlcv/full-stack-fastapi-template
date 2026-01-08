"""Internationalization dependencies for API routes."""

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Request

from app.core.i18n import get_locale, translate


def get_request_locale(request: Request) -> str:
    """Get locale from request."""
    return get_locale(request)


Locale = Annotated[str, Depends(get_request_locale)]


def get_translator(request: Request) -> Callable[[str], str]:
    """Get translator function for current request locale."""
    locale = get_locale(request)

    def translator(message: str) -> str:
        return translate(message, locale)

    return translator


Translator = Annotated[Callable[[str], str], Depends(get_translator)]
