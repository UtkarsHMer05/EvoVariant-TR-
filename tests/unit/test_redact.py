"""Tests for evovariant_tr.redact — Milestone 19.

Covers log redaction (Validation 1 support: secrets never reach logs).

All token-shaped fixtures are built by concatenation so that no
credential-shaped literal ever appears in tracked files; otherwise the
repository's own secret scanner (scripts/check_secrets.sh) would flag them.
"""

from __future__ import annotations

import logging

from evovariant_tr.redact import REDACTED, RedactingFilter, redact

FAKE_SK = "sk-" + "abcdefghijklmnopqrstuvwxyz1234"
FAKE_SK_PROJ = "sk-" + "proj-" + "abcdefghijklmnopqrstuvwxyz1234"
FAKE_GHP = "ghp_" + "abcdefghijklmnopqrstuvwxyz1234"
FAKE_AKIA = "AKIA" + "IOSFODNN7EXAMPLE"
FAKE_XOXB = "xox" + "b-" + "1234567890abcdefghij"
FAKE_XOXB_DASHED = "xox" + "b-" + "1234567890" + "-" + "abcdefghijklmnopqrstuvwxyz"
FAKE_ALNUM = "abcdef" + "1234567890"
FAKE_PASSWORD = "p@ssw0rd" + "12345678"


# --------------------------------------------------------------------------- #
#  Happy path: key=value / key: value style secrets
# --------------------------------------------------------------------------- #
def test_redact_key_value_secret():
    out = redact(f"TOKEN={FAKE_SK}")
    assert FAKE_SK not in out
    assert REDACTED in out


def test_redact_key_value_with_quotes():
    out = redact(f"API_KEY='{FAKE_SK}'")
    assert REDACTED in out
    assert "sk-" not in out


def test_redact_bearer_token():
    out = redact(f"Authorization: Bearer {FAKE_GHP}")
    assert FAKE_GHP not in out
    assert REDACTED in out


def test_redact_lowercase_key():
    out = redact(f"my_secret_token={FAKE_XOXB}")
    assert FAKE_XOXB not in out
    assert REDACTED in out


def test_redact_multiple_secrets():
    out = redact(f"TOKEN={FAKE_ALNUM} and PASSWORD={FAKE_PASSWORD}")
    assert FAKE_ALNUM not in out
    assert FAKE_PASSWORD not in out
    assert out.count(REDACTED) == 2


# --------------------------------------------------------------------------- #
#  Happy path: bare token shapes
# --------------------------------------------------------------------------- #
def test_redact_openai_key():
    assert redact(FAKE_SK_PROJ) == REDACTED


def test_redact_github_pat():
    assert redact(FAKE_GHP) == REDACTED


def test_redact_aws_key():
    assert redact(FAKE_AKIA) == REDACTED


def test_redact_slack_token():
    assert redact(FAKE_XOXB_DASHED) == REDACTED


# --------------------------------------------------------------------------- #
#  Invalid input: non-secret strings are unchanged
# --------------------------------------------------------------------------- #
def test_redact_plain_text_unchanged():
    text = "hello world, this is a normal log message"
    assert redact(text) == text


def test_redact_short_value_not_treated_as_secret():
    """A short assignment (e.g. a code variable) should not be redacted."""
    text = "_TOKEN_VAR = frozenset("
    out = redact(text)
    assert "frozenset" in out


def test_redact_no_redacted_marker_in_clean_text():
    text = "chromosome 1 position 12345 ref A alt T"
    assert REDACTED not in redact(text)


# --------------------------------------------------------------------------- #
#  Boundary: empty / non-string
# --------------------------------------------------------------------------- #
def test_redact_empty_string():
    assert redact("") == ""


# --------------------------------------------------------------------------- #
#  Repetition: deterministic
# --------------------------------------------------------------------------- #
def test_redact_is_deterministic():
    text = f"TOKEN={FAKE_SK} BEARER {FAKE_XOXB}"
    first = redact(text)
    second = redact(text)
    assert first == second


# --------------------------------------------------------------------------- #
#  RedactingFilter integrates with logging
# --------------------------------------------------------------------------- #
def test_redacting_filter_in_logger(caplog):
    logger = logging.getLogger("test_redact_filter")
    logger.addFilter(RedactingFilter())
    with caplog.at_level(logging.DEBUG, logger="test_redact_filter"):
        logger.info(f"TOKEN={FAKE_SK}")
    # The captured record must not contain the raw token.
    assert FAKE_SK not in caplog.text
    assert REDACTED in caplog.text


def test_redacting_filter_with_args(caplog):
    """String arguments in log records must also be redacted."""
    logger = logging.getLogger("test_redact_filter_args")
    logger.addFilter(RedactingFilter())
    with caplog.at_level(logging.DEBUG, logger="test_redact_filter_args"):
        logger.info("status=%s", f"TOKEN={FAKE_SK}")
    assert FAKE_SK not in caplog.text
    assert REDACTED in caplog.text
