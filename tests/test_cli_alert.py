"""Tests for logslice.cli_alert."""

from __future__ import annotations

import argparse
import json

import pytest

from logslice.cli_alert import add_alert_subparser, run_alert


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "input": "-",
        "condition": "error",
        "output": None,
        "count": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestAddAlertSubparser:
    def test_subparser_registered(self):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers(dest="cmd")
        add_alert_subparser(sub)
        ns = parser.parse_args(["alert"])
        assert ns.cmd == "alert"

    def test_condition_default(self):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers(dest="cmd")
        add_alert_subparser(sub)
        ns = parser.parse_args(["alert"])
        assert ns.condition == "error"

    def test_count_flag(self):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers(dest="cmd")
        add_alert_subparser(sub)
        ns = parser.parse_args(["alert", "--count"])
        assert ns.count is True


class TestRunAlert:
    def test_missing_file_returns_1(self):
        args = _make_args(input="/nonexistent/path/log.txt")
        assert run_alert(args) == 1

    def test_reads_from_file_and_counts(self, tmp_path):
        log = tmp_path / "app.log"
        log.write_text(
            '{"level": "error", "message": "boom"}\n'
            '{"level": "info", "message": "ok"}\n'
            '{"level": "error", "message": "crash"}\n'
        )
        args = _make_args(input=str(log), count=True)
        captured = []
        import builtins
        original_print = builtins.print

        def _capture(*a, **kw):
            captured.append(a)

        builtins.print = _capture
        try:
            rc = run_alert(args)
        finally:
            builtins.print = original_print

        assert rc == 0
        assert captured[-1] == (2,)

    def test_output_written_to_file(self, tmp_path):
        log = tmp_path / "app.log"
        log.write_text('{"level": "error", "message": "disk full"}\n')
        out = tmp_path / "alerts.jsonl"
        args = _make_args(input=str(log), output=str(out))
        rc = run_alert(args)
        assert rc == 0
        lines = out.read_text().splitlines()
        assert len(lines) == 1
        assert json.loads(lines[0])["message"] == "disk full"
