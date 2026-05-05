"""Log statistics and summary reporting module."""

from collections import Counter, defaultdict
from typing import List, Dict, Any, Optional


LEVEL_ORDER = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def compute_stats(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute summary statistics from a list of parsed log entries."""
    if not entries:
        return {
            "total": 0,
            "by_level": {},
            "by_source": {},
            "first_timestamp": None,
            "last_timestamp": None,
            "error_rate": 0.0,
        }

    level_counts: Counter = Counter()
    source_counts: Counter = Counter()
    timestamps = []

    for entry in entries:
        level = (entry.get("level") or "UNKNOWN").upper()
        level_counts[level] += 1

        source = entry.get("source") or entry.get("logger") or "unknown"
        source_counts[source] += 1

        ts = entry.get("timestamp")
        if ts:
            timestamps.append(ts)

    total = len(entries)
    error_count = level_counts.get("ERROR", 0) + level_counts.get("CRITICAL", 0)

    return {
        "total": total,
        "by_level": dict(level_counts),
        "by_source": dict(source_counts),
        "first_timestamp": min(timestamps) if timestamps else None,
        "last_timestamp": max(timestamps) if timestamps else None,
        "error_rate": round(error_count / total, 4) if total > 0 else 0.0,
    }


def format_stats_text(stats: Dict[str, Any]) -> str:
    """Format statistics as a human-readable text summary."""
    lines = ["=== Log Statistics ==="]
    lines.append(f"Total entries : {stats['total']}")
    lines.append(f"Error rate    : {stats['error_rate'] * 100:.2f}%")

    if stats["first_timestamp"]:
        lines.append(f"From          : {stats['first_timestamp']}")
        lines.append(f"To            : {stats['last_timestamp']}")

    lines.append("")
    lines.append("By level:")
    for level in LEVEL_ORDER:
        count = stats["by_level"].get(level, 0)
        if count:
            lines.append(f"  {level:<10} {count}")
    for level, count in stats["by_level"].items():
        if level not in LEVEL_ORDER:
            lines.append(f"  {level:<10} {count}")

    if stats["by_source"]:
        lines.append("")
        lines.append("By source (top 5):")
        top_sources = sorted(stats["by_source"].items(), key=lambda x: -x[1])[:5]
        for src, count in top_sources:
            lines.append(f"  {src:<30} {count}")

    return "\n".join(lines)
