"""Tests for logslice.cli_index."""

from __future__ import annotations

import argparse
import io
import json

import pytest

from logslice.cli_index import add_index_subparser, run_index, _parse_query


def _make_args(**kw) -> argparse.Namespace:
    defaults = {
        "fields": None,
        "queries": [],
        "list_values": None,
        "stats": False,
    }
    defaults.update(kw)
    return argparse.Namespace(**defaults)


def _stream(*entries):
    lines = [json.dumps(e) for e in entries]
    return io.StringIO("\n".join(lines))


# ---------------------------------------------------------------------------
class TestAddIndexSubparser:
    def test_subparser_registered(self):
        p = argparse.ArgumentParser()
        sub = p.add_subparsers()
        add_index_subparser(sub)
        ns = p.parse_args(["index"])
        assert ns is not None

    def test_field_argument(self):
        p = argparse.ArgumentParser()
        sub = p.add_subparsers()
        add_index_subparser(sub)
        ns = p.parse_args(["index", "--field", "level", "--field", "source"])
        assert ns.fields == ["level", "source"]

    def test_query_argument(self):
        p = argparse.ArgumentParser()
        sub = p.add_subparsers()
        add_index_subparser(sub)
        ns = p.parse_args(["index", "--query", "level=error"])
        assert ns.queries == ["level=error"]

    def test_stats_flag_default_false(self):
        p = argparse.ArgumentParser()
        sub = p.add_subparsers()
        add_index_subparser(sub)
        ns = p.parse_args(["index"])
        assert ns.stats is False


# ---------------------------------------------------------------------------
class TestRunIndex:
    def test_no_query_prints_all(self, capsys):
        entries = [{"level": "info", "message": "a"}, {"level": "error", "message": "b"}]
        run_index(_make_args(), _stream(*entries))
        out = capsys.readouterr().out
        lines = [l for l in out.strip().splitlines() if l]
        assert len(lines) == 2

    def test_query_filters_entries(self, capsys):
        entries = [
            {"level": "info", "source": "app", "message": "ok"},
            {"level": "error", "source": "app", "message": "fail"},
        ]
        run_index(_make_args(queries=["level=error"]), _stream(*entries))
        out = capsys.readouterr().out
        parsed = [json.loads(l) for l in out.strip().splitlines() if l]
        assert len(parsed) == 1
        assert parsed[0]["level"] == "error"

    def test_list_values(self, capsys):
        entries = [
            {"level": "info", "source": "app"},
            {"level": "error", "source": "app"},
        ]
        run_index(_make_args(list_values="level"), _stream(*entries))
        out = capsys.readouterr().out
        vals = set(out.strip().splitlines())
        assert vals == {"info", "error"}

    def test_stats_output(self, capsys):
        entries = [{"level": "info", "source": "app"}] * 3
        run_index(_make_args(stats=True), _stream(*entries))
        out = capsys.readouterr().out
        assert "total entries" in out
        assert "3" in out

    def test_plain_line_becomes_message(self, capsys):
        stream = io.StringIO("not json\n")
        run_index(_make_args(), stream)
        out = capsys.readouterr().out
        parsed = json.loads(out.strip())
        assert parsed["message"] == "not json"


# ---------------------------------------------------------------------------
class TestParseQuery:
    def test_simple(self):
        assert _parse_query("level=error") == ("level", "error")

    def test_value_with_equals(self):
        assert _parse_query("msg=a=b") == ("msg", "a=b")

    def test_missing_equals_raises(self):
        with pytest.raises(Exception):
            _parse_query("noequalssign")
