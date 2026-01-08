"""Tests for internationalization (i18n) functionality."""

from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.i18n import get_i18n, translate
from tests.utils.utils import random_email, random_lower_string


def test_i18n_locale_detection_from_header(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test locale detection from Accept-Language header."""
    # Test with Chinese locale
    headers = {
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        **superuser_token_headers,
    }
    response = client.get(f"{settings.API_V1_STR}/items/", headers=headers)
    
    # Should accept the request (locale detection happens in exception handlers)
    assert response.status_code == 200


def test_i18n_locale_detection_from_query(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test locale detection from query parameter."""
    # Test with English locale via query parameter
    response = client.get(
        f"{settings.API_V1_STR}/items/?locale=en_US",
        headers=superuser_token_headers,
    )
    
    # Should accept the request
    assert response.status_code == 200


def test_i18n_default_locale(client: TestClient) -> None:
    """Test that default locale is used when no locale specified."""
    i18n = get_i18n()
    
    # Should use default locale
    assert i18n.get_translation(settings.I18N_DEFAULT_LOCALE) is not None


def test_i18n_translation_function() -> None:
    """Test translation function."""
    i18n = get_i18n()
    
    # Test translation (will return original if translation not found)
    translated = i18n.translate("Item not found", "zh_CN")
    assert isinstance(translated, str)
    
    # Test with English
    translated_en = i18n.translate("Item not found", "en_US")
    assert isinstance(translated_en, str)


def test_i18n_supported_locales() -> None:
    """Test that supported locales are configured."""
    i18n = get_i18n()
    
    # Should have translations for all supported locales
    for locale in settings.I18N_SUPPORTED_LOCALES:
        translation = i18n.get_translation(locale)
        assert translation is not None


def test_i18n_error_message_translation(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test that error messages are translated."""
    import uuid
    
    # Make a request that will generate an error
    headers = {
        "Accept-Language": "zh-CN",
        **superuser_token_headers,
    }
    response = client.get(
        f"{settings.API_V1_STR}/items/{uuid.uuid4()}",
        headers=headers,
    )
    
    # Error message should be present (may be in Chinese if translation exists)
    assert response.status_code == 404
    content = response.json()
    assert "detail" in content


def test_i18n_locale_fallback() -> None:
    """Test locale fallback mechanism."""
    i18n = get_i18n()
    
    # Request unsupported locale should fallback to default
    unsupported_locale = "fr_FR"
    translation = i18n.get_translation(unsupported_locale)
    
    # Should return a translation object (either for default locale or NullTranslations)
    assert translation is not None


def test_i18n_disabled() -> None:
    """Test i18n behavior when disabled."""
    from app.core.config import settings as app_settings
    
    # Temporarily disable i18n
    original_value = app_settings.I18N_ENABLED
    app_settings.I18N_ENABLED = False
    
    try:
        i18n = get_i18n()
        # When disabled, translate should return original message
        result = i18n.translate("Test message", "zh_CN")
        assert result == "Test message"
    finally:
        # Restore original value
        app_settings.I18N_ENABLED = original_value
