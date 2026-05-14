"""Command-line entry point for logslice."""

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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logslice",
        description="Fast log filtering and analysis utility",
    )
    subparsers = parser.add_subparsers(dest="command")

    add_summary_subparser(subparsers)
    add_tail_subparser(subparsers)
    add_highlight_subparser(subparsers)
    add_redact_subparser(subparsers)
    add_aggregate_subparser(subparsers)
    add_export_subparser(subparsers)
    add_alert_subparser(subparsers)
    add_pipeline_subparser(subparsers)
    add_replay_subparser(subparsers)
    add_rotate_subparser(subparsers)
    add_schema_subparser(subparsers)
    add_enrich_subparser(subparsers)

    return parser


_RUNNERS = {
    "summary": run_summary,
    "tail": run_tail,
    "highlight": run_highlight,
    "redact": run_redact,
    "aggregate": run_aggregate,
    "export": run_export,
    "alert": run_alert,
    "pipeline": run_pipeline,
    "replay": run_replay,
    "rotate": run_rotate,
    "schema": run_schema,
    "enrich": run_enrich,
}


def run(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        sys.exit(0)
    _RUNNERS[args.command](args)


def main() -> None:  # pragma: no cover
    run()
