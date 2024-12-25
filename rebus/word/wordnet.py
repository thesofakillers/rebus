from nltk.corpus import wordnet

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
