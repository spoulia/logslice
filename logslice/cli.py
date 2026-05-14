"""Entry point for the logslice command-line interface."""

from __future__ import annotations

import argparse
import sys

from logslice.cli_summary import add_summary_subparser, run_summary
from logslice.cli_tail import add_tail_subparser, run_tail
from logslice.cli_highlight import add_highlight_subparser, run_highlight
from logslice.cli_redact import add_redact_subparser, run_redact
from logslice.cli_aggregate import add_aggregate_subparser, run_aggregate
from logslice.cli_export import add_export_subparser, run_export
from logslice.cli_alert import add_alert_subparser, run_alert
from logslice.cli_pipeline import add_pipeline_subparser, run_pipeline
from logslice.cli_replay import add_replay_subparser, run_replay
from logslice.cli_rotate import add_rotate_subparser, run_rotate
from logslice.cli_schema import add_schema_subparser, run_schema
from logslice.cli_enrich import add_enrich_subparser, run_enrich
from logslice.cli_normalize import add_normalize_subparser, run_normalize
from logslice.cli_label import add_label_subparser, run_label
from logslice.cli_diff import add_diff_subparser, run_diff

_SUBCOMMANDS = [
    ("summary", add_summary_subparser, run_summary),
    ("tail", add_tail_subparser, run_tail),
    ("highlight", add_highlight_subparser, run_highlight),
    ("redact", add_redact_subparser, run_redact),
    ("aggregate", add_aggregate_subparser, run_aggregate),
    ("export", add_export_subparser, run_export),
    ("alert", add_alert_subparser, run_alert),
    ("pipeline", add_pipeline_subparser, run_pipeline),
    ("replay", add_replay_subparser, run_replay),
    ("rotate", add_rotate_subparser, run_rotate),
    ("schema", add_schema_subparser, run_schema),
    ("enrich", add_enrich_subparser, run_enrich),
    ("normalize", add_normalize_subparser, run_normalize),
    ("label", add_label_subparser, run_label),
    ("diff", add_diff_subparser, run_diff),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logslice",
        description="Fast log filtering and analysis utility.",
    )
    subparsers = parser.add_subparsers(dest="command")
    for _name, add_fn, _run_fn in _SUBCOMMANDS:
        add_fn(subparsers)
    return parser


def run(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        sys.exit(0)
    for name, _add_fn, run_fn in _SUBCOMMANDS:
        if args.command == name:
            run_fn(args)
            return
    parser.print_help()
    sys.exit(1)


def main() -> None:  # pragma: no cover
    run()
