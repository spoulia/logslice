"""Terminal color highlighting for log entries."""

import re
from typing import Optional

ANSI_RESET = "\033[0m"

LEVEL_COLORS = {
    "debug": "\033[36m",    # cyan
    "info": "\033[32m",     # green
    "warning": "\033[33m",  # yellow
    "warn": "\033[33m",     # yellow
    "error": "\033[31m",    # red
    "critical": "\033[35m", # magenta
    "fatal": "\033[35m",    # magenta
}

PATTERN_COLOR = "\033[1;33m"  # bold yellow for pattern matches


def colorize_level(level: str) -> str:
    """Wrap a log level string in its corresponding ANSI color."""
    color = LEVEL_COLORS.get(level.lower(), "")
    if not color:
        return level
    return f"{color}{level}{ANSI_RESET}"


def highlight_pattern(text: str, pattern: str) -> str:
    """Highlight all occurrences of pattern in text with bold yellow."""
    if not pattern:
        return text
    try:
        highlighted = re.sub(
            f"({re.escape(pattern)})",
            f"{PATTERN_COLOR}\\1{ANSI_RESET}",
            text,
            flags=re.IGNORECASE,
        )
        return highlighted
    except re.error:
        return text


def highlight_entry(entry: dict, pattern: Optional[str] = None, use_color: bool = True) -> str:
    """Format a log entry as a colored string for terminal output."""
    if not use_color:
        parts = []
        if entry.get("timestamp"):
            parts.append(entry["timestamp"])
        if entry.get("level"):
            parts.append(f"[{entry['level'].upper()}]")
        parts.append(entry.get("message", ""))
        return " ".join(parts)

    parts = []
    if entry.get("timestamp"):
        parts.append(f"\033[90m{entry['timestamp']}{ANSI_RESET}")
    if entry.get("level"):
        parts.append(f"[{colorize_level(entry['level'].upper())}]")
    message = entry.get("message", "")
    if pattern:
        message = highlight_pattern(message, pattern)
    parts.append(message)
    return " ".join(parts)


def supports_color() -> bool:
    """Check whether the current terminal likely supports ANSI color codes."""
    import sys
    import os
    if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
        return False
    term = os.environ.get("TERM", "")
    if term == "dumb":
        return False
    return True
