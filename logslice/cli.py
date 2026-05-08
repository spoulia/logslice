"""Entry-point: build the top-level argument parser and dispatch sub-commands."""

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

_COMMANDS = {
    "summary": run_summary,
    "tail": run_tail,
    "highlight": run_highlight,
    "redact": run_redact,
    "aggregate": run_aggregate,
    "export": run_export,
    "alert": run_alert,
    "pipeline": run_pipeline,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logslice",
        description="Fast log filtering and analysis utility.",
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True

    add_summary_subparser(sub)
    add_tail_subparser(sub)
    add_highlight_subparser(sub)
    add_redact_subparser(sub)
    add_aggregate_subparser(sub)
    add_export_subparser(sub)
    add_alert_subparser(sub)
    add_pipeline_subparser(sub)

    return parser


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    handler = _COMMANDS.get(args.command)
    if handler is None:
        parser.print_help()
        return 1
    try:
        handler(args)
        return 0
    except (BrokenPipeError, KeyboardInterrupt):
        return 0
    except Exception as exc:  # pragma: no cover
        print(f"logslice: error: {exc}", file=sys.stderr)
        return 1


def main() -> None:  # pragma: no cover
    sys.exit(run())
