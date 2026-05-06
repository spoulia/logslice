"""Tests for logslice.transform module."""

import pytest
from logslice.transform import (
    get_transformer,
    transform_field,
    transform_fields,
    transform_entries,
    rename_field,
    drop_fields,
)


def _entry(**kwargs):
    base = {"message": "test log", "level": "info", "source": "app"}
    base.update(kwargs)
    return base


class TestGetTransformer:
    def test_upper_exists(self):
        assert get_transformer("upper") is not None

    def test_lower_exists(self):
        assert get_transformer("lower") is not None

    def test_unknown_returns_none(self):
        assert get_transformer("nonexistent") is None

    def test_upper_works(self):
        fn = get_transformer("upper")
        assert fn("hello") == "HELLO"

    def test_lower_works(self):
        fn = get_transformer("lower")
        assert fn("WARN") == "warn"

    def test_strip_works(self):
        fn = get_transformer("strip")
        assert fn("  spaces  ") == "spaces"

    def test_int_works(self):
        fn = get_transformer("int")
        assert fn("42") == 42

    def test_bool_true(self):
        fn = get_transformer("bool")
        assert fn("true") is True

    def test_bool_false(self):
        fn = get_transformer("bool")
        assert fn("false") is False


class TestTransformField:
    def test_transforms_existing_field(self):
        entry = _entry(level="INFO")
        result = transform_field(entry, "level", "lower")
        assert result["level"] == "info"

    def test_missing_field_leaves_entry_unchanged(self):
        entry = _entry()
        result = transform_field(entry, "nonexistent", "upper")
        assert result == entry

    def test_unknown_transformer_raises(self):
        entry = _entry()
        with pytest.raises(ValueError, match="Unknown transformer"):
            transform_field(entry, "message", "bogus")

    def test_does_not_mutate_original(self):
        entry = _entry(message="hello")
        transform_field(entry, "message", "upper")
        assert entry["message"] == "hello"

    def test_bad_conversion_leaves_original(self):
        entry = _entry(message="not-a-number")
        result = transform_field(entry, "message", "int")
        assert result["message"] == "not-a-number"


class TestTransformFields:
    def test_applies_multiple_rules(self):
        entry = _entry(level="INFO", message="  hello  ")
        rules = [
            {"field": "level", "transform": "lower"},
            {"field": "message", "transform": "strip"},
        ]
        result = transform_fields(entry, rules)
        assert result["level"] == "info"
        assert result["message"] == "hello"

    def test_empty_rules_returns_copy(self):
        entry = _entry()
        result = transform_fields(entry, [])
        assert result == entry
        assert result is not entry


class TestTransformEntries:
    def test_transforms_all_entries(self):
        entries = [_entry(level="ERROR"), _entry(level="WARN")]
        rules = [{"field": "level", "transform": "lower"}]
        results = transform_entries(entries, rules)
        assert results[0]["level"] == "error"
        assert results[1]["level"] == "warn"

    def test_empty_list(self):
        assert transform_entries([], [{"field": "level", "transform": "lower"}]) == []


class TestRenameField:
    def test_renames_existing_field(self):
        entry = _entry(source="myapp")
        result = rename_field(entry, "source", "service")
        assert "service" in result
        assert "source" not in result
        assert result["service"] == "myapp"

    def test_missing_field_unchanged(self):
        entry = _entry()
        result = rename_field(entry, "missing", "new_name")
        assert result == entry


class TestDropFields:
    def test_drops_specified_fields(self):
        entry = _entry()
        result = drop_fields(entry, ["source", "level"])
        assert "source" not in result
        assert "level" not in result
        assert "message" in result

    def test_no_fields_to_drop(self):
        entry = _entry()
        result = drop_fields(entry, [])
        assert result == entry
