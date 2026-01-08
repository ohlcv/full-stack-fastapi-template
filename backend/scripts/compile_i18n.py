"""Compile i18n translation files."""

import subprocess
import sys
from pathlib import Path

from app.core.config import settings


def compile_translations() -> None:
    """Compile .po files to .mo files."""
    if not settings.I18N_ENABLED:
        print("i18n is disabled, skipping compilation")
        return

    locale_dir = Path(settings.I18N_LOCALE_DIR)
    if not locale_dir.exists():
        print(f"Locale directory {locale_dir} does not exist")
        return

    # Find all .po files
    po_files = list(locale_dir.rglob("*.po"))
    if not po_files:
        print("No .po files found")
        return

    # Compile each .po file
    for po_file in po_files:
        mo_file = po_file.with_suffix(".mo")
        try:
            # Use msgfmt to compile .po to .mo
            result = subprocess.run(
                ["msgfmt", "-o", str(mo_file), str(po_file)],
                check=True,
                capture_output=True,
                text=True,
            )
            print(f"Compiled: {po_file} -> {mo_file}")
        except subprocess.CalledProcessError as e:
            print(f"Error compiling {po_file}: {e.stderr}")
            sys.exit(1)
        except FileNotFoundError:
            print("msgfmt not found. Please install gettext tools:")
            print("  - Windows: Install gettext from https://mlocati.github.io/articles/gettext-iconv-windows.html")
            print("  - macOS: brew install gettext")
            print("  - Linux: apt-get install gettext")
            sys.exit(1)

    print("All translation files compiled successfully")


if __name__ == "__main__":
    compile_translations()
