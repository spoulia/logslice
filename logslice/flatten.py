"""
logslice.flatten
~~~~~~~~~~~~~~~~
Flatten nested log entry dicts into a single-level dict with
dot-separated keys, and unflatten them back.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List


def flatten_entry(
    entry: Dict[str, Any],
    sep: str = ".",
    prefix: str = "",
) -> Dict[str, Any]:
    """Return a new dict where nested keys are joined by *sep*.

    Example::

        >>> flatten_entry({"a": {"b": 1}})
        {'a.b': 1}
    """
    result: Dict[str, Any] = {}
    for key, value in entry.items():
        full_key = f"{prefix}{sep}{key}" if prefix else key
        if isinstance(value, dict):
            result.update(flatten_entry(value, sep=sep, prefix=full_key))
        else:
            result[full_key] = value
    return result


def unflatten_entry(
    entry: Dict[str, Any],
    sep: str = ".",
) -> Dict[str, Any]:
    """Reconstruct a nested dict from a flat dot-separated dict.

    Example::

        >>> unflatten_entry({'a.b': 1})
        {'a': {'b': 1}}
    """
    result: Dict[str, Any] = {}
    for compound_key, value in entry.items():
        parts = compound_key.split(sep)
        target = result
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        target[parts[-1]] = value
    return result


def flatten_entries(
    entries: Iterable[Dict[str, Any]],
    sep: str = ".",
) -> List[Dict[str, Any]]:
    """Apply :func:`flatten_entry` to every entry in *entries*."""
    return [flatten_entry(e, sep=sep) for e in entries]


def unflatten_entries(
    entries: Iterable[Dict[str, Any]],
    sep: str = ".",
) -> List[Dict[str, Any]]:
    """Apply :func:`unflatten_entry` to every entry in *entries*."""
    return [unflatten_entry(e, sep=sep) for e in entries]
