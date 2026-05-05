"""Integration tests for the highlight CLI subcommand."""

import argparse
import sys
import io
import pytest
from unittest.mock import patch, MagicMock

from logslice.cli_highlight import add_highlight_subparser, run_highlight


def _make_args(**kwargs):
    defaults = {"file": None, "pattern": None, "no_color": True}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestAddHighlightSubparser:
    def test_subparser_registered(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        add_highlight_subparser(subparsers)
        args = parser.parse_args(["highlight"])
        assert hasattr(args, "func")

    def test_pattern_argument(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        add_highlight_subparser(subparsers)
        args = parser.parse_args(["highlight", "--pattern", "error"])
        assert args.pattern == "error"

    def test_no_color_flag(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        add_highlight_subparser(subparsers)
        args = parser.parse_args(["highlight", "--no-color"])
        assert args.no_color is True


class TestRunHighlight:
    def test_reads_from_stdin(self, capsys):
        fake_stdin = io.StringIO("2024-01-01 INFO hello world\n")
        args = _make_args()
        with patch("sys.stdin", fake_stdin):
            run_highlight(args)
        captured = capsys.readouterr()
        assert "hello world" in captured.out

    def test_reads_from_file(self, tmp_path, capsys):
        log_file = tmp_path / "app.log"
        log_file.write_text("2024-01-01 ERROR something failed\n")
        args = _make_args(file=str(log_file))
        run_highlight(args)
        captured = capsys.readouterr()
        assert "something failed" in captured.out

    def test_missing_file_exits(self, capsys):
        args = _make_args(file="/nonexistent/path/file.log")
        with pytest.raises(SystemExit) as exc_info:
            run_highlight(args)
        assert exc_info.value.code == 1

    def test_multiple_lines(self, capsys):
        lines = "line one\nline two\nline three\n"
        fake_stdin = io.StringIO(lines)
        args = _make_args()
        with patch("sys.stdin", fake_stdin):
            run_highlight(args)
        captured = capsys.readouterr()
        assert "line one" in captured.out
        assert "line three" in captured.out
