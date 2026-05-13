"""Log rotation detection and handling utilities."""

from __future__ import annotations

import os
from typing import Iterator, List, Optional


def _file_inode(path: str) -> Optional[int]:
    """Return the inode number of *path*, or None if the file does not exist."""
    try:
        return os.stat(path).st_ino
    except FileNotFoundError:
        return None


def _file_size(path: str) -> int:
    """Return the size of *path* in bytes, or 0 if the file does not exist."""
    try:
        return os.stat(path).st_size
    except FileNotFoundError:
        return 0


def detect_rotation(path: str, last_inode: Optional[int], last_size: int) -> bool:
    """Return True if *path* has been rotated since the last check.

    Rotation is detected when:
    - the inode has changed (file replaced), or
    - the current file size is smaller than *last_size* (file truncated).
    """
    current_inode = _file_inode(path)
    if current_inode is None:
        return False
    if last_inode is not None and current_inode != last_inode:
        return True
    if _file_size(path) < last_size:
        return True
    return False


def read_new_lines(path: str, position: int) -> tuple[List[str], int]:
    """Read lines added to *path* since *position*.

    Returns a tuple of (new_lines, new_position).
    If the file is shorter than *position* (truncated), reading restarts from 0.
    """
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            size = os.fstat(fh.fileno()).st_size
            seek_pos = position if size >= position else 0
            fh.seek(seek_pos)
            lines = fh.readlines()
            new_position = fh.tell()
    except FileNotFoundError:
        return [], position
    return [line.rstrip("\n") for line in lines], new_position


def iter_with_rotation(path: str, start_position: int = 0) -> Iterator[tuple[str, int]]:
    """Yield (line, position_after_line) pairs, restarting from 0 on rotation.

    This is a one-shot iterator — it reads until EOF and returns.
    For continuous tailing see :mod:`logslice.tail`.
    """
    inode = _file_inode(path)
    lines, pos = read_new_lines(path, start_position)
    for line in lines:
        yield line, pos
