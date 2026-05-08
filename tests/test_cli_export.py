"""Tests for logslice.cli_export."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from logslice.cli_export import add_export_subparser, run_export


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "input": None,
        "output": "",
        "format": "json",
        "fields": None,
        "indent": 2,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestAddExportSubparser:
    def test_subparser_registered(self):
        root = argparse.ArgumentParser()
        sub = root.add_subparsers()
        add_export_subparser(sub)
        args = root.parse_args(["export", "-o", "out.json"])
        assert args.format == "json"

    def test_format_choices(self):
        root = argparse.ArgumentParser()
        sub = root.add_subparsers()
        add_export_subparser(sub)
        args = root.parse_args(["export", "-o", "out.csv", "-f", "csv"])
        assert args.format == "csv"

    def test_invalid_format_exits(self):
        root = argparse.ArgumentParser()
        sub = root.add_subparsers()
        add_export_subparser(sub)
        with pytest.raises(SystemExit):
            root.parse_args(["export", "-o", "out.xml", "-f", "xml"])


class TestRunExport:
    def test_json_file_created(self, tmp_path):
        log_file = tmp_path / "app.log"
        log_file.write_text(
            '{"timestamp": "2024-01-01T00:00:00", "level": "INFO", "message": "hi"}\n',
            encoding="utf-8",
        )
        out_file = tmp_path / "out.json"
        args = _make_args(input=str(log_file), output=str(out_file), format="json")
        run_export(args)
        assert out_file.exists()
        data = json.loads(out_file.read_text())
        assert isinstance(data, list)

    def test_csv_file_created(self, tmp_path):
        log_file = tmp_path / "app.log"
        log_file.write_text(
            '{"timestamp": "2024-01-01T00:00:00", "level": "ERROR", "message": "bad"}\n',
            encoding="utf-8",
        )
        out_file = tmp_path / "out.csv"
        args = _make_args(
            input=str(log_file), output=str(out_file), format="csv", fields=["level", "message"]
        )
        run_export(args)
        assert out_file.exists()
        assert "level" in out_file.read_text()

    def test_output_directory_created(self, tmp_path):
        log_file = tmp_path / "app.log"
        log_file.write_text(
            '{"timestamp": "2024-01-01T00:00:00", "level": "INFO", "message": "x"}\n'
        )
        out_file = tmp_path / "nested" / "dir" / "out.json"
        args = _make_args(input=str(log_file), output=str(out_file))
        run_export(args)
        assert out_file.exists()
