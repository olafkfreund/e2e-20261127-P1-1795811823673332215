# Criterion (AC#1): count_words extracts tokens, lowercases by default, preserves
# case, filters by min_len, and sorts by (-count, word).
#
# Target: wordfreq.cli.count_words

from wordfreq.cli import count_words


def test_count_words_extracts_alnum_tokens_splitting_on_punctuation():
    result = count_words("hello, world! 42 abc_def")

    assert set(dict(result).keys()) == {"hello", "world", "42", "abc", "def"}


def test_count_words_lowercases_by_default_merges_case_variants():
    result = count_words("Hello HELLO hello")

    assert dict(result) == {"hello": 3}


def test_count_words_ignore_case_false_preserves_case():
    result = count_words("Hello HELLO hello", ignore_case=False)

    assert dict(result) == {"Hello": 1, "HELLO": 1, "hello": 1}


def test_count_words_min_len_filters_short_tokens():
    result = count_words("a bb ccc", min_len=2)

    assert set(dict(result).keys()) == {"bb", "ccc"}


def test_count_words_sorts_by_descending_count():
    result = count_words("b a b c a b")

    assert list(result) == [("b", 3), ("a", 2), ("c", 1)]


def test_count_words_ties_sorted_alphabetically_by_word():
    result = count_words("zeta alpha")

    assert list(result) == [("alpha", 1), ("zeta", 1)]
