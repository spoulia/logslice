"""CLI sub-command: pipeline — run a pre-defined chain of filters/transforms."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from logslice.core import parse_log_line
from logslice.filters import filter_by_level, filter_by_pattern
from logslice.pipeline import Pipeline, make_filter_step, make_transform_step
from logslice.redact import redact_entry


def add_pipeline_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("pipeline", help="Run a chained filter/transform pipeline")
    p.add_argument("file", nargs="?", help="Input log file (default: stdin)")
    p.add_argument("--level", default=None, help="Minimum log level to include")
    p.add_argument("--pattern", default=None, help="Regex pattern to match")
    p.add_argument("--redact", action="store_true", help="Redact sensitive fields")
    p.add_argument("--output", default="json", choices=["json", "text"], help="Output format")


def _read_entries(file_path: str | None) -> List[dict]:
    if file_path:
        with open(file_path) as fh:
            lines = fh.readlines()
    else:
        lines = sys.stdin.readlines()
    return [e for line in lines if (e := parse_log_line(line.rstrip())) is not None]


def run_pipeline(args: argparse.Namespace) -> None:
    entries = _read_entries(getattr(args, "file", None))
    pipeline = Pipeline()

    if args.level:
        level = args.level
        pipeline.add_step(make_filter_step(lambda e, lv=level: filter_by_level([e], lv) != []))

    if args.pattern:
        pattern = args.pattern
        pipeline.add_step(make_filter_step(lambda e, p=pattern: bool(filter_by_pattern([e], p))))

    if args.redact:
        pipeline.add_step(make_transform_step(redact_entry))

    results = list(pipeline.run(entries))

    if args.output == "json":
        print(json.dumps(results, indent=2, default=str))
    else:
        for entry in results:
            msg = entry.get("message", "")
            level = entry.get("level", "")
            ts = entry.get("timestamp", "")
            print(f"[{ts}] [{level}] {msg}")
