"""Tests for logslice.compress."""

import gzip
import bz2
import lzma
import os
import textwrap

import pytest

from logslice.compress import (
    detect_compression,
    open_compressed,
    iter_lines,
    write_compressed,
    compress_bytes,
    decompress_bytes,
)


# ---------------------------------------------------------------------------
# detect_compression
# ---------------------------------------------------------------------------

class TestDetectCompression:
    def test_gz_extension(self):
        assert detect_compression("app.log.gz") == ".gz"

    def test_bz2_extension(self):
        assert detect_compression("app.log.bz2") == ".bz2"

    def test_xz_extension(self):
        assert detect_compression("app.log.xz") == ".xz"

    def test_lzma_extension(self):
        assert detect_compression("app.log.lzma") == ".lzma"

    def test_plain_returns_none(self):
        assert detect_compression("app.log") is None

    def test_no_extension_returns_none(self):
        assert detect_compression("logfile") is None


# ---------------------------------------------------------------------------
# iter_lines / open_compressed
# ---------------------------------------------------------------------------

def test_iter_lines_plain(tmp_path):
    f = tmp_path / "sample.log"
    f.write_text("line1\nline2\nline3\n")
    assert list(iter_lines(str(f))) == ["line1", "line2", "line3"]


def test_iter_lines_gzip(tmp_path):
    f = tmp_path / "sample.log.gz"
    with gzip.open(str(f), "wt") as fh:
        fh.write("alpha\nbeta\n")
    assert list(iter_lines(str(f))) == ["alpha", "beta"]


def test_iter_lines_bz2(tmp_path):
    f = tmp_path / "sample.log.bz2"
    with bz2.open(str(f), "wt") as fh:
        fh.write("hello\nworld\n")
    assert list(iter_lines(str(f))) == ["hello", "world"]


# ---------------------------------------------------------------------------
# write_compressed
# ---------------------------------------------------------------------------

def test_write_compressed_plain(tmp_path):
    dest = tmp_path / "out.log"
    n = write_compressed(str(dest), iter(["a", "b", "c"]))
    assert n == 3
    assert dest.read_text() == "a\nb\nc\n"


def test_write_compressed_gz(tmp_path):
    dest = tmp_path / "out.log.gz"
    n = write_compressed(str(dest), iter(["x", "y"]))
    assert n == 2
    with gzip.open(str(dest), "rt") as fh:
        assert fh.read() == "x\ny\n"


# ---------------------------------------------------------------------------
# compress_bytes / decompress_bytes
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("fmt", ["gz", "bz2", "xz"])
def test_roundtrip(fmt):
    original = b"hello compressed world\n" * 10
    compressed = compress_bytes(original, fmt=fmt)
    assert compressed != original
    restored = decompress_bytes(compressed, fmt=fmt)
    assert restored == original


def test_compress_bytes_unknown_format_raises():
    with pytest.raises(ValueError, match="Unknown compression format"):
        compress_bytes(b"data", fmt="zip")


def test_decompress_bytes_unknown_format_raises():
    with pytest.raises(ValueError, match="Unknown compression format"):
        decompress_bytes(b"data", fmt="zip")


def test_gz_output_is_smaller_for_repetitive_data():
    data = b"AAAA" * 1000
    assert len(compress_bytes(data, fmt="gz")) < len(data)
