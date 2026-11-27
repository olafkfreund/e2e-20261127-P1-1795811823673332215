# Acceptance criterion (AC#3): --json output terminated with a final \n.
# main --json emits a JSON array of {word, count} objects terminated by a
# final newline, including '[]\n' for empty input.

import json

import pytest

from wordfreq.cli import main


@pytest.fixture
def empty_input_file(tmp_path):
    path = tmp_path / "empty.txt"
    path.write_text("", encoding="utf-8")
    return path


@pytest.fixture
def sample_input_file(tmp_path):
    path = tmp_path / "sample.txt"
    path.write_text("the cat and the hat and the bat\n", encoding="utf-8")
    return path


def test_main_json_empty_input_outputs_empty_array_with_newline(empty_input_file, capsys):
    main(["--json", str(empty_input_file)])

    captured = capsys.readouterr()

    assert captured.out == "[]\n"


def test_main_json_output_ends_with_final_newline(sample_input_file, capsys):
    main(["--json", str(sample_input_file)])

    captured = capsys.readouterr()

    assert captured.out.endswith("\n")


def test_main_json_output_is_json_array(sample_input_file, capsys):
    main(["--json", str(sample_input_file)])

    parsed = json.loads(capsys.readouterr().out)

    assert isinstance(parsed, list)


def test_main_json_output_items_have_word_and_count_keys(sample_input_file, capsys):
    main(["--json", str(sample_input_file)])

    parsed = json.loads(capsys.readouterr().out)

    assert all(set(item.keys()) == {"word", "count"} for item in parsed)


def test_main_json_output_items_are_objects_with_word_and_count_values(sample_input_file, capsys):
    main(["--json", str(sample_input_file)])

    parsed = json.loads(capsys.readouterr().out)

    assert all(isinstance(item["word"], str) and isinstance(item["count"], int) for item in parsed)
