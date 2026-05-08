"""Tests for logslice.aggregate."""

from datetime import datetime, timezone
from typing import Any, Dict

import pytest

from logslice.aggregate import (
    _bucket_timestamp,
    count_by_field,
    count_by_time,
    group_by_field,
    group_by_time,
)


def _entry(level: str = "INFO", source: str = "app", ts: datetime = None) -> Dict[str, Any]:
    e: Dict[str, Any] = {"message": "msg", "level": level, "source": source}
    if ts is not None:
        e["timestamp"] = ts
    return e


_DT_HOUR1 = datetime(2024, 3, 15, 10, 5, 0, tzinfo=timezone.utc)
_DT_HOUR1B = datetime(2024, 3, 15, 10, 45, 0, tzinfo=timezone.utc)
_DT_HOUR2 = datetime(2024, 3, 15, 11, 0, 0, tzinfo=timezone.utc)


class TestBucketTimestamp:
    def test_minute_bucket(self):
        assert _bucket_timestamp(_DT_HOUR1, "minute") == "2024-03-15T10:05"

    def test_hour_bucket(self):
        assert _bucket_timestamp(_DT_HOUR1, "hour") == "2024-03-15T10"
        assert _bucket_timestamp(_DT_HOUR1B, "hour") == "2024-03-15T10"

    def test_day_bucket(self):
        assert _bucket_timestamp(_DT_HOUR2, "day") == "2024-03-15"

    def test_none_returns_none(self):
        assert _bucket_timestamp(None, "hour") is None

    def test_unknown_interval_raises(self):
        with pytest.raises(ValueError, match="Unknown interval"):
            _bucket_timestamp(_DT_HOUR1, "week")


class TestGroupByField:
    def test_groups_by_level(self):
        entries = [_entry("INFO"), _entry("ERROR"), _entry("INFO")]
        groups = group_by_field(entries, "level")
        assert len(groups["INFO"]) == 2
        assert len(groups["ERROR"]) == 1

    def test_missing_field_grouped_under_missing(self):
        entries = [_entry(), {"message": "no-level"}]
        groups = group_by_field(entries, "level")
        assert "<missing>" in groups
        assert len(groups["<missing>"]) == 1

    def test_empty_input(self):
        assert group_by_field([], "level") == {}


class TestCountByField:
    def test_counts_match_groups(self):
        entries = [_entry("WARN"), _entry("WARN"), _entry("DEBUG")]
        counts = count_by_field(entries, "level")
        assert counts["WARN"] == 2
        assert counts["DEBUG"] == 1

    def test_returns_dict(self):
        assert isinstance(count_by_field([], "level"), dict)


class TestGroupByTime:
    def test_same_hour_same_bucket(self):
        entries = [_entry(ts=_DT_HOUR1), _entry(ts=_DT_HOUR1B)]
        groups = group_by_time(entries, "hour")
        assert len(groups) == 1
        assert len(list(groups.values())[0]) == 2

    def test_different_hours_different_buckets(self):
        entries = [_entry(ts=_DT_HOUR1), _entry(ts=_DT_HOUR2)]
        groups = group_by_time(entries, "hour")
        assert len(groups) == 2

    def test_no_timestamp_grouped_separately(self):
        entries = [_entry(), _entry(ts=_DT_HOUR1)]
        groups = group_by_time(entries, "hour")
        assert "<no-timestamp>" in groups


class TestCountByTime:
    def test_counts_correct(self):
        entries = [_entry(ts=_DT_HOUR1), _entry(ts=_DT_HOUR1B), _entry(ts=_DT_HOUR2)]
        counts = count_by_time(entries, "hour")
        assert counts["2024-03-15T10"] == 2
        assert counts["2024-03-15T11"] == 1
