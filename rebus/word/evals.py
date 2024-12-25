from tqdm.asyncio import tqdm as tqdm_asyncio

from rebus.word.llm import is_visual_word


async def eval_ivw():
    """
    Evaluates the `is_visual_word` function
    """
    test_cases = [
        # Hard edge cases that should be False
        ("between", False),  # requires context/reference points
        ("inside", False),  # spatial relationship, needs context
        ("through", False),  # motion/spatial relationship
        ("almost", False),  # abstract concept of nearness
        ("during", False),  # temporal concept
        ("while", False),  # temporal relationship
        ("because", False),  # causation is abstract
        ("about", False),  # approximation/relation
        ("without", False),  # absence is hard to draw directly
        ("versus", False),  # comparison needs context
        ("either", False),  # choice/alternative is abstract
        ("rather", False),  # preference is abstract
        ("among", False),  # spatial relationship needs context
        ("within", False),  # spatial/temporal relationship
        ("beyond", False),  # relative position needs context
        # Concrete nouns (should be visual)
        ("apple", True),
        ("tree", True),
        ("house", True),
        ("cat", True),
        ("mountain", True),
        ("book", True),
        # Abstract nouns (should not be visual)
        ("love", True),  # easy to visualize -- draw a heart
        ("happiness", True),  # easy to visualize -- draw a smiley face
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
        ("think", True),  # just draw a thought bubble or a thinking statue pose
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
        ("bank", True),  # just draw a building with a dollar sign
        ("spring", True),  # Can be a season, water source, or mechanical device
        ("light", True),  # Can be physical illumination or metaphorical
        # Technical/scientific terms
        ("molecule", True),  # just draw like H20 or something
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

    true_positives = 0
    true_negatives = 0
    false_positives = 0
    false_negatives = 0
    errors = []
    total = len(test_cases)

    # Create tasks for all words
    tasks = [is_visual_word(word) for word, _ in test_cases]

    # Run all tasks concurrently
    results = await tqdm_asyncio.gather(*tasks)

    for (word, expected), result in zip(test_cases, results):
        if result == expected:
            if result:
                true_positives += 1
            else:
                true_negatives += 1
        else:
            if result:  # Got True when should be False
                false_positives += 1
            else:  # Got False when should be True
                false_negatives += 1
            errors.append(f"'{word}': expected {expected}, got {result}")

    total_actual_positive = sum(1 for _, expected in test_cases if expected)
    total_actual_negative = total - total_actual_positive

    accuracy = ((true_positives + true_negatives) / total) * 100
    false_positive_rate = (
        (false_positives / total_actual_negative * 100)
        if total_actual_negative > 0
        else 0
    )
    false_negative_rate = (
        (false_negatives / total_actual_positive * 100)
        if total_actual_positive > 0
        else 0
    )

    print("\nMetrics:")
    print(
        f"Accuracy: {accuracy:.1f}% ({true_positives + true_negatives}/{total} correct)"
    )
    print(
        f"False Positive Rate: {false_positive_rate:.1f}% ({false_positives}/{total_actual_negative} cases)"
    )
    print(
        f"False Negative Rate: {false_negative_rate:.1f}% ({false_negatives}/{total_actual_positive} cases)"
    )

    if errors:
        print("\nErrors found:")
        for error in errors:
            print(f"  {error}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(eval_ivw())
