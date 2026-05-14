"""Tests for logslice.enrich."""

from __future__ import annotations

import socket
from typing import Any, Dict

import pytest

from logslice.enrich import (
    apply_enrichers,
    enrich_with_derived,
    enrich_with_hostname,
    enrich_with_regex,
    enrich_with_static,
)


def _e(**kw: Any) -> Dict[str, Any]:
    return dict(kw)


# ---------------------------------------------------------------------------
# enrich_with_hostname
# ---------------------------------------------------------------------------

class TestEnrichWithHostname:
    def test_adds_host_key(self):
        result = enrich_with_hostname(_e(message="hi"))
        assert "host" in result

    def test_host_value_matches_socket(self):
        result = enrich_with_hostname(_e(message="hi"))
        assert result["host"] == socket.gethostname()

    def test_does_not_overwrite_existing_host(self):
        entry = _e(host="custom-host", message="hi")
        result = enrich_with_hostname(entry)
        assert result["host"] == "custom-host"

    def test_original_entry_not_mutated(self):
        entry = _e(message="hi")
        enrich_with_hostname(entry)
        assert "host" not in entry


# ---------------------------------------------------------------------------
# enrich_with_static
# ---------------------------------------------------------------------------

class TestEnrichWithStatic:
    def test_adds_static_fields(self):
        fn = enrich_with_static({"env": "prod", "region": "us-east-1"})
        result = fn(_e(message="hello"))
        assert result["env"] == "prod"
        assert result["region"] == "us-east-1"

    def test_entry_values_win_over_static(self):
        fn = enrich_with_static({"env": "prod"})
        result = fn(_e(env="staging", message="hello"))
        assert result["env"] == "staging"

    def test_original_not_mutated(self):
        fn = enrich_with_static({"x": "1"})
        entry = _e(message="hi")
        fn(entry)
        assert "x" not in entry


# ---------------------------------------------------------------------------
# enrich_with_derived
# ---------------------------------------------------------------------------

class TestEnrichWithDerived:
    def test_derives_field(self):
        fn = enrich_with_derived("message", "msg_len", len)
        result = fn(_e(message="hello"))
        assert result["msg_len"] == 5

    def test_missing_source_leaves_entry_unchanged(self):
        fn = enrich_with_derived("missing", "dest", str.upper)
        entry = _e(message="hi")
        result = fn(entry)
        assert "dest" not in result

    def test_transform_applied(self):
        fn = enrich_with_derived("level", "level_upper", str.upper)
        result = fn(_e(level="info"))
        assert result["level_upper"] == "INFO"


# ---------------------------------------------------------------------------
# enrich_with_regex
# ---------------------------------------------------------------------------

class TestEnrichWithRegex:
    def test_named_groups_extracted(self):
        fn = enrich_with_regex("message", r"user=(?P<user>\w+)")
        result = fn(_e(message="login user=alice ok"))
        assert result["user"] == "alice"

    def test_no_match_leaves_entry_unchanged(self):
        fn = enrich_with_regex("message", r"user=(?P<user>\w+)")
        entry = _e(message="no match here")
        result = fn(entry)
        assert "user" not in result

    def test_positional_groups_with_dest_fields(self):
        fn = enrich_with_regex("message", r"(\d+)\.(\d+)", dest_fields=["major", "minor"])
        result = fn(_e(message="version 3.14"))
        assert result["major"] == "3"
        assert result["minor"] == "14"


# ---------------------------------------------------------------------------
# apply_enrichers
# ---------------------------------------------------------------------------

class TestApplyEnrichers:
    def test_empty_enrichers_returns_all(self):
        entries = [_e(message="a"), _e(message="b")]
        assert apply_enrichers(entries, []) == entries

    def test_enrichers_applied_in_order(self):
        fn1 = enrich_with_static({"step": "first"})
        fn2 = enrich_with_derived("step", "step_upper", str.upper)
        results = apply_enrichers([_e(message="hi")], [fn1, fn2])
        assert results[0]["step_upper"] == "FIRST"

    def test_all_entries_enriched(self):
        entries = [_e(message="x"), _e(message="y"), _e(message="z")]
        fn = enrich_with_static({"tag": "test"})
        results = apply_enrichers(entries, [fn])
        assert all(r["tag"] == "test" for r in results)
