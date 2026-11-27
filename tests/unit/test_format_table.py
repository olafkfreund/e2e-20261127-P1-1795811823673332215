# Criterion (AC#2): format_table formats rows as word\tcount lines separated by \n
# and returns '' for empty input.
#
# Behaviour under test:
#   - multiple rows are joined with "\n" in input order
#   - each row renders as "word\tcount"
#   - no trailing newline is appended after the last row
#   - empty input returns the empty string ''

from wordfreq.cli import format_table


def test_format_table_multiple_rows_joined_with_newline_separator():
    rows = [("apple", 3), ("banana", 1)]

    result = format_table(rows)

    assert result == "apple\t3\nbanana\t1"


def test_format_table_single_row_has_no_trailing_newline():
    rows = [("apple", 3)]

    result = format_table(rows)

    assert result == "apple\t3"


def test_format_table_empty_input_returns_empty_string():
    result = format_table([])

    assert result == ""
