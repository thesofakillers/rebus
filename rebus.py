from nltk.corpus import wordnet
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
import anthropic
import re
from tqdm.asyncio import tqdm as tqdm_asyncio
import asyncio


visual_word_cache = {}

ANTHROPIC_TIMEOUT_EXCEPTIONS = (
    anthropic.RateLimitError,
    anthropic.APIConnectionError,
    anthropic.APITimeoutError,
    anthropic.InternalServerError,
)

client = anthropic.AsyncAnthropic(max_retries=0)

IS_WORD_PROMPT = """Is the word "{word}" something that can be straightforwardly represented in a drawing?

Rules for "drawable" words:
- Must be recognizable without text or context
- Should be interpretable by most viewers
- Should have a consistent visual representation

Examples by category:

Physical Objects; these are usually "drawable":
- "apple" -> clear round fruit shape -> <answer>yes</answer>
- "book" -> rectangular object with pages -> <answer>yes</answer>
- "breeze" -> just draw some flowy lines -> <answer>yes</answer>

Actions; these are sometimes "drawable", usually correlated with how common and physical:
- "running" -> figure in motion -> <answer>yes</answer>
- "sleeping" -> figure lying with 'Z's -> <answer>yes</answer>

Abstract/Concepts; these are usually not drawable, unless they have a known symbol:
- "hello" -> not visually representable -> <answer>no</answer>
- "freedom" -> too abstract to draw directly -> <answer>no</answer>
- "peace" -> universally recognized symbol -> <answer>yes</answer>

Properties; these are a mixed bag, some are "drawable", some are not:
- "red" -> color requires context -> <answer>no</answer>
- "big" -> relative concept, needs reference -> <answer>no</answer>
- "triangular" -> clear shape, draw a triangle can be drawn -> <answer>yes</answer>
- "spherical" -> clear shape, draw a circle -> <answer>yes</answer>
- "spiky" -> clear shape, draw a spiky object -> <answer>yes</answer>
- "angular" -> clear description, draw an angular object -> <answer>yes</answer>
- "slouched" -> just draw a person slouching -> <answer>yes</answer>

Heuristic 1: Could a person draw this word AND have another person recognize what was drawn?
Heuristic 2: Don't overthink it! If you can't imagine a simple drawing, it's probably not a "drawable" word.
Likewise, if you can easily imagine a simple drawing, even if its not a 100% match with the word, then it's likely a "drawable" word.
Heuristic 4: Somethings are hard to visualize without also visualizing other things. You should lean towards "no" for these.
Heuristic 3: If unsure, lean towards "no".

To re-iterate: Can the word "{word}" be unambiguously represented in a simple drawing that most people would recognize without additional context?

Provide brief reasoning, then your answer in XML tags: <answer>yes</answer> or <answer>no</answer>"""


@retry(
    retry=retry_if_exception_type(ANTHROPIC_TIMEOUT_EXCEPTIONS),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
)
async def _query_model(word: str) -> bool:
    """Helper function to query Claude with retries."""
    response = await client.messages.create(
        model="claude-3-5-sonnet-20241022",
        messages=[{"role": "user", "content": IS_WORD_PROMPT.format(word=word)}],
        temperature=0,
        max_tokens=256,
    )
    response_text = response.content[0].text

    # Extract answer using regex
    if match := re.search(r"<answer>?(yes|no)?</answer>", response_text.lower()):
        return match.group(1) == "yes"
    return False


async def is_visual_word(substring: str) -> bool:
    """
    Checks if a substring is a "visual" (noun/verb/adjective) word
    Visual words are those that can be represented visually straightforwardly
    negative examples: "hello" "introspection"
    positive examples: "apple", "idea", "upright", "running"
    """

    substring = substring.strip().lower()

    # Check cache first
    if substring in visual_word_cache:
        return visual_word_cache[substring]

    # Check if it's a valid word using WordNet
    if not wordnet.synsets(substring):
        visual_word_cache[substring] = False
        return False

    result = await _query_model(substring)
    visual_word_cache[substring] = result
    return result


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


