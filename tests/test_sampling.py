"""Tests for logslice.sampling."""

import pytest
from logslice.sampling import sample_entries, sample_every_nth, reservoir_sample


def _make_entries(n: int):
    return [{"message": f"msg {i}", "level": "INFO"} for i in range(n)]


# ---------------------------------------------------------------------------
# sample_entries
# ---------------------------------------------------------------------------

class TestSampleEntries:
    def test_rate_one_returns_all(self):
        entries = _make_entries(10)
        assert sample_entries(entries, 1.0) == entries

    def test_rate_zero_raises(self):
        with pytest.raises(ValueError):
            sample_entries(_make_entries(10), 0.0)

    def test_rate_above_one_raises(self):
        with pytest.raises(ValueError):
            sample_entries(_make_entries(10), 1.5)

    def test_empty_input_returns_empty(self):
        assert sample_entries([], 0.5) == []

    def test_reproducible_with_seed(self):
        entries = _make_entries(100)
        a = sample_entries(entries, 0.3, seed=42)
        b = sample_entries(entries, 0.3, seed=42)
        assert a == b

    def test_different_seeds_may_differ(self):
        entries = _make_entries(100)
        a = sample_entries(entries, 0.5, seed=1)
        b = sample_entries(entries, 0.5, seed=2)
        # With 100 entries and 50% rate the chance of identical results is negligible
        assert a != b

    def test_approximate_rate(self):
        entries = _make_entries(10_000)
        sampled = sample_entries(entries, 0.1, seed=0)
        assert 800 <= len(sampled) <= 1200


# ---------------------------------------------------------------------------
# sample_every_nth
# ---------------------------------------------------------------------------

class TestSampleEveryNth:
    def test_n_one_returns_all(self):
        entries = _make_entries(5)
        assert sample_every_nth(entries, 1) == entries

    def test_n_two_returns_half(self):
        entries = _make_entries(6)
        result = sample_every_nth(entries, 2)
        assert len(result) == 3
        assert result == entries[::2]

    def test_n_zero_raises(self):
        with pytest.raises(ValueError):
            sample_every_nth(_make_entries(5), 0)

    def test_empty_input(self):
        assert sample_every_nth([], 3) == []

    def test_n_larger_than_list(self):
        entries = _make_entries(3)
        assert sample_every_nth(entries, 10) == [entries[0]]


# ---------------------------------------------------------------------------
# reservoir_sample
# ---------------------------------------------------------------------------

class TestReservoirSample:
    def test_k_zero_returns_empty(self):
        assert reservoir_sample(_make_entries(10), 0) == []

    def test_k_negative_raises(self):
        with pytest.raises(ValueError):
            reservoir_sample(_make_entries(5), -1)

    def test_k_larger_than_list_returns_all(self):
        entries = _make_entries(5)
        result = reservoir_sample(entries, 100, seed=0)
        assert len(result) == 5

    def test_exact_k_returned(self):
        entries = _make_entries(50)
        result = reservoir_sample(entries, 10, seed=7)
        assert len(result) == 10

    def test_reproducible_with_seed(self):
        entries = _make_entries(50)
        a = reservoir_sample(entries, 10, seed=99)
        b = reservoir_sample(entries, 10, seed=99)
        assert a == b

    def test_empty_input(self):
        assert reservoir_sample([], 5) == []
