"""Log diff: compare two sequences of log entries and surface differences."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

Entry = Dict[str, Any]


def _entry_signature(entry: Entry, fields: List[str]) -> Tuple:
    """Return a hashable signature for an entry based on selected fields."""
    return tuple(entry.get(f) for f in fields)


def diff_entries(
    left: List[Entry],
    right: List[Entry],
    fields: List[str] | None = None,
) -> Dict[str, List[Entry]]:
    """Compare two entry lists and return added, removed, and common entries.

    Args:
        left:   Baseline entry list (e.g. older log).
        right:  Comparison entry list (e.g. newer log).
        fields: Fields used to compute entry identity.  Defaults to
                ``["message", "level"]``.

    Returns:
        A dict with keys ``"added"``, ``"removed"``, and ``"common"``.
    """
    if fields is None:
        fields = ["message", "level"]

    left_sigs = {_entry_signature(e, fields): e for e in left}
    right_sigs = {_entry_signature(e, fields): e for e in right}

    added = [right_sigs[s] for s in right_sigs if s not in left_sigs]
    removed = [left_sigs[s] for s in left_sigs if s not in right_sigs]
    common = [left_sigs[s] for s in left_sigs if s in right_sigs]

    return {"added": added, "removed": removed, "common": common}


def diff_summary(result: Dict[str, List[Entry]]) -> Dict[str, int]:
    """Return a concise count summary of a diff result."""
    return {
        "added": len(result.get("added", [])),
        "removed": len(result.get("removed", [])),
        "common": len(result.get("common", [])),
    }


def format_diff_text(result: Dict[str, List[Entry]], message_field: str = "message") -> str:
    """Render a human-readable diff report."""
    lines: List[str] = []
    for entry in result.get("added", []):
        lines.append(f"+ {entry.get(message_field, '<no message>')}")
    for entry in result.get("removed", []):
        lines.append(f"- {entry.get(message_field, '<no message>')}")
    if not lines:
        lines.append("  (no differences)")
    summary = diff_summary(result)
    lines.append(
        f"\n  added={summary['added']}  removed={summary['removed']}  common={summary['common']}"
    )
    return "\n".join(lines)
