# AC#4: pytest -q passes across tests/test_wordfreq.py
# Covers the end-to-end behaviour of count_words and main (AC#1-AC#3):
# tokenizing, casing, min_len filtering, (-count, word) sorting, argument
# validation, TSV/JSON output with trailing newlines, stdin handling,
# exit codes, and python -m wordfreq.

import io
import json
import subprocess
import sys

import pytest

from wordfreq.cli import count_words, format_table, main


# ---------------------------------------------------------------------------
# count_words
# ---------------------------------------------------------------------------

def test_count_words_mixed_case_default_lowercases_to_single_word():
    assert count_words("Hello hello") == [("hello", 2)]


def test_count_words_punctuated_text_extracts_alphanumeric_tokens():
    assert count_words("a-b_c d1") == [("a", 1), ("b", 1), ("c", 1), ("d1", 1)]


def test_count_words_ignore_case_false_preserves_case():
    assert count_words("Hello hello", ignore_case=False) == [("Hello", 1), ("hello", 1)]


def test_count_words_min_len_filters_short_tokens():
    assert count_words("a bb ccc", min_len=2) == [("bb", 1), ("ccc", 1)]


def test_count_words_sorts_by_count_descending():
    assert count_words("b a b c a b") == [("b", 3), ("a", 2), ("c", 1)]


def test_count_words_ties_sorted_by_word_ascending():
    assert count_words("b a") == [("a", 1), ("b", 1)]


def test_count_words_top_truncates_to_requested_size():
    assert count_words("b a b c a b", top=2) == [("b", 3), ("a", 2)]


def test_count_words_top_zero_returns_empty_list():
    assert count_words("b a b", top=0) == []


def test_count_words_min_len_below_one_raises_value_error():
    with pytest.raises(ValueError, match=r"^min_len must be >= 1$"):
        count_words("hello", min_len=0)


def test_count_words_negative_top_raises_value_error():
    with pytest.raises(ValueError, match=r"^top must be >= 0$"):
        count_words("hello", top=-1)


# ---------------------------------------------------------------------------
# format_table
# ---------------------------------------------------------------------------

def test_format_table_rows_joined_with_tabs_and_newlines():
    assert format_table([("hello", 2), ("world", 1)]) == "hello\t2\nworld\t1"


def test_format_table_empty_input_returns_empty_string():
    assert format_table([]) == ""


# ---------------------------------------------------------------------------
# main: stdin handling
# ---------------------------------------------------------------------------

def test_main_default_reads_stdin_and_prints_tsv(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", io.StringIO("hello hello world\n"))
    rc = main([])
    assert capsys.readouterr().out == "hello\t2\nworld\t1\n"
    assert rc == 0


def test_main_dash_path_reads_stdin(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", io.StringIO("hello hello world\n"))
    rc = main(["-"])
    assert capsys.readouterr().out == "hello\t2\nworld\t1\n"
    assert rc == 0


def test_main_empty_stdin_writes_nothing(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", io.StringIO(""))
    rc = main([])
    assert capsys.readouterr().out == ""
    assert rc == 0


# ---------------------------------------------------------------------------
# main: options
# ---------------------------------------------------------------------------

def test_main_case_sensitive_preserves_case(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", io.StringIO("Hello hello\n"))
    main(["--case-sensitive"])
    assert capsys.readouterr().out == "Hello\t1\nhello\t1\n"


def test_main_top_option_truncates_output(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", io.StringIO("b a b c a b\n"))
    main(["--top", "2"])
    assert capsys.readouterr().out == "b\t3\na\t2\n"


def test_main_min_len_option_filters_short_words(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", io.StringIO("a bb ccc\n"))
    main(["--min-len", "2"])
    assert capsys.readouterr().out == "bb\t1\nccc\t1\n"


def test_main_json_option_emits_word_count_objects(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", io.StringIO("hello hello world\n"))
    main(["--json"])
    out = capsys.readouterr().out
    assert json.loads(out) == [{"word": "hello", "count": 2}, {"word": "world", "count": 1}]


def test_main_json_option_output_ends_with_newline(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", io.StringIO("hello\n"))
    main(["--json"])
    assert capsys.readouterr().out.endswith("\n")


def test_main_json_option_empty_input_prints_empty_array(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", io.StringIO(""))
    main(["--json"])
    assert capsys.readouterr().out == "[]\n"


# ---------------------------------------------------------------------------
# main: exit codes and errors
# ---------------------------------------------------------------------------

def test_main_invalid_top_returns_two_with_stderr(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", io.StringIO("hello\n"))
    rc = main(["--top", "-1"])
    assert rc == 2
    assert capsys.readouterr().err != ""


def test_main_invalid_min_len_returns_two_with_stderr(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", io.StringIO("hello\n"))
    rc = main(["--min-len", "0"])
    assert rc == 2
    assert capsys.readouterr().err != ""


def test_main_missing_file_returns_two_with_stderr(tmp_path, capsys):
    missing = tmp_path / "does_not_exist.txt"
    rc = main([str(missing)])
    assert rc == 2
    assert capsys.readouterr().err != ""


# ---------------------------------------------------------------------------
# python -m wordfreq
# ---------------------------------------------------------------------------

def test_python_m_wordfreq_reads_stdin_and_prints_tsv():
    result = subprocess.run(
        [sys.executable, "-m", "wordfreq"],
        input="hello hello world\n",
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.stdout == "hello\t2\nworld\t1\n"
    assert result.returncode == 0


def test_python_m_wordfreq_missing_file_exits_two(tmp_path):
    missing = tmp_path / "does_not_exist.txt"
    result = subprocess.run(
        [sys.executable, "-m", "wordfreq", str(missing)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 2
