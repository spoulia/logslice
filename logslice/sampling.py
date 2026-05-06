"""Log entry sampling utilities for logslice."""

from typing import List, Dict, Any, Optional
import random
import math


def sample_entries(
    entries: List[Dict[str, Any]],
    rate: float,
    seed: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Return a random sample of entries at the given rate (0.0–1.0).

    Args:
        entries: List of parsed log entry dicts.
        rate: Fraction of entries to keep (e.g. 0.1 keeps ~10%).
        seed: Optional random seed for reproducibility.

    Returns:
        Sampled subset of entries.

    Raises:
        ValueError: If rate is not in the range (0, 1].
    """
    if not 0.0 < rate <= 1.0:
        raise ValueError(f"sample rate must be in (0, 1], got {rate}")

    if rate == 1.0:
        return list(entries)

    rng = random.Random(seed)
    return [e for e in entries if rng.random() < rate]


def sample_every_nth(
    entries: List[Dict[str, Any]],
    n: int,
) -> List[Dict[str, Any]]:
    """Keep every n-th entry (deterministic stride sampling).

    Args:
        entries: List of parsed log entry dicts.
        n: Stride — keep entries at indices 0, n, 2n, …

    Returns:
        Strided subset of entries.

    Raises:
        ValueError: If n is less than 1.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1, got {n}")
    return entries[::n]


def reservoir_sample(
    entries: List[Dict[str, Any]],
    k: int,
    seed: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Return exactly k entries chosen uniformly at random (reservoir sampling).

    Args:
        entries: List of parsed log entry dicts.
        k: Number of entries to return.
        seed: Optional random seed for reproducibility.

    Returns:
        A list of at most k entries.

    Raises:
        ValueError: If k is negative.
    """
    if k < 0:
        raise ValueError(f"k must be >= 0, got {k}")

    rng = random.Random(seed)
    return rng.sample(entries, min(k, len(entries)))
