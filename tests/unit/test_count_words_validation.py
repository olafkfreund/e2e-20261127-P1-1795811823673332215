# AC#1: count_words raises ValueError('min_len must be >= 1') when min_len < 1,
# raises ValueError('top must be >= 0') when top < 0, and honors top truncation
# including top=0.

import pytest

from wordfreq.cli import count_words

SAMPLE_TEXT = "the cat the dog the bird cat fish"


@pytest.mark.parametrize(
    "min_len",
    [0, -1],
    ids=["min_len_zero", "min_len_negative"],
)
def test_count_words_min_len_below_one_raises_value_error(min_len):
    with pytest.raises(ValueError) as exc_info:
        count_words(SAMPLE_TEXT, min_len=min_len, top=10)
    assert str(exc_info.value) == "min_len must be >= 1"


@pytest.mark.parametrize(
    "top",
    [-1, -10],
    ids=["top_minus_one", "top_minus_ten"],
)
def test_count_words_top_negative_raises_value_error(top):
    with pytest.raises(ValueError) as exc_info:
        count_words(SAMPLE_TEXT, min_len=1, top=top)
    assert str(exc_info.value) == "top must be >= 0"


def test_count_words_top_zero_returns_empty_result():
    result = count_words(SAMPLE_TEXT, min_len=1, top=0)
    assert len(result) == 0


def test_count_words_top_two_truncates_result_to_two_entries():
    result = count_words(SAMPLE_TEXT, min_len=1, top=2)
    assert len(result) == 2
