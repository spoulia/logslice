"""Checkpoint support — persist and resume log processing position."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

_DEFAULT_DIR = Path.home() / ".logslice" / "checkpoints"


def _checkpoint_path(name: str, directory: Path) -> Path:
    safe = name.replace(os.sep, "_").replace(".", "_")
    return directory / f"{safe}.json"


def save_checkpoint(
    name: str,
    position: int,
    *,
    directory: Optional[Path] = None,
    extra: Optional[dict] = None,
) -> Path:
    """Persist *position* (byte offset) for *name* (e.g. a file path).

    Returns the path of the written checkpoint file.
    """
    directory = Path(directory) if directory else _DEFAULT_DIR
    directory.mkdir(parents=True, exist_ok=True)
    path = _checkpoint_path(name, directory)
    payload: dict = {"name": name, "position": position}
    if extra:
        payload["extra"] = extra
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def load_checkpoint(
    name: str,
    *,
    directory: Optional[Path] = None,
) -> Optional[dict]:
    """Load a previously saved checkpoint for *name*.

    Returns ``None`` when no checkpoint exists.
    """
    directory = Path(directory) if directory else _DEFAULT_DIR
    path = _checkpoint_path(name, directory)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def clear_checkpoint(name: str, *, directory: Optional[Path] = None) -> bool:
    """Delete the checkpoint for *name*.  Returns True if it existed."""
    directory = Path(directory) if directory else _DEFAULT_DIR
    path = _checkpoint_path(name, directory)
    if path.exists():
        path.unlink()
        return True
    return False


def get_position(name: str, *, directory: Optional[Path] = None) -> int:
    """Return the saved byte offset for *name*, or 0 if none exists."""
    cp = load_checkpoint(name, directory=directory)
    if cp is None:
        return 0
    return int(cp.get("position", 0))
