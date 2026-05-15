"""Entry point for the logslice CLI."""

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
from logslice.cli_schema import add_schema_subparser, run_schema
from logslice.cli_enrich import add_enrich_subparser, run_enrich
from logslice.cli_normalize import add_normalize_subparser, run_normalize
from logslice.cli_label import add_label_subparser, run_label
from logslice.cli_diff import add_diff_subparser, run_diff
from logslice.cli_partition import add_partition_subparser, run_partition
from logslice.cli_merge import add_merge_subparser, run_merge
from logslice.cli_rate import add_rate_subparser, run_rate
from logslice.cli_sort import add_sort_subparser, run_sort
from logslice.cli_split import add_split_subparser, run_split
from logslice.cli_rotate import add_rotate_subparser, run_rotate
from logslice.cli_index import add_index_subparser, run_index


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
    ("schema", add_schema_subparser, run_schema),
    ("enrich", add_enrich_subparser, run_enrich),
    ("normalize", add_normalize_subparser, run_normalize),
    ("label", add_label_subparser, run_label),
    ("diff", add_diff_subparser, run_diff),
    ("partition", add_partition_subparser, run_partition),
    ("merge", add_merge_subparser, run_merge),
    ("rate", add_rate_subparser, run_rate),
    ("sort", add_sort_subparser, run_sort),
    ("split", add_split_subparser, run_split),
    ("rotate", add_rotate_subparser, run_rotate),
    ("index", add_index_subparser, run_index),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logslice",
        description="Fast log filtering and analysis utility.",
    )
    subparsers = parser.add_subparsers(dest="subcommand")
    for _name, adder, runner in _SUBCOMMANDS:
        adder(subparsers)
        # stash runner on the namespace via set_defaults inside each adder
    return parser


def run(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.subcommand is None:
        parser.print_help()
        sys.exit(0)
    for name, _adder, runner in _SUBCOMMANDS:
        if args.subcommand == name:
            runner(args)
            return
    parser.print_help()
    sys.exit(1)


def main() -> None:  # pragma: no cover
    run()
