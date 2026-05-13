"""Schema validation for structured log entries."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# Built-in schema presets
_BUILTIN_SCHEMAS: Dict[str, Dict[str, type]] = {
    "basic": {
        "message": str,
        "level": str,
    },
    "full": {
        "message": str,
        "level": str,
        "timestamp": str,
        "source": str,
    },
}


class SchemaError(ValueError):
    """Raised when an entry does not conform to a schema."""


def load_schema(name_or_fields: Any) -> Dict[str, type]:
    """Return a schema dict by preset name or pass through a dict.

    Args:
        name_or_fields: A preset name (str) or a mapping of field -> type.

    Returns:
        A dict mapping field names to expected Python types.

    Raises:
        KeyError: If a preset name is not found.
    """
    if isinstance(name_or_fields, str):
        return dict(_BUILTIN_SCHEMAS[name_or_fields])
    return dict(name_or_fields)


def validate_entry(
    entry: Dict[str, Any],
    schema: Dict[str, type],
    *,
    strict: bool = False,
) -> List[str]:
    """Validate a single entry against *schema*.

    Args:
        entry:  The log entry dict to validate.
        schema: Mapping of required field names to expected types.
        strict: If True, unknown fields in *entry* are also reported.

    Returns:
        A list of human-readable violation strings (empty = valid).
    """
    violations: List[str] = []

    for field, expected_type in schema.items():
        if field not in entry:
            violations.append(f"missing required field '{field}'")
        elif not isinstance(entry[field], expected_type):
            actual = type(entry[field]).__name__
            violations.append(
                f"field '{field}' expected {expected_type.__name__}, got {actual}"
            )

    if strict:
        known = set(schema)
        for key in entry:
            if key not in known:
                violations.append(f"unexpected field '{key}'")

    return violations


def filter_valid(
    entries: List[Dict[str, Any]],
    schema: Dict[str, type],
    *,
    strict: bool = False,
) -> List[Dict[str, Any]]:
    """Return only entries that pass schema validation."""
    return [e for e in entries if not validate_entry(e, schema, strict=strict)]


def available_schemas() -> List[str]:
    """Return names of built-in schema presets."""
    return list(_BUILTIN_SCHEMAS)
