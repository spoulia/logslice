"""Entry point for the logslice command-line interface."""

import argparse
import sys

from logslice.cli_summary import add_summary_subparser
from logslice.cli_tail import add_tail_subparser
from logslice.cli_highlight import add_highlight_subparser
from logslice.cli_redact import add_redact_subparser
from logslice.cli_aggregate import add_aggregate_subparser
from logslice.cli_export import add_export_subparser
from logslice.cli_alert import add_alert_subparser
from logslice.cli_pipeline import add_pipeline_subparser
from logslice.cli_replay import add_replay_subparser


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logslice",
        description="Fast log filtering and analysis utility.",
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

    return parser


def run(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    args.func(args)


def main() -> None:  # pragma: no cover
    run()
