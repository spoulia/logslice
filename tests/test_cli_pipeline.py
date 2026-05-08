"""Tests for logslice.cli_pipeline."""

from __future__ import annotations

import argparse
import json
from io import StringIO
from unittest.mock import patch

import pytest

from logslice.cli_pipeline import add_pipeline_subparser, run_pipeline


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "file": None,
        "level": None,
        "pattern": None,
        "redact": False,
        "output": "json",
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


_SAMPLE_LINES = [
    '{"timestamp": "2024-01-01T10:00:00", "level": "INFO", "message": "started"}\n',
    '{"timestamp": "2024-01-01T10:01:00", "level": "ERROR", "message": "boom"}\n',
]


class TestAddPipelineSubparser:
    def test_subparser_registered(self):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers(dest="cmd")
        add_pipeline_subparser(sub)
        ns = parser.parse_args(["pipeline"])
        assert ns.cmd == "pipeline"

    def test_level_argument(self):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers(dest="cmd")
        add_pipeline_subparser(sub)
        ns = parser.parse_args(["pipeline", "--level", "ERROR"])
        assert ns.level == "ERROR"

    def test_redact_flag(self):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers(dest="cmd")
        add_pipeline_subparser(sub)
        ns = parser.parse_args(["pipeline", "--redact"])
        assert ns.redact is True

    def test_output_choices(self):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers(dest="cmd")
        add_pipeline_subparser(sub)
        with pytest.raises(SystemExit):
            parser.parse_args(["pipeline", "--output", "xml"])


class TestRunPipeline:
    def _run(self, args, lines=None):
        lines = lines or _SAMPLE_LINES
        with patch("logslice.cli_pipeline._read_entries", return_value=[
            json.loads(l) for l in lines
        ]):
            import io, sys
            captured = io.StringIO()
            with patch("sys.stdout", captured):
                run_pipeline(args)
            return captured.getvalue()

    def test_json_output_is_valid(self):
        out = self._run(_make_args())
        data = json.loads(out)
        assert isinstance(data, list)

    def test_level_filter_applied(self):
        out = self._run(_make_args(level="ERROR"))
        data = json.loads(out)
        assert all(e["level"] == "ERROR" for e in data)

    def test_text_output_contains_message(self):
        out = self._run(_make_args(output="text"))
        assert "started" in out
        assert "boom" in out

    def test_empty_entries_returns_empty_list(self):
        with patch("logslice.cli_pipeline._read_entries", return_value=[]):
            import io, sys
            captured = io.StringIO()
            with patch("sys.stdout", captured):
                run_pipeline(_make_args())
            assert json.loads(captured.getvalue()) == []
