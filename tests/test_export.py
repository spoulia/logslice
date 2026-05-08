"""Tests for logslice.export."""

from __future__ import annotations

import csv
import io
import json

import pytest

from logslice.export import (
    export_entries,
    export_to_csv,
    export_to_json,
    export_to_ndjson,
)


def _entries():
    return [
        {"timestamp": "2024-01-01T00:00:00", "level": "INFO", "message": "started"},
        {"timestamp": "2024-01-01T00:00:01", "level": "ERROR", "message": "oops"},
    ]


class TestExportToJson:
    def test_returns_valid_json(self):
        result = export_to_json(_entries())
        parsed = json.loads(result)
        assert isinstance(parsed, list)
        assert len(parsed) == 2

    def test_preserves_fields(self):
        result = json.loads(export_to_json(_entries()))
        assert result[0]["level"] == "INFO"
        assert result[1]["message"] == "oops"

    def test_custom_indent(self):
        result = export_to_json(_entries(), indent=0)
        assert "\n" not in result.strip()

    def test_empty_list(self):
        assert export_to_json([]) == "[]"


class TestExportToCsv:
    def test_returns_header_row(self):
        result = export_to_csv(_entries())
        reader = csv.DictReader(io.StringIO(result))
        rows = list(reader)
        assert len(rows) == 2

    def test_field_subset(self):
        result = export_to_csv(_entries(), fields=["level", "message"])
        reader = csv.DictReader(io.StringIO(result))
        assert reader.fieldnames == ["level", "message"]

    def test_empty_entries_returns_empty_string(self):
        assert export_to_csv([]) == ""

    def test_missing_field_is_empty(self):
        entries = [{"level": "INFO"}]
        result = export_to_csv(entries, fields=["level", "message"])
        reader = csv.DictReader(io.StringIO(result))
        row = next(reader)
        assert row["message"] == ""


class TestExportToNdjson:
    def test_one_line_per_entry(self):
        result = export_to_ndjson(_entries())
        lines = [l for l in result.splitlines() if l.strip()]
        assert len(lines) == 2

    def test_each_line_is_valid_json(self):
        for line in export_to_ndjson(_entries()).splitlines():
            json.loads(line)

    def test_empty_input(self):
        assert export_to_ndjson([]) == ""


class TestExportEntries:
    def test_dispatch_json(self):
        result = export_entries(_entries(), "json")
        assert json.loads(result)

    def test_dispatch_csv(self):
        result = export_entries(_entries(), "csv")
        assert "level" in result

    def test_dispatch_ndjson(self):
        result = export_entries(_entries(), "ndjson")
        assert result.count("\n") == 2

    def test_unknown_format_raises(self):
        with pytest.raises(ValueError, match="Unsupported"):
            export_entries(_entries(), "xml")

    def test_case_insensitive_format(self):
        result = export_entries(_entries(), "JSON")
        assert json.loads(result)
