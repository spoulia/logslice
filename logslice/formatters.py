"""Output formatters for log entries."""

import json
from typing import Any, Dict, Optional


def format_plain(entry: Dict[str, Any]) -> str:
    """Format a log entry as plain text."""
    parts = []
    if entry.get("timestamp"):
        parts.append(str(entry["timestamp"]))
    if entry.get("level"):
        parts.append(f"[{entry['level'].upper()}]")
    if entry.get("message"):
        parts.append(entry["message"])
    elif entry.get("raw"):
        parts.append(entry["raw"])
    return " ".join(parts)


def format_json(entry: Dict[str, Any]) -> str:
    """Format a log entry as a JSON string."""
    output = {}
    if entry.get("timestamp"):
        output["timestamp"] = str(entry["timestamp"])
    if entry.get("level"):
        output["level"] = entry["level"]
    if entry.get("message"):
        output["message"] = entry["message"]
    elif entry.get("raw"):
        output["message"] = entry["raw"]
    if entry.get("fields"):
        output["fields"] = entry["fields"]
    return json.dumps(output)


def format_csv(entry: Dict[str, Any], delimiter: str = ",") -> str:
    """Format a log entry as a CSV row."""
    timestamp = str(entry.get("timestamp") or "")
    level = entry.get("level") or ""
    message = entry.get("message") or entry.get("raw") or ""
    # Escape delimiter in message
    message = message.replace('"', '""')
    if delimiter in message or '"' in message or '\n' in message:
        message = f'"{message}"'
    return delimiter.join([timestamp, level, message])


def get_formatter(fmt: str):
    """Return a formatter function by name."""
    formatters = {
        "plain": format_plain,
        "json": format_json,
        "csv": format_csv,
    }
    if fmt not in formatters:
        raise ValueError(f"Unknown format '{fmt}'. Choose from: {', '.join(formatters)}")
    return formatters[fmt]
