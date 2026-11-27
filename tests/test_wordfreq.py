"""Unit and CLI tests for the wordfreq package."""

from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

from wordfreq.cli import count_words, format_table, main

ROOT = Path(__file__).resolve().parent.parent


def _run_module(*args: str, stdin: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "wordfreq", *args],
        input=stdin,
        capture_output=True,
        encoding="utf-8",
        cwd=ROOT,
        check=False,
    )


def test_count_words_basic_ranking() -> None:
    text = "Apple banana apple, cherry! Banana apple."
    assert count_words(text) == [("apple", 3), ("banana", 2), ("cherry", 1)]


def test_format_table_tsv() -> None:
    assert format_table([("apple", 3), ("banana", 2)]) == "apple\t3\nbanana\t2"


def test_cli_top_and_min_len(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    sample = tmp_path / "sample.txt"
    sample.write_text("to be or not to be that is the question", encoding="utf-8")
    rc = main([str(sample), "--min-len", "3", "--top", "2"])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.strip().splitlines() == ["not\t1", "question\t1"]


# --- count_words -----------------------------------------------------------


def test_count_words_breaks_ties_alphabetically() -> None:
    text = "zebra mango apple mango zebra kiwi"
    assert count_words(text) == [
        ("mango", 2),
        ("zebra", 2),
        ("apple", 1),
        ("kiwi", 1),
    ]


def test_count_words_tie_order_ignores_input_order() -> None:
    assert count_words("b a") == [("a", 1), ("b", 1)]
    assert count_words("a b") == [("a", 1), ("b", 1)]


def test_count_words_lowercases_by_default() -> None:
    assert count_words("Hello HELLO hello") == [("hello", 3)]


def test_count_words_preserves_case_when_ignore_case_is_false() -> None:
    rows = count_words("Apple apple APPLE apple", ignore_case=False)
    assert rows == [("apple", 2), ("APPLE", 1), ("Apple", 1)]


def test_count_words_extracts_only_ascii_alphanumeric_runs() -> None:
    rows = count_words("naïve café, 42 42! foo_bar")
    assert rows == [
        ("42", 2),
        ("bar", 1),
        ("caf", 1),
        ("foo", 1),
        ("na", 1),
        ("ve", 1),
    ]


def test_count_words_min_len_drops_short_words() -> None:
    assert count_words("a an the cat", min_len=3) == [("cat", 1), ("the", 1)]


def test_count_words_top_keeps_highest_ranked_rows() -> None:
    assert count_words("a b b c c c", top=2) == [("c", 3), ("b", 2)]


def test_count_words_top_zero_returns_no_rows() -> None:
    assert count_words("a b", top=0) == []


def test_count_words_empty_text_returns_no_rows() -> None:
    assert count_words("") == []


@pytest.mark.parametrize("min_len", [0, -1])
def test_count_words_rejects_min_len_below_one(min_len: int) -> None:
    with pytest.raises(ValueError, match=r"^min_len must be >= 1$"):
        count_words("a", min_len=min_len)


def test_count_words_rejects_negative_top() -> None:
    with pytest.raises(ValueError, match=r"^top must be >= 0$"):
        count_words("a", top=-1)


# --- format_table ----------------------------------------------------------


def test_format_table_empty_returns_empty_string() -> None:
    assert format_table([]) == ""


def test_format_table_single_row_has_no_newline() -> None:
    assert format_table([("solo", 7)]) == "solo\t7"


# --- CLI: stdin and case handling -----------------------------------------


@pytest.mark.parametrize("argv", [[], ["-"]])
def test_main_reads_stdin_by_default(
    argv: list[str],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO("b a a\n"))
    rc = main(argv)
    assert rc == 0
    assert capsys.readouterr().out == "a\t2\nb\t1\n"


def test_main_decodes_stdin_buffer_as_utf8(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    raw = io.BytesIO(b"alpha beta alpha\n")
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(raw, encoding="utf-8"))
    rc = main([])
    assert rc == 0
    assert capsys.readouterr().out == "alpha\t2\nbeta\t1\n"


def test_main_invalid_utf8_stdin_returns_2(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    raw = io.BytesIO(b"\xff\xfe broken")
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(raw, encoding="utf-8"))
    rc = main([])
    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "not valid UTF-8" in captured.err


def test_main_lowercases_without_case_sensitive_flag(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO("Apple apple\n"))
    rc = main([])
    assert rc == 0
    assert capsys.readouterr().out == "apple\t2\n"


def test_main_case_sensitive_flag_preserves_case(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO("Apple apple\n"))
    rc = main(["--case-sensitive"])
    assert rc == 0
    assert capsys.readouterr().out == "Apple\t1\napple\t1\n"


def test_cli_tie_breaking_orders_words_alphabetically(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    sample = tmp_path / "ties.txt"
    sample.write_text("pear apple pear fig apple", encoding="utf-8")
    rc = main([str(sample)])
    assert rc == 0
    assert capsys.readouterr().out == "apple\t2\npear\t2\nfig\t1\n"


# --- CLI: output framing ---------------------------------------------------


def test_cli_tsv_output_has_single_trailing_newline(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    sample = tmp_path / "sample.txt"
    sample.write_text("b a", encoding="utf-8")
    rc = main([str(sample)])
    out = capsys.readouterr().out
    assert rc == 0
    assert out == "a\t1\nb\t1\n"
    assert not out.endswith("\n\n")


def test_cli_empty_input_writes_nothing(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    sample = tmp_path / "empty.txt"
    sample.write_text("", encoding="utf-8")
    rc = main([str(sample)])
    assert rc == 0
    assert capsys.readouterr().out == ""


def test_cli_top_zero_writes_nothing(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    sample = tmp_path / "sample.txt"
    sample.write_text("alpha beta", encoding="utf-8")
    rc = main([str(sample), "--top", "0"])
    assert rc == 0
    assert capsys.readouterr().out == ""


def test_cli_json_output_is_array_with_single_trailing_newline(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    sample = tmp_path / "sample.txt"
    sample.write_text("b a a", encoding="utf-8")
    rc = main(["--json", str(sample)])
    out = capsys.readouterr().out
    assert rc == 0
    assert out.endswith("\n")
    assert not out.endswith("\n\n")
    assert json.loads(out) == [{"word": "a", "count": 2}, {"word": "b", "count": 1}]


def test_cli_json_empty_input_emits_empty_array(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO(""))
    rc = main(["--json"])
    assert rc == 0
    assert capsys.readouterr().out == "[]\n"


def test_cli_json_honors_case_sensitive_and_top(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO("dog Dog dog\n"))
    rc = main(["--json", "--case-sensitive", "--top", "1"])
    assert rc == 0
    assert json.loads(capsys.readouterr().out) == [{"word": "dog", "count": 2}]


# --- CLI: argument validation and errors -----------------------------------


@pytest.mark.parametrize(
    ("argv", "message"),
    [
        (["--min-len", "0"], "--min-len must be >= 1"),
        (["--top", "-1"], "--top must be >= 0"),
    ],
)
def test_cli_rejects_out_of_range_values(
    argv: list[str],
    message: str,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    sample = tmp_path / "sample.txt"
    sample.write_text("alpha", encoding="utf-8")
    rc = main([*argv, str(sample)])
    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert message in captured.err


@pytest.mark.parametrize(
    "argv",
    [["--top", "many"], ["--no-such-flag"]],
)
def test_cli_rejects_malformed_arguments(
    argv: list[str],
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    sample = tmp_path / "sample.txt"
    sample.write_text("alpha", encoding="utf-8")
    rc = main([*argv, str(sample)])
    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert captured.err.strip() != ""


def test_cli_missing_file_returns_2(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc = main([str(tmp_path / "does-not-exist.txt")])
    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "cannot read" in captured.err


# --- python -m wordfreq ----------------------------------------------------


def test_python_m_wordfreq_reads_stdin_and_writes_tsv() -> None:
    result = _run_module(stdin="b a a\n")
    assert result.returncode == 0
    assert result.stdout == "a\t2\nb\t1\n"
    assert result.stderr == ""


def test_python_m_wordfreq_json_output_has_single_trailing_newline() -> None:
    result = _run_module("--json", stdin="b a a\n")
    assert result.returncode == 0
    assert result.stdout.endswith("\n")
    assert not result.stdout.endswith("\n\n")
    assert json.loads(result.stdout) == [
        {"word": "a", "count": 2},
        {"word": "b", "count": 1},
    ]


def test_python_m_wordfreq_missing_file_exits_2(tmp_path: Path) -> None:
    result = _run_module(str(tmp_path / "missing.txt"))
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr.strip() != ""
