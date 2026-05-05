"""Tests for logslice.highlight module."""

import pytest
from logslice.highlight import (
    colorize_level,
    highlight_pattern,
    highlight_entry,
    ANSI_RESET,
    LEVEL_COLORS,
)


class TestColorizeLevel:
    def test_known_level_info(self):
        result = colorize_level("info")
        assert LEVEL_COLORS["info"] in result
        assert ANSI_RESET in result
        assert "info" in result

    def test_known_level_error(self):
        result = colorize_level("error")
        assert LEVEL_COLORS["error"] in result

    def test_unknown_level_returned_as_is(self):
        result = colorize_level("verbose")
        assert result == "verbose"

    def test_case_insensitive(self):
        result_lower = colorize_level("warning")
        result_upper = colorize_level("WARNING")
        assert LEVEL_COLORS["warning"] in result_lower
        assert LEVEL_COLORS["warning"] in result_upper


class TestHighlightPattern:
    def test_pattern_wrapped_in_color(self):
        result = highlight_pattern("found error here", "error")
        assert "error" in result
        assert ANSI_RESET in result

    def test_empty_pattern_returns_original(self):
        text = "no change expected"
        assert highlight_pattern(text, "") == text

    def test_case_insensitive_match(self):
        result = highlight_pattern("ERROR occurred", "error")
        assert "ERROR" in result
        assert ANSI_RESET in result

    def test_no_match_returns_original(self):
        text = "nothing to see here"
        result = highlight_pattern(text, "xyz123")
        assert result == text


class TestHighlightEntry:
    def _entry(self, **kwargs):
        base = {"timestamp": "2024-01-01T00:00:00", "level": "info", "message": "hello"}
        base.update(kwargs)
        return base

    def test_no_color_plain_format(self):
        entry = self._entry()
        result = highlight_entry(entry, use_color=False)
        assert "2024-01-01T00:00:00" in result
        assert "INFO" in result
        assert "hello" in result
        assert "\033[" not in result

    def test_with_color_contains_ansi(self):
        entry = self._entry(level="error")
        result = highlight_entry(entry, use_color=True)
        assert "\033[" in result
        assert ANSI_RESET in result

    def test_pattern_highlighted_in_message(self):
        entry = self._entry(message="connection timeout occurred")
        result = highlight_entry(entry, pattern="timeout", use_color=True)
        assert "timeout" in result
        assert ANSI_RESET in result

    def test_missing_timestamp_skipped(self):
        entry = {"level": "info", "message": "no ts"}
        result = highlight_entry(entry, use_color=False)
        assert "INFO" in result
        assert "no ts" in result

    def test_missing_level_skipped(self):
        entry = {"timestamp": "2024-01-01", "message": "no level"}
        result = highlight_entry(entry, use_color=False)
        assert "[" not in result
        assert "no level" in result
