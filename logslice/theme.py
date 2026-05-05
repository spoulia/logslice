"""Color theme configuration for logslice highlighting."""

from typing import Dict, Optional

DEFAULT_THEME: Dict[str, str] = {
    "debug": "\033[36m",
    "info": "\033[32m",
    "warning": "\033[33m",
    "warn": "\033[33m",
    "error": "\033[31m",
    "critical": "\033[35m",
    "fatal": "\033[35m",
    "timestamp": "\033[90m",
    "pattern": "\033[1;33m",
    "reset": "\033[0m",
}

MONO_THEME: Dict[str, str] = {key: "" for key in DEFAULT_THEME}

_BUILTIN_THEMES = {
    "default": DEFAULT_THEME,
    "mono": MONO_THEME,
}

_active_theme: Dict[str, str] = dict(DEFAULT_THEME)


def load_theme(name: str) -> None:
    """Switch the active theme by name. Raises ValueError for unknown themes."""
    global _active_theme
    if name not in _BUILTIN_THEMES:
        raise ValueError(f"Unknown theme: '{name}'. Available: {list(_BUILTIN_THEMES)}.")
    _active_theme = dict(_BUILTIN_THEMES[name])


def get_color(key: str) -> str:
    """Return the ANSI escape code for a given theme key, or empty string."""
    return _active_theme.get(key.lower(), "")


def get_reset() -> str:
    """Return the reset ANSI code from the active theme."""
    return _active_theme.get("reset", "")


def available_themes() -> list:
    """Return the list of available built-in theme names."""
    return list(_BUILTIN_THEMES.keys())


def apply_custom_theme(overrides: Dict[str, str]) -> None:
    """Merge custom color overrides into the active theme."""
    global _active_theme
    _active_theme.update(overrides)
