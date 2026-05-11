"""Tests for logslice.replay."""

import datetime
import pytest

from logslice.replay import _delta_seconds, replay_entries, collect_replay


def _ts(hour: int, minute: int = 0, second: int = 0) -> datetime.datetime:
    return datetime.datetime(2024, 1, 1, hour, minute, second)


def _e(ts=None, msg="hello"):
    return {"timestamp": ts, "message": msg, "level": "INFO", "raw": msg}


# ---------------------------------------------------------------------------
# _delta_seconds
# ---------------------------------------------------------------------------

class TestDeltaSeconds:
    def test_none_prev_returns_zero(self):
        assert _delta_seconds(None, _e(_ts(10))) == 0.0

    def test_same_timestamp_returns_zero(self):
        e = _e(_ts(10))
        assert _delta_seconds(e, e) == 0.0

    def test_one_second_apart(self):
        prev = _e(_ts(10, 0, 0))
        cur = _e(_ts(10, 0, 1))
        assert _delta_seconds(prev, cur) == pytest.approx(1.0)

    def test_negative_delta_clamped_to_zero(self):
        prev = _e(_ts(10, 0, 5))
        cur = _e(_ts(10, 0, 0))
        assert _delta_seconds(prev, cur) == 0.0

    def test_missing_timestamp_returns_zero(self):
        prev = {"message": "a"}
        cur = {"message": "b"}
        assert _delta_seconds(prev, cur) == 0.0


# ---------------------------------------------------------------------------
# replay_entries
# ---------------------------------------------------------------------------

class TestReplayEntries:
    def test_invalid_speed_raises(self):
        with pytest.raises(ValueError):
            list(replay_entries([], speed=0))

    def test_negative_speed_raises(self):
        with pytest.raises(ValueError):
            list(replay_entries([], speed=-1))

    def test_yields_all_entries(self):
        entries = [_e(msg=str(i)) for i in range(5)]
        result = list(replay_entries(entries, speed=1.0, max_delay=0.0))
        assert len(result) == 5

    def test_order_preserved(self):
        entries = [_e(msg=str(i)) for i in range(3)]
        result = list(replay_entries(entries, speed=1.0, max_delay=0.0))
        assert [r["message"] for r in result] == ["0", "1", "2"]

    def test_callback_called_for_each(self):
        entries = [_e(msg=str(i)) for i in range(4)]
        seen = []
        list(replay_entries(entries, speed=1.0, max_delay=0.0, callback=seen.append))
        assert len(seen) == 4

    def test_max_delay_limits_sleep(self, monkeypatch):
        slept = []
        monkeypatch.setattr("logslice.replay.time.sleep", slept.append)
        entries = [
            _e(_ts(10, 0, 0)),
            _e(_ts(10, 0, 30)),  # 30-second gap
        ]
        list(replay_entries(entries, speed=1.0, max_delay=2.0))
        assert slept and slept[0] <= 2.0

    def test_speed_scales_delay(self, monkeypatch):
        slept = []
        monkeypatch.setattr("logslice.replay.time.sleep", slept.append)
        entries = [
            _e(_ts(10, 0, 0)),
            _e(_ts(10, 0, 10)),  # 10-second gap
        ]
        list(replay_entries(entries, speed=2.0, max_delay=60.0))
        assert slept and slept[0] == pytest.approx(5.0)


# ---------------------------------------------------------------------------
# collect_replay
# ---------------------------------------------------------------------------

class TestCollectReplay:
    def test_returns_list(self):
        entries = [_e(msg="x")]
        result = collect_replay(entries, speed=1.0, max_delay=0.0)
        assert isinstance(result, list)
        assert result[0]["message"] == "x"
