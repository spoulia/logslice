"""Tests for logslice.mask."""

from __future__ import annotations

import pytest

from logslice.mask import mask_value, mask_field, mask_fields, mask_entries


# ---------------------------------------------------------------------------
# mask_value
# ---------------------------------------------------------------------------

class TestMaskValue:
    def test_full_mask_by_default(self):
        assert mask_value("secret") == "******"

    def test_keep_start(self):
        assert mask_value("hello", keep_start=2) == "he***"

    def test_keep_end(self):
        assert mask_value("hello", keep_end=2) == "***lo"

    def test_keep_start_and_end(self):
        assert mask_value("hello", keep_start=1, keep_end=1) == "h***o"

    def test_custom_char(self):
        assert mask_value("abc", char="-") == "---"

    def test_keep_exceeds_length_returns_original(self):
        assert mask_value("hi", keep_start=5) == "hi"

    def test_non_string_coerced(self):
        result = mask_value(12345)  # type: ignore[arg-type]
        assert result == "*****"

    def test_empty_string(self):
        assert mask_value("") == ""


# ---------------------------------------------------------------------------
# mask_field
# ---------------------------------------------------------------------------

class TestMaskField:
    def _entry(self, **kwargs):
        base = {"message": "hello", "level": "INFO"}
        base.update(kwargs)
        return base

    def test_masks_existing_field(self):
        entry = self._entry(token="abc123")
        result = mask_field(entry, "token")
        assert result["token"] == "******"

    def test_missing_field_unchanged(self):
        entry = self._entry()
        result = mask_field(entry, "token")
        assert "token" not in result

    def test_other_fields_preserved(self):
        entry = self._entry(token="abc")
        result = mask_field(entry, "token")
        assert result["message"] == "hello"
        assert result["level"] == "INFO"

    def test_does_not_mutate_original(self):
        entry = {"token": "abc"}
        mask_field(entry, "token")
        assert entry["token"] == "abc"


# ---------------------------------------------------------------------------
# mask_fields
# ---------------------------------------------------------------------------

class TestMaskFields:
    def test_masks_multiple_fields(self):
        entry = {"user": "alice", "password": "s3cr3t", "level": "DEBUG"}
        result = mask_fields(entry, ["user", "password"])
        assert result["user"] == "*****"
        assert result["password"] == "******"
        assert result["level"] == "DEBUG"

    def test_skips_missing_fields(self):
        entry = {"level": "INFO"}
        result = mask_fields(entry, ["token", "password"])
        assert result == {"level": "INFO"}

    def test_keep_start_applied_to_all(self):
        entry = {"a": "hello", "b": "world"}
        result = mask_fields(entry, ["a", "b"], keep_start=2)
        assert result["a"] == "he***"
        assert result["b"] == "wo***"


# ---------------------------------------------------------------------------
# mask_entries
# ---------------------------------------------------------------------------

class TestMaskEntries:
    def _entries(self):
        return [
            {"message": "login", "token": "abc", "level": "INFO"},
            {"message": "logout", "token": "xyz", "level": "INFO"},
        ]

    def test_masks_field_in_all_entries(self):
        results = mask_entries(self._entries(), ["token"])
        assert all(e["token"] == "***" for e in results)

    def test_returns_list(self):
        assert isinstance(mask_entries(self._entries(), ["token"]), list)

    def test_empty_entries(self):
        assert mask_entries([], ["token"]) == []

    def test_originals_not_mutated(self):
        entries = self._entries()
        mask_entries(entries, ["token"])
        assert entries[0]["token"] == "abc"
