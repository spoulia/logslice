"""Tests for logslice.summary module."""

import io
import json
import os
import tempfile

import pytest
from logslice.summary import print_summary, summary_from_file


SAMPLE_ENTRIES = [
    {"timestamp": "2024-03-01T08:00:00", "level": "INFO", "source": "svc", "message": "ok"},
    {"timestamp": "2024-03-01T08:01:00", "level": "ERROR", "source": "svc", "message": "fail"},
]


class TestPrintSummary:
    def test_text_output_contains_total(self):
        buf = io.StringIO()
        print_summary(SAMPLE_ENTRIES, output_format="text", out=buf)
        assert "2" in buf.getvalue()

    def test_json_output_is_valid_json(self):
        buf = io.StringIO()
        print_summary(SAMPLE_ENTRIES, output_format="json", out=buf)
        data = json.loads(buf.getvalue())
        assert data["total"] == 2

    def test_json_output_has_error_rate(self):
        buf = io.StringIO()
        print_summary(SAMPLE_ENTRIES, output_format="json", out=buf)
        data = json.loads(buf.getvalue())
        assert "error_rate" in data

    def test_empty_entries_text(self):
        buf = io.StringIO()
        print_summary([], output_format="text", out=buf)
        assert "0" in buf.getvalue()

    def test_empty_entries_json(self):
        buf = io.StringIO()
        print_summary([], output_format="json", out=buf)
        data = json.loads(buf.getvalue())
        assert data["total"] == 0


class TestSummaryFromFile:
    def _write_jsonl(self, entries):
        tf = tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
        )
        for entry in entries:
            tf.write(json.dumps(entry) + "\n")
        tf.close()
        return tf.name

    def test_reads_file_and_prints(self):
        path = self._write_jsonl(SAMPLE_ENTRIES)
        try:
            buf = io.StringIO()
            summary_from_file(path, output_format="text", out=buf)
            assert "2" in buf.getvalue()
        finally:
            os.unlink(path)

    def test_skips_blank_lines(self):
        tf = tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
        )
        tf.write(json.dumps(SAMPLE_ENTRIES[0]) + "\n")
        tf.write("\n")
        tf.write(json.dumps(SAMPLE_ENTRIES[1]) + "\n")
        tf.close()
        try:
            buf = io.StringIO()
            summary_from_file(tf.name, output_format="json", out=buf)
            data = json.loads(buf.getvalue())
            assert data["total"] == 2
        finally:
            os.unlink(tf.name)

    def test_skips_invalid_json_lines(self):
        tf = tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
        )
        tf.write("not valid json\n")
        tf.write(json.dumps(SAMPLE_ENTRIES[0]) + "\n")
        tf.close()
        try:
            buf = io.StringIO()
            summary_from_file(tf.name, output_format="json", out=buf)
            data = json.loads(buf.getvalue())
            assert data["total"] == 1
        finally:
            os.unlink(tf.name)
