"""Internationalization utility functions."""

from fastapi import Request

from app.core.i18n import get_locale, translate


def gettext(request: Request, message: str) -> str:
    """Translate a message using request locale."""
    locale = get_locale(request)
    return translate(message, locale)


def _gettext(message: str) -> str:
    """Mark a string for translation (returns as-is, translation happens at runtime)."""
    return message
