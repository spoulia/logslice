"""Tests for logslice.tail."""

import os
import tempfile
import threading
import time

import pytest

from logslice.tail import tail_file


def _write_lines(path: str, lines: list, delay: float = 0.05) -> None:
    """Append *lines* to *path* with a small delay between each."""
    with open(path, "a", encoding="utf-8") as fh:
        for line in lines:
            time.sleep(delay)
            fh.write(line + "\n")
            fh.flush()


def _run_tail(path, collected, **kwargs):
    """Run tail_file in a thread; stops after KeyboardInterrupt injected via event."""
    stop = threading.Event()

    def _cb(entry):
        collected.append(entry)
        if len(collected) >= kwargs.pop("_stop_after", 999):
            stop.set()

    def _tail():
        try:
            tail_file(path, _cb, poll_interval=0.05, **kwargs)
        except Exception:
            pass

    t = threading.Thread(target=_tail, daemon=True)
    t.start()
    return t, stop


class TestTailFile:
    def test_receives_new_lines(self, tmp_path):
        log_file = tmp_path / "app.log"
        log_file.write_text("")  # create empty file

        collected = []
        lines = [
            '2024-01-01T10:00:00 INFO starting up',
            '2024-01-01T10:00:01 INFO ready',
        ]

        t = threading.Thread(
            target=tail_file,
            args=(str(log_file), collected.append),
            kwargs={"poll_interval": 0.05},
            daemon=True,
        )
        t.start()

        _write_lines(str(log_file), lines, delay=0.05)
        time.sleep(0.4)
        t.join(timeout=0.1)

        assert len(collected) == 2
        assert collected[0]["message"] is not None

    def test_level_filter_excludes_low_severity(self, tmp_path):
        log_file = tmp_path / "app.log"
        log_file.write_text("")

        collected = []
        lines = [
            '2024-01-01T10:00:00 DEBUG verbose detail',
            '2024-01-01T10:00:01 ERROR something broke',
        ]

        t = threading.Thread(
            target=tail_file,
            args=(str(log_file), collected.append),
            kwargs={"poll_interval": 0.05, "min_level": "error"},
            daemon=True,
        )
        t.start()

        _write_lines(str(log_file), lines, delay=0.05)
        time.sleep(0.4)
        t.join(timeout=0.1)

        assert len(collected) == 1
        assert (collected[0].get("level") or "").lower() == "error"

    def test_pattern_filter(self, tmp_path):
        log_file = tmp_path / "app.log"
        log_file.write_text("")

        collected = []
        lines = [
            '2024-01-01T10:00:00 INFO user login',
            '2024-01-01T10:00:01 INFO payment processed',
        ]

        t = threading.Thread(
            target=tail_file,
            args=(str(log_file), collected.append),
            kwargs={"poll_interval": 0.05, "pattern": "payment"},
            daemon=True,
        )
        t.start()

        _write_lines(str(log_file), lines, delay=0.05)
        time.sleep(0.4)
        t.join(timeout=0.1)

        assert len(collected) == 1
        assert "payment" in collected[0].get("message", "")

    def test_missing_file_raises(self, tmp_path):
        """tail_file should raise FileNotFoundError when the target path does not exist."""
        missing = tmp_path / "nonexistent.log"

        with pytest.raises(FileNotFoundError):
            tail_file(str(missing), lambda entry: None, poll_interval=0.05)
