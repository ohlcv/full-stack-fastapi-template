"""Internationalization (i18n) configuration and utilities."""

import gettext
from pathlib import Path
from typing import Callable

from fastapi import Request

from app.core.config import settings


class I18n:
    """Internationalization manager."""

    def __init__(self) -> None:
        """Initialize i18n manager."""
        self.translations: dict[str, gettext.GNUTranslations] = {}
        self._load_translations()

    def _load_translations(self) -> None:
        """Load translation files for all supported locales."""
        if not settings.I18N_ENABLED:
            return

        locale_dir = Path(settings.I18N_LOCALE_DIR)
        if not locale_dir.exists():
            # Create default locale directory structure
            locale_dir.mkdir(parents=True, exist_ok=True)

        for locale in settings.I18N_SUPPORTED_LOCALES:
            try:
                # Try to load .mo file first (compiled), fallback to .po if not found
                translation = gettext.translation(
                    "messages",
                    localedir=str(locale_dir),
                    languages=[locale],
                    fallback=False,
                )
                self.translations[locale] = translation
            except (FileNotFoundError, OSError):
                # Use null translation if file not found (returns original message)
                self.translations[locale] = gettext.NullTranslations()

    def get_locale_from_request(self, request: Request) -> str:
        """Get locale from request (Accept-Language header or query parameter)."""
        # Check query parameter first
        locale_param = request.query_params.get("locale")
        if locale_param and locale_param in settings.I18N_SUPPORTED_LOCALES:
            return locale_param

        # Check Accept-Language header
        accept_language = request.headers.get("Accept-Language", "")
        if accept_language:
            # Parse Accept-Language header (e.g., "en-US,en;q=0.9,zh-CN;q=0.8")
            languages = []
            for lang in accept_language.split(","):
                lang = lang.split(";")[0].strip()
                # Convert format: en-US -> en_US
                lang = lang.replace("-", "_")
                languages.append(lang)

            # Find first supported locale
            for lang in languages:
                # Try exact match
                if lang in settings.I18N_SUPPORTED_LOCALES:
                    return lang
                # Try language only (e.g., en_US -> en)
                lang_code = lang.split("_")[0]
                for supported in settings.I18N_SUPPORTED_LOCALES:
                    if supported.startswith(lang_code):
                        return supported

        return settings.I18N_DEFAULT_LOCALE

    def get_translation(self, locale: str) -> gettext.GNUTranslations:
        """Get translation for a specific locale."""
        return self.translations.get(locale, self.translations.get(settings.I18N_DEFAULT_LOCALE, gettext.NullTranslations()))

    def translate(self, message: str, locale: str) -> str:
        """Translate a message to the specified locale."""
        if not settings.I18N_ENABLED:
            return message

        translation = self.get_translation(locale)
        return translation.gettext(message)


# Global i18n instance
_i18n_instance: I18n | None = None


def get_i18n() -> I18n:
    """Get global i18n instance."""
    global _i18n_instance
    if _i18n_instance is None:
        _i18n_instance = I18n()
    return _i18n_instance


def get_locale(request: Request) -> str:
    """Get locale from request."""
    return get_i18n().get_locale_from_request(request)


def translate(message: str, locale: str) -> str:
    """Translate a message to the specified locale."""
    return get_i18n().translate(message, locale)


def gettext_lazy(message: str) -> Callable[[Request], str]:
    """Create a lazy translation function that requires request."""
    def _translate(request: Request) -> str:
        locale = get_locale(request)
        return translate(message, locale)
    return _translate
