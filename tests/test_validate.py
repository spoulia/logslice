"""Tests for logslice.validate."""

from __future__ import annotations

import pytest

from logslice.validate import (
    filter_valid,
    get_validator,
    validate_entry,
)


def _e(**kwargs):
    base = {"message": "hello", "level": "info", "timestamp": "2024-01-01T00:00:00Z"}
    base.update(kwargs)
    return base


# ---------------------------------------------------------------------------
# get_validator
# ---------------------------------------------------------------------------

class TestGetValidator:
    def test_nonempty_exists(self):
        assert get_validator("nonempty") is not None

    def test_numeric_exists(self):
        assert get_validator("numeric") is not None

    def test_unknown_returns_none(self):
        assert get_validator("nonexistent_xyz") is None

    def test_nonempty_passes_for_value(self):
        fn = get_validator("nonempty")
        assert fn("hello") is True

    def test_nonempty_fails_for_blank(self):
        fn = get_validator("nonempty")
        assert fn("   ") is False

    def test_numeric_passes_for_int_string(self):
        fn = get_validator("numeric")
        assert fn("42") is True

    def test_numeric_fails_for_alpha(self):
        fn = get_validator("numeric")
        assert fn("abc") is False


# ---------------------------------------------------------------------------
# validate_entry
# ---------------------------------------------------------------------------

class TestValidateEntry:
    def test_no_errors_for_valid_entry(self):
        entry = _e(message="hello")
        errors = validate_entry(entry, {"message": ["nonempty"]})
        assert errors == []

    def test_error_for_blank_message(self):
        entry = _e(message="   ")
        errors = validate_entry(entry, {"message": ["nonempty"]})
        assert len(errors) == 1
        assert errors[0][0] == "message"

    def test_missing_field_counts_as_failure(self):
        entry = {"level": "info"}
        errors = validate_entry(entry, {"message": ["nonempty"]})
        assert any(f == "message" for f, _ in errors)

    def test_regex_validator_passes(self):
        entry = _e(level="ERROR")
        errors = validate_entry(entry, {"level": ["regex:^(ERROR|INFO|WARN)$"]})
        assert errors == []

    def test_regex_validator_fails(self):
        entry = _e(level="VERBOSE")
        errors = validate_entry(entry, {"level": ["regex:^(ERROR|INFO|WARN)$"]})
        assert len(errors) == 1

    def test_oneof_validator_passes(self):
        entry = _e(level="info")
        errors = validate_entry(entry, {"level": ["oneof:info,warn,error"]})
        assert errors == []

    def test_oneof_validator_fails(self):
        entry = _e(level="trace")
        errors = validate_entry(entry, {"level": ["oneof:info,warn,error"]})
        assert len(errors) == 1

    def test_unknown_validator_skipped(self):
        entry = _e()
        errors = validate_entry(entry, {"message": ["unknown_rule"]})
        assert errors == []

    def test_multiple_rules_multiple_errors(self):
        entry = {"message": "", "level": "bad"}
        rules = {
            "message": ["nonempty"],
            "level": ["oneof:info,warn,error"],
        }
        errors = validate_entry(entry, rules)
        assert len(errors) == 2


# ---------------------------------------------------------------------------
# filter_valid
# ---------------------------------------------------------------------------

class TestFilterValid:
    def test_passes_valid_entries(self):
        entries = [_e(message="ok"), _e(message="also ok")]
        result = list(filter_valid(entries, {"message": ["nonempty"]}))
        assert len(result) == 2

    def test_drops_entry_missing_field_in_non_strict(self):
        entries = [{"level": "info"}, _e(message="good")]
        result = list(filter_valid(entries, {"message": ["nonempty"]}))
        assert len(result) == 1

    def test_strict_drops_invalid_entries(self):
        entries = [_e(message=""), _e(message="valid")]
        result = list(filter_valid(entries, {"message": ["nonempty"]}, strict=True))
        assert len(result) == 1
        assert result[0]["message"] == "valid"

    def test_empty_input_returns_empty(self):
        result = list(filter_valid([], {"message": ["nonempty"]}))
        assert result == []
