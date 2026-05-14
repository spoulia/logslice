"""Field normalization utilities for log entries."""

from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, List, Optional

# Built-in normalizers
_NORMALIZERS: Dict[str, Callable[[Any], Any]] = {
    "lower": lambda v: v.lower() if isinstance(v, str) else v,
    "upper": lambda v: v.upper() if isinstance(v, str) else v,
    "strip": lambda v: v.strip() if isinstance(v, str) else v,
    "int": lambda v: int(v) if v is not None else v,
    "float": lambda v: float(v) if v is not None else v,
    "bool": lambda v: str(v).lower() in ("1", "true", "yes") if v is not None else False,
    "str": lambda v: str(v) if v is not None else "",
}


def get_normalizer(name: str) -> Optional[Callable[[Any], Any]]:
    """Return a built-in normalizer by name, or None if unknown."""
    return _NORMALIZERS.get(name)


def normalize_field(entry: Dict[str, Any], field: str, normalizer: str) -> Dict[str, Any]:
    """Apply a named normalizer to a single field in an entry.

    Returns a new dict; the original is not mutated.
    """
    fn = get_normalizer(normalizer)
    if fn is None:
        raise ValueError(f"Unknown normalizer: {normalizer!r}")
    result = dict(entry)
    if field in result:
        result[field] = fn(result[field])
    return result


def normalize_fields(
    entry: Dict[str, Any],
    spec: Dict[str, str],
) -> Dict[str, Any]:
    """Apply multiple normalizers described by *spec* (field -> normalizer name).

    Returns a new dict; the original is not mutated.
    """
    result = dict(entry)
    for field, normalizer in spec.items():
        fn = get_normalizer(normalizer)
        if fn is None:
            raise ValueError(f"Unknown normalizer: {normalizer!r}")
        if field in result:
            result[field] = fn(result[field])
    return result


def normalize_entries(
    entries: Iterable[Dict[str, Any]],
    spec: Dict[str, str],
) -> List[Dict[str, Any]]:
    """Apply *spec* normalizers to every entry in *entries*."""
    return [normalize_fields(e, spec) for e in entries]


def normalize_level(entry: Dict[str, Any], field: str = "level") -> Dict[str, Any]:
    """Convenience: uppercase the log level field."""
    return normalize_field(entry, field, "upper")
