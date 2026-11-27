# Criterion: main(argv) with monkeypatched sys.stdin (io.StringIO) and capsys:
# default stdin and '-' both read stdin; --case-sensitive preserves case;
# --top N truncates; --min-len N filters; TSV output ends with a single '\n';
# empty input writes nothing to stdout and returns 0.

import io
import sys

import pytest

from wordfreq.cli import main


@pytest.fixture
def feed_stdin(monkeypatch):
    def _feed(text):
        monkeypatch.setattr(sys, "stdin", io.StringIO(text))

    return _feed


@pytest.mark.parametrize(
    "argv",
    [[], ["-"]],
    ids=["default-stdin", "dash-stdin"],
)
def test_main_stdin_source_reads_input_and_outputs_word(feed_stdin, capsys, argv):
    feed_stdin("hello hello world\n")
    main(argv)
    assert "hello" in capsys.readouterr().out


def test_main_case_sensitive_preserves_case(feed_stdin, capsys):
    feed_stdin("Hello hello\n")
    main(["--case-sensitive"])
    assert "Hello" in capsys.readouterr().out


def test_main_top_n_truncates_output_lines(feed_stdin, capsys):
    feed_stdin("a a a b b c c c c d d d d d\n")
    main(["--top", "2"])
    lines = [line for line in capsys.readouterr().out.splitlines() if line.strip()]
    assert len(lines) == 2


def test_main_min_len_filters_short_words(feed_stdin, capsys):
    feed_stdin("a bb ccc\n")
    main(["--min-len", "3"])
    assert "bb" not in capsys.readouterr().out


def test_main_min_len_keeps_words_meeting_length(feed_stdin, capsys):
    feed_stdin("a bb ccc\n")
    main(["--min-len", "3"])
    assert "ccc" in capsys.readouterr().out


def test_main_tsv_output_ends_with_single_newline(feed_stdin, capsys):
    feed_stdin("alpha beta alpha\n")
    main([])
    out = capsys.readouterr().out
    assert out.endswith("\n") and not out.endswith("\n\n")


def test_main_empty_input_writes_nothing_to_stdout(feed_stdin, capsys):
    feed_stdin("")
    main([])
    assert capsys.readouterr().out == ""


def test_main_empty_input_returns_zero(feed_stdin):
    feed_stdin("")
    assert main([]) == 0
