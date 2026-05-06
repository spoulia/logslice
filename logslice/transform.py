"""Field transformation utilities for log entries."""

from typing import Any, Callable, Dict, List, Optional

# Built-in transformers
_TRANSFORMERS: Dict[str, Callable[[Any], Any]] = {
    "upper": lambda v: v.upper() if isinstance(v, str) else v,
    "lower": lambda v: v.lower() if isinstance(v, str) else v,
    "strip": lambda v: v.strip() if isinstance(v, str) else v,
    "int": lambda v: int(v),
    "float": lambda v: float(v),
    "bool": lambda v: v.lower() in ("true", "1", "yes") if isinstance(v, str) else bool(v),
    "truncate": lambda v: v[:64] if isinstance(v, str) else v,
}


def get_transformer(name: str) -> Optional[Callable[[Any], Any]]:
    """Return a built-in transformer by name, or None if not found."""
    return _TRANSFORMERS.get(name)


def transform_field(entry: Dict[str, Any], field: str, transformer_name: str) -> Dict[str, Any]:
    """Apply a named transformer to a single field in an entry.

    Returns a new entry dict with the field transformed.
    Leaves the entry unchanged if the field is missing or transformer unknown.
    """
    transformer = get_transformer(transformer_name)
    if transformer is None:
        raise ValueError(f"Unknown transformer: {transformer_name!r}")

    if field not in entry:
        return dict(entry)

    result = dict(entry)
    try:
        result[field] = transformer(entry[field])
    except (ValueError, TypeError, AttributeError):
        pass  # Leave original value on conversion failure
    return result


def transform_fields(
    entry: Dict[str, Any],
    rules: List[Dict[str, str]],
) -> Dict[str, Any]:
    """Apply multiple transformation rules to an entry.

    Each rule is a dict with 'field' and 'transform' keys.
    Rules are applied in order.
    """
    result = dict(entry)
    for rule in rules:
        field = rule.get("field", "")
        transformer_name = rule.get("transform", "")
        if field and transformer_name:
            result = transform_field(result, field, transformer_name)
    return result


def transform_entries(
    entries: List[Dict[str, Any]],
    rules: List[Dict[str, str]],
) -> List[Dict[str, Any]]:
    """Apply transformation rules to a list of log entries."""
    return [transform_fields(entry, rules) for entry in entries]


def rename_field(entry: Dict[str, Any], old_name: str, new_name: str) -> Dict[str, Any]:
    """Rename a field in an entry, returning a new dict."""
    if old_name not in entry:
        return dict(entry)
    result = dict(entry)
    result[new_name] = result.pop(old_name)
    return result


def drop_fields(entry: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
    """Return a new entry with specified fields removed."""
    return {k: v for k, v in entry.items() if k not in fields}
