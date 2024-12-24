import pytest
from rebus import get_parent_word


@pytest.mark.parametrize(
    "candidate, start_idx, end_idx, expected",
    [
        # Basic single word tests
        ("hello", 0, 2, "hello"),  # Start of word
        ("hello", 3, 5, "hello"),  # End of word
        ("hello", 1, 4, "hello"),  # Middle of word
        # Multiple word tests
        ("hello world", 0, 2, "hello"),  # Start of first word
        ("hello world", 3, 5, "hello"),  # End of first word
        ("hello world", 6, 8, "world"),  # Middle of second word
        # Tests with non-alphabetic characters
        ("he!!o", 0, 2, "he!!o"),  # Word with symbols
        ("ab-cd", 0, 2, "ab-cd"),  # Hyphenated word
        ("a.b.c", 0, 2, "a.b.c"),  # Word with periods
        # Spanning multiple words (should return empty string)
        ("hello world", 3, 8, ""),  # Span across two words
        ("one two three", 2, 6, ""),  # Span across middle words
        ("a b c", 0, 3, ""),  # Span across multiple short words
        # Edge cases
        ("", 0, 0, ""),  # Empty string
        ("word", 0, 0, "word"),  # Zero-length substring
        ("word", 0, 4, "word"),  # Exact word length
        ("word", 3, 4, "word"),  # Single char at end
        # Complex cases with multiple spaces
        ("  hello  world  ", 0, 2, "hello"),  # Extra spaces
        ("one   two", 0, 3, "one"),  # Multiple spaces between words
        # Cases with numbers and special characters
        ("hello123 world456", 0, 5, "hello123"),  # Words with numbers
        ("hello!! world##", 0, 5, "hello!!"),  # Words with symbols
        # Boundary tests
        ("word", 0, 1, "word"),  # First character
        ("word", 3, 4, "word"),  # Last character
        ("a b", 0, 1, "a"),  # Single letter words
        # Invalid indices (should return empty string)
        ("word", 5, 6, ""),  # Start index beyond string
        ("word", -1, 2, ""),  # Negative index
        ("word", 2, 1, ""),  # End before start
        ("word", 4, 8, ""),  # End index beyond string
    ],
)
def test_get_parent_word(candidate, start_idx, end_idx, expected):
    assert get_parent_word(start_idx, end_idx, candidate) == expected


# Additional specific test cases that need more detailed verification
def test_get_parent_word_specific_cases():
    # Test with mixed case
    assert get_parent_word(0, 2, "HeLLo WoRLD") == "HeLLo"

    # Test with unicode characters
    assert get_parent_word(0, 2, "café world") == "café"

    # Test with tab separators
    assert get_parent_word(0, 2, "hello\tworld") == "hello"

    # Test with newline separators
    assert get_parent_word(0, 2, "hello\nworld") == "hello"

