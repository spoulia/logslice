"""CLI sub-commands for snapshot: create, restore, diff."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Iterator

from logslice.snapshot import (
    create_snapshot,
    diff_snapshots,
    load_snapshot,
    restore_entries,
    save_snapshot,
)


def add_snapshot_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser("snapshot", help="Capture or restore log snapshots")
    sub = p.add_subparsers(dest="snapshot_cmd", required=True)

    # create
    c = sub.add_parser("create", help="Save current stdin entries to a snapshot file")
    c.add_argument("output", help="Destination .json file")
    c.add_argument("--label", default="", help="Human-readable label for this snapshot")

    # restore
    r = sub.add_parser("restore", help="Print entries from a snapshot file")
    r.add_argument("input", help="Snapshot .json file to read")

    # diff
    d = sub.add_parser("diff", help="Show entries added/removed between two snapshots")
    d.add_argument("old", help="Older snapshot file")
    d.add_argument("new", help="Newer snapshot file")
    d.add_argument("--key", default="message", help="Field used to identify entries (default: message)")


def _read_entries() -> Iterator[dict]:
    for line in sys.stdin:
        line = line.strip()
        if line:
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                yield {"message": line}


def run_snapshot(args: argparse.Namespace) -> None:
    cmd = args.snapshot_cmd

    if cmd == "create":
        snap = create_snapshot(_read_entries(), label=args.label)
        path = save_snapshot(snap, args.output)
        print(f"Snapshot saved: {path} ({snap['count']} entries)", file=sys.stderr)

    elif cmd == "restore":
        snap = load_snapshot(args.input)
        for entry in restore_entries(snap):
            print(json.dumps(entry, default=str))

    elif cmd == "diff":
        old = load_snapshot(args.old)
        new = load_snapshot(args.new)
        result = diff_snapshots(old, new, key=args.key)
        print(json.dumps(result, indent=2, default=str))
