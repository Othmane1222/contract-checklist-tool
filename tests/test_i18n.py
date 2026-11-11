
import html
import json
import re
from pathlib import Path

import pytest

from errors import ERROR_MESSAGES

I18N_DIR = Path(__file__).parent.parent / "static" / "i18n"
LANGUAGES = ("en", "es", "zh")
PLACEHOLDER = re.compile(r"\{(\w+)\}")
HTML_TAG = re.compile(r"<[a-zA-Z/!]")


def load(language):
    with (I18N_DIR / f"{language}.json").open(encoding="utf-8") as file:
        return json.load(file)


def public_keys(translations):
    return {key for key in translations if not key.startswith("_")}


ENGLISH = load("en")


@pytest.mark.parametrize("language", LANGUAGES)
def test_same_keys_as_english(language):
    assert public_keys(load(language)) == public_keys(ENGLISH)


@pytest.mark.parametrize("language", LANGUAGES)
def test_same_placeholders_as_english(language):
    translations = load(language)
    for key in public_keys(ENGLISH):
        expected = set(PLACEHOLDER.findall(ENGLISH[key]))
        assert set(PLACEHOLDER.findall(translations[key])) == expected, f"{language}: {key}"


@pytest.mark.parametrize("language", LANGUAGES)
def test_no_html_in_translations(language):
    for key, value in load(language).items():
        if not key.startswith("_"):
            assert not HTML_TAG.search(value), f"{language}: {key}"


@pytest.mark.parametrize("language", LANGUAGES)
def test_every_server_error_code_is_translated(language):
    translations = load(language)
    for code in ERROR_MESSAGES:
        assert f"error.{code}" in translations, f"{language}: error.{code}"


def test_english_error_placeholders_match_server_messages():
    for code, message in ERROR_MESSAGES.items():
        expected = set(PLACEHOLDER.findall(message))
        assert set(PLACEHOLDER.findall(ENGLISH[f"error.{code}"])) == expected, code


@pytest.mark.parametrize("language", LANGUAGES)
def test_lawyer_review_keys_exist(language):
    translations = load(language)
    review = translations.get("_needs_lawyer_review", [])
    assert "disclaimer" in review
    assert "contact.consent" in review
    for key in review:
        assert key in translations, f"{language}: {key}"



STATIC_DIR = I18N_DIR.parent
USED_IN_HTML = re.compile(r'data-i18n="([^"]+)"')
USED_IN_JS = re.compile(r'\bt\("([\w.]+)"')


def test_every_key_used_by_the_pages_exists():
    used = set()
    for path in STATIC_DIR.glob("*.html"):
        used |= set(USED_IN_HTML.findall(path.read_text(encoding="utf-8")))
    for path in STATIC_DIR.glob("*.js"):
        used |= set(USED_IN_JS.findall(path.read_text(encoding="utf-8")))
    missing = sorted(used - public_keys(ENGLISH))
    assert not missing, missing
    

FALLBACK_TEXT = re.compile(r'data-i18n="([^"]+)"[^>]*>([^<]*)<')


def test_html_fallback_text_matches_english():
    mismatches = []
    for path in STATIC_DIR.glob("*.html"):
        for key, text in FALLBACK_TEXT.findall(path.read_text(encoding="utf-8")):
            text = html.unescape(text.strip())
            if text and text != ENGLISH.get(key):
                mismatches.append(f"{path.name}: {key}")
    assert not mismatches, mismatches