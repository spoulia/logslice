"""Field-level value validation for log entries."""

from __future__ import annotations

import re
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple


ValidationError = Tuple[str, str]  # (field, reason)


def _is_nonempty(value: Any) -> bool:
    return value is not None and str(value).strip() != ""


def _matches_regex(pattern: str) -> Callable[[Any], bool]:
    compiled = re.compile(pattern)
    return lambda value: bool(compiled.search(str(value)))


def _is_one_of(choices: List[str]) -> Callable[[Any], bool]:
    lower = [c.lower() for c in choices]
    return lambda value: str(value).lower() in lower


BUILTIN_VALIDATORS: Dict[str, Callable[[Any], bool]] = {
    "nonempty": _is_nonempty,
    "numeric": lambda v: str(v).lstrip("-").replace(".", "", 1).isdigit(),
    "alpha": lambda v: str(v).isalpha(),
    "alnum": lambda v: str(v).isalnum(),
}


def get_validator(name: str) -> Optional[Callable[[Any], bool]]:
    """Return a built-in validator by name, or None if unknown."""
    return BUILTIN_VALIDATORS.get(name)


def validate_entry(
    entry: Dict[str, Any],
    rules: Dict[str, List[str]],
) -> List[ValidationError]:
    """Validate a single entry against a dict of {field: [validator_name, ...]}.

    Returns a list of (field, reason) tuples for every failed check.
    """
    errors: List[ValidationError] = []
    for field, validators in rules.items():
        value = entry.get(field)
        for v_name in validators:
            if v_name.startswith("regex:"):
                pattern = v_name[len("regex:"):]
                ok = _matches_regex(pattern)(value) if value is not None else False
            elif v_name.startswith("oneof:"):
                choices = v_name[len("oneof:"):].split(",")
                ok = _is_one_of(choices)(value) if value is not None else False
            else:
                fn = get_validator(v_name)
                if fn is None:
                    continue
                ok = fn(value) if value is not None else False
            if not ok:
                errors.append((field, v_name))
    return errors


def filter_valid(
    entries: Iterable[Dict[str, Any]],
    rules: Dict[str, List[str]],
    strict: bool = False,
) -> Iterable[Dict[str, Any]]:
    """Yield entries that pass all validation rules.

    If *strict* is True, entries with any validation error are dropped.
    Otherwise only entries missing required fields entirely are dropped.
    """
    for entry in entries:
        errors = validate_entry(entry, rules)
        if strict and errors:
            continue
        if not strict and any(entry.get(f) is None for f in rules):
            continue
        yield entry
