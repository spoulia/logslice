"""Tests for logslice.alert."""

from __future__ import annotations

import pytest

from logslice.alert import (
    build_condition,
    evaluate_alerts,
    file_handler,
    stdout_handler,
)


def _entry(level: str = "info", message: str = "hello") -> dict:
    return {"level": level, "message": message, "timestamp": None, "source": None, "fields": {}}


# ---------------------------------------------------------------------------
# build_condition
# ---------------------------------------------------------------------------

class TestBuildCondition:
    def test_builtin_error_matches_error(self):
        cond = build_condition("error")
        assert cond(_entry(level="error")) is True

    def test_builtin_error_matches_critical(self):
        cond = build_condition("error")
        assert cond(_entry(level="CRITICAL")) is True

    def test_builtin_error_does_not_match_info(self):
        cond = build_condition("error")
        assert cond(_entry(level="info")) is False

    def test_builtin_warning_matches_warn(self):
        cond = build_condition("warning")
        assert cond(_entry(level="WARN")) is True

    def test_builtin_any_always_true(self):
        cond = build_condition("any")
        assert cond(_entry(level="debug")) is True

    def test_regex_pattern_matches_message(self):
        cond = build_condition(r"timeout")
        assert cond(_entry(message="connection timeout occurred")) is True

    def test_regex_pattern_no_match(self):
        cond = build_condition(r"timeout")
        assert cond(_entry(message="all good")) is False


# ---------------------------------------------------------------------------
# evaluate_alerts
# ---------------------------------------------------------------------------

class TestEvaluateAlerts:
    def test_returns_only_matching_entries(self):
        entries = [
            _entry(level="info"),
            _entry(level="error"),
            _entry(level="debug"),
            _entry(level="error", message="boom"),
        ]
        triggered = evaluate_alerts(entries, "error", handler=lambda _e: None)
        assert len(triggered) == 2

    def test_handler_called_for_each_match(self):
        calls = []
        entries = [_entry(level="error"), _entry(level="info"), _entry(level="error")]
        evaluate_alerts(entries, "error", handler=calls.append)
        assert len(calls) == 2

    def test_no_matches_returns_empty(self):
        entries = [_entry(level="info"), _entry(level="debug")]
        triggered = evaluate_alerts(entries, "error", handler=lambda _e: None)
        assert triggered == []

    def test_default_handler_is_stdout(self, capsys):
        entries = [_entry(level="error", message="oops")]
        evaluate_alerts(entries, "error")
        captured = capsys.readouterr()
        assert "oops" in captured.out

    def test_file_handler_writes_json(self, tmp_path):
        import json
        out = tmp_path / "alerts.jsonl"
        handler = file_handler(str(out))
        entries = [_entry(level="error", message="disk full")]
        evaluate_alerts(entries, "error", handler=handler)
        lines = out.read_text().splitlines()
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["message"] == "disk full"
