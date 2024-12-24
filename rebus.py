from nltk.corpus import wordnet



def is_word(substring: str) -> bool:
    """
    Checks if the given substring is a valid word
    """
    raise NotImplementedError("is_word not implemented yet")


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


def find_substrings(candidate: list[str]) -> list[str]:
    candidate_chars = [char for char in candidate if char.isalpha()]

    substring_positions = []
    num_chars = len(candidate_chars)

    start = 0
    while start < num_chars:
        found_substring = False
        for length in range(start + 1, num_chars - start + 1):
            substring = candidate_chars[start : start + length]
            if not is_word(substring):
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
