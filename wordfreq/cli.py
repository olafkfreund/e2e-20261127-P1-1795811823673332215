"""Command-line entry point and word frequency helpers for wordfreq."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from collections.abc import Sequence
from pathlib import Path

_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+")
_STDIN_PATH = "-"


def count_words(
    text: str,
    *,
    min_len: int = 1,
    ignore_case: bool = True,
    top: int | None = None,
) -> list[tuple[str, int]]:
    """Count word occurrences in *text* and return `(word, count)` pairs."""
    if min_len < 1:
        msg = "min_len must be >= 1"
        raise ValueError(msg)
    if top is not None and top < 0:
        msg = "top must be >= 0"
        raise ValueError(msg)

    tokens = _TOKEN_PATTERN.findall(text)
    if ignore_case:
        tokens = [token.lower() for token in tokens]
    counts = Counter(token for token in tokens if len(token) >= min_len)
    ranked = sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))
    if top is None:
        return ranked
    return ranked[:top]


def format_table(rows: Sequence[tuple[str, int]]) -> str:
    """Format `(word, count)` pairs as tab-separated lines."""
    return "\n".join(f"{word}\t{count}" for word, count in rows)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wordfreq",
        description="Deterministically count and rank words in text.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=_STDIN_PATH,
        help="UTF-8 text file to read; '-' or omitted reads from stdin",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=None,
        help="show only the N most frequent words (default: all)",
    )
    parser.add_argument(
        "--min-len",
        type=int,
        default=1,
        help="ignore words shorter than M characters (default: 1)",
    )
    parser.add_argument(
        "--case-sensitive",
        action="store_true",
        help="preserve token case instead of lowercasing",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit a JSON array of {word, count} objects",
    )
    return parser


def _read_stdin() -> str:
    buffer = getattr(sys.stdin, "buffer", None)
    if buffer is None:
        return sys.stdin.read()
    return buffer.read().decode("utf-8")


def _read_input(path: str) -> str:
    if path == _STDIN_PATH:
        return _read_stdin()
    return Path(path).read_text(encoding="utf-8")


def _fail(message: str) -> int:
    print(f"wordfreq: error: {message}", file=sys.stderr)
    return 2


def main(argv: Sequence[str] | None = None) -> int:
    """Run the wordfreq CLI and return the process exit code."""
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2

    if args.min_len < 1:
        return _fail("--min-len must be >= 1")
    if args.top is not None and args.top < 0:
        return _fail("--top must be >= 0")

    try:
        text = _read_input(args.path)
    except OSError as exc:
        return _fail(f"cannot read {args.path!r}: {exc}")
    except UnicodeDecodeError as exc:
        return _fail(f"input is not valid UTF-8: {exc}")

    rows = count_words(
        text,
        min_len=args.min_len,
        ignore_case=not args.case_sensitive,
        top=args.top,
    )

    if args.json:
        payload = [{"word": word, "count": count} for word, count in rows]
        sys.stdout.write(json.dumps(payload) + "\n")
        return 0

    table = format_table(rows)
    if table:
        sys.stdout.write(table + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
