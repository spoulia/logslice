"""Tests for logslice.pipeline."""

from __future__ import annotations

from typing import Iterable, Iterator

import pytest

from logslice.pipeline import (
    Pipeline,
    build_pipeline,
    make_filter_step,
    make_transform_step,
)


def _entry(msg: str = "hello", level: str = "INFO") -> dict:
    return {"message": msg, "level": level, "timestamp": "2024-01-01T00:00:00"}


class TestPipeline:
    def test_empty_pipeline_returns_all(self):
        entries = [_entry(), _entry("world")]
        result = list(Pipeline().run(entries))
        assert result == entries

    def test_add_step_returns_self(self):
        p = Pipeline()
        ret = p.add_step(make_filter_step(lambda e: True))
        assert ret is p

    def test_len_reflects_step_count(self):
        p = Pipeline()
        assert len(p) == 0
        p.add_step(make_filter_step(lambda e: True))
        assert len(p) == 1

    def test_filter_step_removes_entries(self):
        entries = [_entry(level="ERROR"), _entry(level="INFO"), _entry(level="ERROR")]
        step = make_filter_step(lambda e: e["level"] == "ERROR")
        result = list(Pipeline().add_step(step).run(entries))
        assert len(result) == 2
        assert all(e["level"] == "ERROR" for e in result)

    def test_transform_step_mutates_entries(self):
        entries = [_entry("hello")]
        step = make_transform_step(lambda e: {**e, "message": e["message"].upper()})
        result = list(Pipeline().add_step(step).run(entries))
        assert result[0]["message"] == "HELLO"

    def test_multiple_steps_applied_in_order(self):
        entries = [_entry("abc", "INFO"), _entry("xyz", "ERROR"), _entry("abc", "ERROR")]
        f1 = make_filter_step(lambda e: e["level"] == "ERROR")
        f2 = make_filter_step(lambda e: e["message"] == "abc")
        result = list(Pipeline().add_step(f1).add_step(f2).run(entries))
        assert len(result) == 1
        assert result[0]["message"] == "abc"

    def test_empty_input_yields_nothing(self):
        step = make_filter_step(lambda e: True)
        result = list(Pipeline().add_step(step).run([]))
        assert result == []


class TestBuildPipeline:
    def test_returns_pipeline_with_all_steps(self):
        steps = [
            make_filter_step(lambda e: True),
            make_transform_step(lambda e: e),
        ]
        p = build_pipeline(steps)
        assert isinstance(p, Pipeline)
        assert len(p) == 2

    def test_empty_steps_list(self):
        p = build_pipeline([])
        assert len(p) == 0


class TestMakeFilterStep:
    def test_all_pass(self):
        entries = [_entry(), _entry()]
        result = list(make_filter_step(lambda e: True)(entries))
        assert result == entries

    def test_none_pass(self):
        entries = [_entry(), _entry()]
        result = list(make_filter_step(lambda e: False)(entries))
        assert result == []


class TestMakeTransformStep:
    def test_appends_field(self):
        entries = [_entry()]
        step = make_transform_step(lambda e: {**e, "extra": 1})
        result = list(step(entries))
        assert result[0]["extra"] == 1

    def test_original_not_mutated(self):
        original = _entry()
        step = make_transform_step(lambda e: {**e, "extra": 1})
        list(step([original]))
        assert "extra" not in original
