"""Utilities for reading and writing compressed log files."""

import gzip
import bz2
import lzma
import io
import os
from typing import Iterator, IO

_OPENERS = {
    ".gz": gzip.open,
    ".bz2": bz2.open,
    ".xz": lzma.open,
    ".lzma": lzma.open,
}


def detect_compression(path: str) -> str | None:
    """Return the compression type for *path* based on its extension, or None."""
    _, ext = os.path.splitext(path)
    return ext if ext in _OPENERS else None


def open_compressed(path: str, mode: str = "rt", encoding: str = "utf-8") -> IO:
    """Open a file for reading, decompressing automatically if needed.

    Falls back to a plain ``open`` for unrecognised extensions.
    """
    _, ext = os.path.splitext(path)
    opener = _OPENERS.get(ext)
    if opener is None:
        return open(path, mode, encoding=encoding)
    # gzip / bz2 / lzma all accept mode and encoding in text mode
    return opener(path, mode, encoding=encoding)


def iter_lines(path: str, encoding: str = "utf-8") -> Iterator[str]:
    """Yield stripped lines from a plain or compressed file."""
    with open_compressed(path, "rt", encoding=encoding) as fh:
        for line in fh:
            yield line.rstrip("\n")


def write_compressed(path: str, lines: Iterator[str], encoding: str = "utf-8") -> int:
    """Write *lines* to *path*, compressing if the extension demands it.

    Returns the number of lines written.
    """
    count = 0
    with open_compressed(path, "wt", encoding=encoding) as fh:
        for line in lines:
            fh.write(line + "\n")
            count += 1
    return count


def compress_bytes(data: bytes, fmt: str = "gz") -> bytes:
    """Compress *data* in memory using *fmt* (``gz``, ``bz2``, or ``xz``)."""
    buf = io.BytesIO()
    if fmt == "gz":
        with gzip.GzipFile(fileobj=buf, mode="wb") as gz:
            gz.write(data)
    elif fmt == "bz2":
        buf.write(bz2.compress(data))
    elif fmt in ("xz", "lzma"):
        buf.write(lzma.compress(data))
    else:
        raise ValueError(f"Unknown compression format: {fmt!r}")
    return buf.getvalue()


def decompress_bytes(data: bytes, fmt: str = "gz") -> bytes:
    """Decompress *data* in memory using *fmt*."""
    if fmt == "gz":
        return gzip.decompress(data)
    if fmt == "bz2":
        return bz2.decompress(data)
    if fmt in ("xz", "lzma"):
        return lzma.decompress(data)
    raise ValueError(f"Unknown compression format: {fmt!r}")
