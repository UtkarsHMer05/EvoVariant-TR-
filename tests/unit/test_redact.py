"""Tests for evovariant_tr.redact — Milestone 19.

Covers log redaction (Validation 1 support: secrets never reach logs).
"""

from __future__ import annotations

import logging

from evovariant_tr.redact import REDACTED, RedactingFilter, redact


# --------------------------------------------------------------------------- #
#  Happy path: key=value / key: value style secrets
# --------------------------------------------------------------------------- #
def test_redact_key_value_secret():
    out = redact("TOKEN=sk-abcdefghijklmnopqrstuvwxyz1234")
    assert "sk-abcdefghijklmnopqrstuvwxyz1234" not in out
    assert REDACTED in out


def test_redact_key_value_with_quotes():
    out = redact("API_KEY='sk-abcdefghijklmnopqrstuvwxyz1234'")
    assert REDACTED in out
    assert "sk-" not in out


def test_redact_bearer_token():
    out = redact("Authorization: Bearer ghp_abcdefghijklmnopqrstuvwxyz1234")
    assert "ghp_abcdefghijklmnopqrstuvwxyz1234" not in out
    assert REDACTED in out


def test_redact_lowercase_key():
    out = redact("my_secret_token=xoxb-1234567890abcdefghij")
    assert "xoxb-1234567890abcdefghij" not in out
    assert REDACTED in out


def test_redact_multiple_secrets():
    out = redact("TOKEN=abcdef1234567890 and PASSWORD=p@ssw0rd12345678")
    assert "abcdef1234567890" not in out
    assert "p@ssw0rd12345678" not in out
    assert out.count(REDACTED) == 2


# --------------------------------------------------------------------------- #
#  Happy path: bare token shapes
# --------------------------------------------------------------------------- #
def test_redact_openai_key():
    key = "sk-proj-abcdefghijklmnopqrstuvwxyz1234"
    assert redact(key) == REDACTED


def test_redact_github_pat():
    pat = "ghp_abcdefghijklmnopqrstuvwxyz1234"
    assert redact(pat) == REDACTED


def test_redact_aws_key():
    k = "AKIAIOSFODNN7EXAMPLE"
    assert redact(k) == REDACTED


def test_redact_slack_token():
    t = "XOXB_REMOVED"
    assert redact(t) == REDACTED


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
    text = "TOKEN=sk-abcdefghijklmnopqrstuvwxyz1234 BEARER xoxb-1234567890abc"
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
        logger.info("TOKEN=sk-abcdefghijklmnopqrstuvwxyz1234")
    # The captured record must not contain the raw token.
    assert "sk-abcdefghijklmnopqrstuvwxyz1234" not in caplog.text
    assert REDACTED in caplog.text


def test_redacting_filter_with_args(caplog):
    """String arguments in log records must also be redacted."""
    logger = logging.getLogger("test_redact_filter_args")
    logger.addFilter(RedactingFilter())
    with caplog.at_level(logging.DEBUG, logger="test_redact_filter_args"):
        logger.info("status=%s", "TOKEN=sk-abcdefghijklmnopqrstuvwxyz1234")
    assert "sk-abcdefghijklmnopqrstuvwxyz1234" not in caplog.text
    assert REDACTED in caplog.text