async def find_substrings(candidate: str) -> list[str]:
    candidate_chars = [char for char in candidate if char.isalpha()]

    substring_positions = []
    num_chars = len(candidate_chars)

    min_length = 2

    start = 0
    while start < num_chars:
        found_substring = False
        remaining = num_chars - start
        for length in range(min_length, remaining + 1):
            substring = "".join(candidate_chars[start : start + length])
            parent_word = get_parent_word(start, start + length, candidate)
            if substring == parent_word:
                continue
            if same_meaning(substring, parent_word):
                continue
            if not await is_visual_word(substring):
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


async def eval_ivw():
    """
    Evaluates the `is_visual_word` function
    """
    test_cases = [
        # Concrete nouns (should be visual)
        ("apple", True),
        ("tree", True),
        ("house", True),
        ("cat", True),
        ("mountain", True),
        ("book", True),
        # Abstract nouns (should not be visual)
        ("love", True),  # easy to visualize -- draw a heart
        ("happiness", True), # easy to visualize -- draw a smiley face
        ("theory", False),
        ("wisdom", False),
        ("freedom", False),
        # Visual verbs (actions that can be seen)
        ("run", True),
        ("jump", True),
        ("throw", True),
        ("dance", True),
        ("climb", True),
        # Non-visual verbs
        ("think", False),  # kinda hard to draw, lean no
        ("believe", False),
        ("understand", False),
        ("hope", False),
        # Visual adjectives (describing physical appearance)
        ("red", False),  # hard to visualize
        ("tall", False),  # need context to visualize
        ("round", True),
        ("square", True),
        ("bright", False),  # hard to visualize
        ("upright", True),
        # Non-visual adjectives
        ("happy", True),  # easy to visualize -- draw a smiley face
        ("brave", False),
        ("wise", False),
        ("logical", False),
        # Compound words
        ("lighthouse", True),
        ("rainbow", True),
        ("daydream", False),  # kinda hard to draw, lean no
        # Edge cases
        ("", False),  # Empty string
        ("xyz123", False),  # Non-existent word
        ("the", False),  # Articles
        ("and", False),  # Conjunctions
        # Words with multiple meanings (should return True if any meaning is visual)
        ("bank", False),  # kinda hard to draw, lean no
        ("spring", True),  # Can be a season, water source, or mechanical device
        ("light", True),  # Can be physical illumination or metaphorical
        # Technical/scientific terms
        ("molecule", False),  # hard to visualize
        ("atom", True),  # just draw the lil orbital thing
        ("gravity", False),  # hard to visualize, lean no
        # Nature-related
        ("cloud", True),
        ("wind", True),
        ("thunder", True),
        ("lightning", True),
        ("rain", True),
        # Man-made objects
        ("computer", True),
        ("phone", True),
        ("chair", True),
        ("table", True),
        # Body parts
        ("hand", True),
        ("eye", True),
        ("brain", True),
        ("heart", True),
    ]

    errors = []
    total = len(test_cases)

    # Create tasks for all words
    tasks = [is_visual_word(word) for word, _ in test_cases]

    # Run all tasks concurrently
    results = await tqdm_asyncio.gather(*tasks)

    # Compare results with expected values
    correct = sum(
        1 for (_, expected), result in zip(test_cases, results) if result == expected
    )

    # Collect errors
    errors = [
        f"'{word}': expected {expected}, got {result}"
        for (word, expected), result in zip(test_cases, results)
        if result != expected
    ]

    accuracy = (correct / total) * 100

    if errors:
        print("\nErrors found:")
        for error in errors:
            print(f"  {error}")

    print(f"\nAccuracy: {accuracy:.1f}% ({correct}/{total} correct)")


if __name__ == "__main__":
    substrings = asyncio.run(find_substrings("carpenter ants marching"))

    print(substrings)
