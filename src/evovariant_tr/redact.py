"""Token redaction for logs and reports.

Any string routed through :func:`redact` (or a logger using
:class:`RedactingFilter`) has credential-looking substrings replaced so tokens
never reach log files, reports, or UI surfaces.
"""

from __future__ import annotations

import logging
import re

REDACTED = "***REDACTED***"

# key=value / key: value assignments where the key names a secret.
# Requires a minimum 16-char value so short code-like values (e.g.
# ``_TOKEN_VAR = frozenset(``) are not redacted. This mirrors the same
# length threshold used by scripts/check_secrets.sh to avoid false positives.
_KEY_VALUE = re.compile(
    r"(?i)\b([A-Z0-9_]*(?:TOKEN|SECRET|PASSWORD|PASSWD|API_?KEY|CREDENTIAL)"
    r"[A-Z0-9_]*\s*[:=]\s*)\S{16,}"
)
_BEARER = re.compile(r"(?i)(\bbearer\s+)\S+")

# Bare well-known token shapes.
_BARE_TOKENS = (
    re.compile(r"\bsk-[A-Za-z0-9_\-]{16,}\b"),  # OpenAI/Anthropic style
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),  # GitHub PAT
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),  # AWS access key id
    re.compile(r"\bxox[baprs]-[A-Za-z0-9\-]{10,}\b"),  # Slack
)


def redact(text: str) -> str:
    """Replace credential-looking substrings with ``***REDACTED***``."""
    out = _KEY_VALUE.sub(rf"\g<1>{REDACTED}", text)
    out = _BEARER.sub(rf"\g<1>{REDACTED}", out)
    for pattern in _BARE_TOKENS:
        out = pattern.sub(REDACTED, out)
    return out


class RedactingFilter(logging.Filter):
    """Logging filter that redacts the message and string arguments."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact(record.msg)
        if record.args:
            args = record.args if isinstance(record.args, tuple) else (record.args,)
            record.args = tuple(
                redact(arg) if isinstance(arg, str) else arg for arg in args
            )
        return True
