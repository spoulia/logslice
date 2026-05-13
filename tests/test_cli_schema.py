"""Tests for logslice.cli_schema."""

from __future__ import annotations

import argparse
import json
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

import pytest

from logslice.cli_schema import add_schema_subparser, run_schema


def _make_args(**kwargs) -> SimpleNamespace:
    defaults = {
        "input": "-",
        "schema": "basic",
        "strict": False,
        "report": False,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


# ---------------------------------------------------------------------------
# Subparser registration
# ---------------------------------------------------------------------------

class TestAddSchemaSubparser:
    def test_subparser_registered(self):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        add_schema_subparser(sub)
        args = parser.parse_args(["schema"])
        assert hasattr(args, "func")

    def test_strict_flag_default_false(self):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        add_schema_subparser(sub)
        args = parser.parse_args(["schema"])
        assert args.strict is False

    def test_report_flag_default_false(self):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        add_schema_subparser(sub)
        args = parser.parse_args(["schema"])
        assert args.report is False

    def test_schema_default_is_basic(self):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        add_schema_subparser(sub)
        args = parser.parse_args(["schema"])
        assert args.schema == "basic"


# ---------------------------------------------------------------------------
# run_schema
# ---------------------------------------------------------------------------

class TestRunSchema:
    _valid_line = json.dumps({"message": "hello", "level": "INFO"})
    _invalid_line = json.dumps({"message": "no level"})

    def _run(self, lines, **kwargs):
        args = _make_args(**kwargs)
        with patch("logslice.cli_schema._read_entries", return_value=[json.loads(l) for l in lines]):
            return run_schema(args)

    def test_valid_entries_exit_zero(self, capsys):
        rc = self._run([self._valid_line])
        assert rc == 0

    def test_valid_entries_printed(self, capsys):
        rc = self._run([self._valid_line])
        out = capsys.readouterr().out
        data = json.loads(out.strip())
        assert data["message"] == "hello"

    def test_invalid_entry_filtered_silently(self, capsys):
        rc = self._run([self._invalid_line])
        assert rc == 0
        out = capsys.readouterr().out
        assert out.strip() == ""

    def test_report_mode_prints_violations(self, capsys):
        rc = self._run([self._invalid_line], report=True)
        assert rc == 1
        out = capsys.readouterr().out
        assert "level" in out

    def test_report_mode_no_violations_exits_zero(self, capsys):
        rc = self._run([self._valid_line], report=True)
        assert rc == 0

    def test_unknown_preset_exits_one(self, capsys):
        args = _make_args(schema="ghost_schema")
        with patch("logslice.cli_schema._read_entries", return_value=[]):
            rc = run_schema(args)
        assert rc == 1
