"""Tests for logslice.cli_enrich."""

from __future__ import annotations

import argparse
import json
import socket
from io import StringIO
from unittest.mock import patch

import pytest

from logslice.cli_enrich import add_enrich_subparser, run_enrich


def _make_args(**kw):
    defaults = {
        "file": None,
        "hostname": False,
        "static": [],
        "regex": [],
    }
    defaults.update(kw)
    return argparse.Namespace(**defaults)


def _entries_as_stdin(entries):
    text = "\n".join(json.dumps(e) for e in entries)
    return patch("sys.stdin", StringIO(text))


class TestAddEnrichSubparser:
    def test_subparser_registered(self):
        p = argparse.ArgumentParser()
        sub = p.add_subparsers()
        add_enrich_subparser(sub)
        ns = p.parse_args(["enrich"])
        assert ns is not None

    def test_hostname_flag_default_false(self):
        p = argparse.ArgumentParser()
        sub = p.add_subparsers()
        add_enrich_subparser(sub)
        ns = p.parse_args(["enrich"])
        assert ns.hostname is False

    def test_static_default_empty(self):
        p = argparse.ArgumentParser()
        sub = p.add_subparsers()
        add_enrich_subparser(sub)
        ns = p.parse_args(["enrich"])
        assert ns.static == []


class TestRunEnrich:
    def test_hostname_injected(self, capsys):
        entries = [{"message": "hello"}]
        with _entries_as_stdin(entries):
            run_enrich(_make_args(hostname=True))
        out = capsys.readouterr().out
        result = json.loads(out.strip())
        assert result["host"] == socket.gethostname()

    def test_static_field_added(self, capsys):
        entries = [{"message": "hi"}]
        with _entries_as_stdin(entries):
            run_enrich(_make_args(static=["env=prod"]))
        out = capsys.readouterr().out
        result = json.loads(out.strip())
        assert result["env"] == "prod"

    def test_invalid_static_exits(self):
        entries = [{"message": "hi"}]
        with _entries_as_stdin(entries):
            with pytest.raises(SystemExit):
                run_enrich(_make_args(static=["badvalue"]))

    def test_regex_extracts_named_group(self, capsys):
        entries = [{"message": "user=bob logged in"}]
        with _entries_as_stdin(entries):
            run_enrich(_make_args(regex=[r"message:user=(?P<user>\w+)"]))
        out = capsys.readouterr().out
        result = json.loads(out.strip())
        assert result["user"] == "bob"

    def test_invalid_regex_spec_exits(self):
        entries = [{"message": "hi"}]
        with _entries_as_stdin(entries):
            with pytest.raises(SystemExit):
                run_enrich(_make_args(regex=["no-colon-here"]))

    def test_multiple_entries_all_enriched(self, capsys):
        entries = [{"message": "a"}, {"message": "b"}]
        with _entries_as_stdin(entries):
            run_enrich(_make_args(static=["src=test"]))
        lines = capsys.readouterr().out.strip().splitlines()
        assert len(lines) == 2
        assert all(json.loads(l)["src"] == "test" for l in lines)
