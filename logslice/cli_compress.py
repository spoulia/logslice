"""CLI sub-command: compress / decompress log files."""

import argparse
import sys

from logslice.compress import (
    detect_compression,
    iter_lines,
    write_compressed,
    compress_bytes,
    decompress_bytes,
)


def add_compress_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "compress",
        help="Compress or decompress a log file.",
    )
    p.add_argument("input", help="Source file path (use '-' for stdin).")
    p.add_argument("output", help="Destination file path.")
    p.add_argument(
        "--decompress",
        "-d",
        action="store_true",
        default=False,
        help="Decompress the input instead of compressing.",
    )
    p.add_argument(
        "--format",
        choices=["gz", "bz2", "xz"],
        default="gz",
        help="Compression format when reading from stdin (default: gz).",
    )
    p.add_argument(
        "--encoding",
        default="utf-8",
        help="Text encoding (default: utf-8).",
    )
    p.set_defaults(func=run_compress)


def _lines_from_stdin(encoding: str):
    for line in sys.stdin:
        yield line.rstrip("\n")


def run_compress(args: argparse.Namespace) -> None:
    use_stdin = args.input == "-"

    if args.decompress:
        if use_stdin:
            raw = sys.stdin.buffer.read()
            data = decompress_bytes(raw, fmt=args.format)
            sys.stdout.buffer.write(data)
            return
        # Source is a compressed file; output is plain text
        lines = iter_lines(args.input, encoding=args.encoding)
        count = write_compressed(args.output, lines, encoding=args.encoding)
    else:
        if use_stdin:
            raw = sys.stdin.buffer.read()
            data = compress_bytes(raw, fmt=args.format)
            with open(args.output, "wb") as fh:
                fh.write(data)
            count = raw.count(b"\n")
        else:
            compression = detect_compression(args.input)
            if compression is None and detect_compression(args.output) is None:
                print(
                    "warning: neither input nor output has a known compressed extension",
                    file=sys.stderr,
                )
            lines = iter_lines(args.input, encoding=args.encoding)
            count = write_compressed(args.output, lines, encoding=args.encoding)

    print(f"Done. {count} line(s) processed.", file=sys.stderr)
