import asyncio
import logging

from rebus.word.wordnet import same_meaning, is_word
from rebus.word.llm import is_visual_word
from rebus.structs import RebusSubstring

logging.basicConfig(
    level=logging.WARNING, format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


async def is_valid_substring(substring: str, parent_word: str) -> bool:
    """Check if a substring is valid for rebus purposes."""
    if not is_word(substring):
        logger.debug("%r is not a word", substring)
        return False

    if substring == parent_word or same_meaning(substring, parent_word):
        logger.debug("%r has same meaning as parent word %r", substring, parent_word)
        return False

    if not await is_visual_word(substring):
        logger.debug("%r is not a visual word", substring)
        return False

    return True


async def find_substrings(candidate: str) -> list[RebusSubstring]:
    """Find valid rebus substrings within a candidate string."""
    candidate_chars = [char for char in candidate if char.isalpha()]

    rebus_substrings = []
    num_chars = len(candidate_chars)

    min_length = 2

    start = 0
    while start < num_chars:
        last_found_valid = None
        remaining = num_chars - start

        # Try increasingly longer substrings until we find an invalid one
        for length in range(min_length, remaining + 1):
            substring = "".join(candidate_chars[start : start + length])
            parent_word = get_parent_word(start, start + length, candidate)

            logger.debug("Checking substring: %r", substring)
            if await is_valid_substring(substring, parent_word):
                logger.debug("Found valid substring: %r; checking next char", substring)
                last_found_valid = RebusSubstring(
                    text=substring, start=start, stop=start + length
                )
            elif last_found_valid:
                logger.debug("Found invalid substring; jumping start")
                break  # Stop if we hit an invalid substring after finding a valid one
            else:
                continue

        if last_found_valid:
            rebus_substrings.append(last_found_valid)
            start = last_found_valid.stop  # Move start to after the found substring
        else:
            start += 1  # Only advance by 1 if no substring was found

    return rebus_substrings


def get_parent_word(start_idx: int, end_idx: int, candidate: str) -> str:
    """
    Gets the parent word that contains the substring at the given indices.
    Returns empty string if the substring spans multiple words.

    Example:
        candidate = "hello world"
        alpha_only = "helloworld"
        - If start_idx=3, end_idx=5 (pointing to "lo" in alpha_only), Returns "hello"
          since that's the original word containing those letters
        - If start_idx=3, end_idx=8 (pointing to "lowor" in alpha_only), Returns ""
          since the substring spans multiple words
    """
    words = candidate.split()
    current_idx = 0

    for word in words:
        word_length = len(word)
        if current_idx <= start_idx <= end_idx <= current_idx + word_length:
            return word
        current_idx += word_length
        continue  # to the next word

    return ""  # Substring spans multiple words


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # substrings = asyncio.run(find_substrings("carpenter ants marching"))
    substrings = asyncio.run(find_substrings("garden flower blooming"))
    print("Found substrings: %s", substrings)
