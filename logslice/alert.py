"""Alert module: trigger callbacks or write alerts when log entries match conditions."""

from __future__ import annotations

import json
from typing import Callable, Dict, Iterable, List, Optional

AlertHandler = Callable[[dict], None]

_BUILTIN_CONDITIONS = {
    "error": lambda entry: (entry.get("level") or "").lower() in ("error", "critical", "fatal"),
    "warning": lambda entry: (entry.get("level") or "").lower() in ("warning", "warn"),
    "any": lambda entry: True,
}


def _make_pattern_condition(pattern: str) -> Callable[[dict], bool]:
    import re
    rx = re.compile(pattern)
    return lambda entry: bool(rx.search(entry.get("message") or ""))


def build_condition(condition: str) -> Callable[[dict], bool]:
    """Return a callable that tests an entry against *condition*.

    *condition* may be a builtin name ("error", "warning", "any") or a
    regular-expression pattern matched against the entry message.
    """
    if condition in _BUILTIN_CONDITIONS:
        return _BUILTIN_CONDITIONS[condition]
    return _make_pattern_condition(condition)


def stdout_handler(entry: dict) -> None:
    """Default alert handler: prints a JSON line to stdout."""
    print(json.dumps(entry))


def file_handler(path: str) -> AlertHandler:
    """Return a handler that appends JSON lines to *path*."""
    def _handler(entry: dict) -> None:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
    return _handler


def evaluate_alerts(
    entries: Iterable[dict],
    condition: str,
    handler: Optional[AlertHandler] = None,
) -> List[dict]:
    """Iterate *entries*, invoke *handler* for every matching entry.

    Returns the list of entries that triggered the alert.
    """
    if handler is None:
        handler = stdout_handler
    test = build_condition(condition)
    triggered: List[dict] = []
    for entry in entries:
        if test(entry):
            handler(entry)
            triggered.append(entry)
    return triggered
