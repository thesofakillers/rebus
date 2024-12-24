from nltk.corpus import wordnet


def is_physical_noun(substring: str) -> bool:
    """
    Checks if a substring is a physical word
    e.g. "hello" is not a noun
    e.g. "introspection" is a noun, but not physical
    "apple", "tree", "idea", "dog" are physical nouns
    i.e. things that can be represented visually
    """
    raise NotImplementedError


def same_meaning(word_a: str, word_b: str) -> bool:
    """
    Checks if two words have similar meanings using WordNet
    Returns True if the words are semantically related (share meanings,
    or one is a more specific/general version of the other)
    """
    synsets_a = wordnet.synsets(word_a.lower())
    synsets_b = wordnet.synsets(word_b.lower())
    if not synsets_a or not synsets_b:  # either word is not in WordNet
        return False

    for syn_a in synsets_a:
        for syn_b in synsets_b:
            if syn_a == syn_b:
                return True
            if syn_b in syn_a.hypernyms() or syn_b in syn_a.hyponyms():
                return True

    return False


def find_substrings(candidate: str) -> list[str]:
    candidate_chars = [char for char in candidate if char.isalpha()]

    substring_positions = []
    num_chars = len(candidate_chars)

    min_length = 2

    start = 0
    while start < num_chars:
        found_substring = False
        # TODO: this isn't working since we added min_length
        for length in range(max(min_length, start + 1), num_chars - start + 1):
            substring = "".join(candidate_chars[start : start + length])
            if not is_physical_noun(substring):
                continue
            parent_word = get_parent_word(start, start + length, candidate)
            if substring == parent_word:
                continue
            if same_meaning(substring, parent_word):
                continue

            substring_positions.append((substring, (start, start + length)))
            start = start + length
            found_substring = True
            break

        if not found_substring:
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
    candidate = "hello world"
    substrings = find_substrings(candidate)
    print(substrings)
