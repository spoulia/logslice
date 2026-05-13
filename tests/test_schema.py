"""Tests for logslice.schema."""

from __future__ import annotations

import pytest

from logslice.schema import (
    available_schemas,
    filter_valid,
    load_schema,
    validate_entry,
)


# ---------------------------------------------------------------------------
# load_schema
# ---------------------------------------------------------------------------

class TestLoadSchema:
    def test_builtin_basic_returns_dict(self):
        s = load_schema("basic")
        assert isinstance(s, dict)
        assert "message" in s

    def test_builtin_full_has_timestamp(self):
        s = load_schema("full")
        assert "timestamp" in s

    def test_unknown_preset_raises(self):
        with pytest.raises(KeyError):
            load_schema("nonexistent_preset")

    def test_passthrough_dict(self):
        custom = {"foo": str, "bar": int}
        assert load_schema(custom) == custom

    def test_returns_copy(self):
        s1 = load_schema("basic")
        s1["extra"] = str
        s2 = load_schema("basic")
        assert "extra" not in s2


# ---------------------------------------------------------------------------
# validate_entry
# ---------------------------------------------------------------------------

class TestValidateEntry:
    _schema = {"message": str, "level": str}

    def test_valid_entry_returns_empty(self):
        entry = {"message": "hello", "level": "INFO"}
        assert validate_entry(entry, self._schema) == []

    def test_missing_field_reported(self):
        entry = {"message": "hello"}
        violations = validate_entry(entry, self._schema)
        assert any("level" in v for v in violations)

    def test_wrong_type_reported(self):
        entry = {"message": 42, "level": "INFO"}
        violations = validate_entry(entry, self._schema)
        assert any("message" in v for v in violations)

    def test_strict_rejects_extra_fields(self):
        entry = {"message": "hi", "level": "DEBUG", "unknown_field": True}
        violations = validate_entry(entry, self._schema, strict=True)
        assert any("unknown_field" in v for v in violations)

    def test_non_strict_allows_extra_fields(self):
        entry = {"message": "hi", "level": "DEBUG", "extra": 1}
        assert validate_entry(entry, self._schema, strict=False) == []

    def test_multiple_violations_all_returned(self):
        entry = {}
        violations = validate_entry(entry, self._schema)
        assert len(violations) == 2


# ---------------------------------------------------------------------------
# filter_valid
# ---------------------------------------------------------------------------

class TestFilterValid:
    _schema = {"message": str, "level": str}

    def test_removes_invalid_entries(self):
        entries = [
            {"message": "ok", "level": "INFO"},
            {"message": "bad"},
            {"level": "WARN"},
        ]
        result = filter_valid(entries, self._schema)
        assert len(result) == 1
        assert result[0]["message"] == "ok"

    def test_empty_input_returns_empty(self):
        assert filter_valid([], self._schema) == []

    def test_all_valid_returns_all(self):
        entries = [{"message": str(i), "level": "INFO"} for i in range(5)]
        assert filter_valid(entries, self._schema) == entries


# ---------------------------------------------------------------------------
# available_schemas
# ---------------------------------------------------------------------------

def test_available_schemas_contains_builtins():
    names = available_schemas()
    assert "basic" in names
    assert "full" in names
