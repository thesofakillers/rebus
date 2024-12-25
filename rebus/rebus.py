import asyncio

from rebus.word.wordnet import same_meaning
from rebus.word.llm import is_visual_word


async def find_substrings(candidate: str) -> list[str]:
    candidate_chars = [char for char in candidate if char.isalpha()]

    substring_positions = []
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

            if substring == parent_word:
                continue
            if same_meaning(substring, parent_word):
                continue

            is_valid = await is_visual_word(substring)
            if is_valid:
                last_found_valid = (substring, (start, start + length))
            elif last_found_valid is not None:
                # If we found an invalid substring and we have a previous valid one,
                # we can stop looking for longer substrings
                break

        if last_found_valid:
            substring_positions.append(last_found_valid)
            start = last_found_valid[1][1]  # Move start to after the found substring
        else:
            start += 1  # Only advance by 1 if no substring was found

    return substring_positions


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
    # substrings = asyncio.run(find_substrings("carpenter ants marching"))
    substrings = asyncio.run(find_substrings("garden flowers blooming"))
    print(substrings)
