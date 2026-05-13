"""Tests for logslice.formatters and logslice.output."""

import io
import json
from datetime import datetime

import pytest

from logslice.formatters import format_csv, format_json, format_plain, get_formatter
from logslice.output import write_entries


SAMPLE_ENTRY = {
    "timestamp": datetime(2024, 1, 15, 12, 0, 0),
    "level": "error",
    "message": "Something went wrong",
    "fields": {"code": 500},
}

MINIMAL_ENTRY = {"raw": "bare log line"}


class TestFormatPlain:
    def test_full_entry(self):
        result = format_plain(SAMPLE_ENTRY)
        assert "2024-01-15" in result
        assert "[ERROR]" in result
        assert "Something went wrong" in result

    def test_minimal_entry(self):
        result = format_plain(MINIMAL_ENTRY)
        assert result == "bare log line"

    def test_empty_entry(self):
        result = format_plain({})
        assert result == ""


class TestFormatJson:
    def test_full_entry(self):
        result = format_json(SAMPLE_ENTRY)
        data = json.loads(result)
        assert data["level"] == "error"
        assert data["message"] == "Something went wrong"
        assert data["fields"] == {"code": 500}

    def test_minimal_entry(self):
        result = format_json(MINIMAL_ENTRY)
        data = json.loads(result)
        assert data["message"] == "bare log line"


class TestFormatCsv:
    def test_full_entry(self):
        result = format_csv(SAMPLE_ENTRY)
        parts = result.split(",")
        assert len(parts) == 3
        assert "error" in parts[1]

    def test_message_with_comma(self):
        entry = {"timestamp": None, "level": "info", "message": "a,b,c"}
        result = format_csv(entry)
        assert '"a,b,c"' in result


class TestGetFormatter:
    def test_valid_formats(self):
        for fmt in ("plain", "json", "csv"):
            assert callable(get_formatter(fmt))

    def test_invalid_format(self):
        with pytest.raises(ValueError, match="Unknown format"):
            get_formatter("xml")


class TestWriteEntries:
    def test_plain_output(self):
        buf = io.StringIO()
        count = write_entries([SAMPLE_ENTRY], fmt="plain", dest=buf)
        assert count == 1
        assert "Something went wrong" in buf.getvalue()

    def test_json_output(self):
        buf = io.StringIO()
        write_entries([SAMPLE_ENTRY], fmt="json", dest=buf)
        data = json.loads(buf.getvalue().strip())
        assert data["level"] == "error"

    def test_csv_header(self):
        buf = io.StringIO()
        write_entries([SAMPLE_ENTRY], fmt="csv", dest=buf, csv_header=True)
        lines = buf.getvalue().splitlines()
        assert lines[0] == "timestamp,level,message"
        assert len(lines) == 2

    def test_csv_no_header(self):
        buf = io.StringIO()
        write_entries([SAMPLE_ENTRY], fmt="csv", dest=buf, csv_header=False)
        lines = buf.getvalue().splitlines()
        assert len(lines) == 1

    def test_empty_entries(self):
        buf = io.StringIO()
        count = write_entries([], fmt="plain", dest=buf)
        assert count == 0
        assert buf.getvalue() == ""

    def test_multiple_entries(self):
        entries = [SAMPLE_ENTRY, MINIMAL_ENTRY]
        buf = io.StringIO()
        count = write_entries(entries, fmt="plain", dest=buf)
        assert count == 2
        output = buf.getvalue()
        assert "Something went wrong" in output
        assert "bare log line" in output
