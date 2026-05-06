"""Redaction utilities for masking sensitive fields in log entries."""

import re
from typing import Any, Dict, List, Optional

# Default patterns to redact: emails, IPs, tokens, credit-card-like numbers
DEFAULT_PATTERNS: List[str] = [
    r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b',  # email
    r'\b(?:\d{1,3}\.){3}\d{1,3}\b',                             # IPv4
    r'\b[A-Fa-f0-9]{32,}\b',                                     # hex token
    r'\b(?:\d[ -]?){13,16}\b',                                   # credit-card-like
]

PLACEHOLDER = "[REDACTED]"


def redact_string(
    text: str,
    patterns: Optional[List[str]] = None,
    placeholder: str = PLACEHOLDER,
) -> str:
    """Replace all matches of *patterns* in *text* with *placeholder*."""
    if patterns is None:
        patterns = DEFAULT_PATTERNS
    for pat in patterns:
        text = re.sub(pat, placeholder, text)
    return text


def redact_fields(
    entry: Dict[str, Any],
    fields: List[str],
    placeholder: str = PLACEHOLDER,
) -> Dict[str, Any]:
    """Overwrite specific *fields* in *entry* with *placeholder*."""
    result = dict(entry)
    for field in fields:
        if field in result:
            result[field] = placeholder
    return result


def redact_entry(
    entry: Dict[str, Any],
    patterns: Optional[List[str]] = None,
    fields: Optional[List[str]] = None,
    placeholder: str = PLACEHOLDER,
) -> Dict[str, Any]:
    """Apply pattern-based and field-based redaction to a log entry dict.

    - *patterns*: regex patterns applied to the ``message`` field (and any
      string-valued field not explicitly listed in *fields*).
    - *fields*: field names whose values are replaced wholesale.
    """
    result = dict(entry)

    # Field-level redaction first
    if fields:
        result = redact_fields(result, fields, placeholder)

    # Pattern-level redaction over all remaining string fields
    active_patterns = patterns if patterns is not None else DEFAULT_PATTERNS
    for key, value in result.items():
        if isinstance(value, str):
            result[key] = redact_string(value, active_patterns, placeholder)

    return result
