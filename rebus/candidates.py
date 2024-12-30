import re
import json
from rebus.word.wordnet import is_word
from tqdm.auto import tqdm


def build_visual_genome_phrases(visual_genome_relationships: list[dict]) -> list[str]:
    phrases = set()

    for item in tqdm(visual_genome_relationships):
        for rel in item["relationships"]:
            # Get the main components
            subject = re.sub(r"[^a-z ]", "", rel["subject"].get("name", ""))
            predicate = re.sub(r"[^a-z ]", "", rel["predicate"])
            object_name = re.sub(
                r"[^a-z ]",
                "",
                (
                    rel["object"].get("names", [None])[0]
                    if rel["object"].get("names")
                    else rel["object"].get("name", "")
                ),
            )
            if not all([is_word(word) for word in [subject, predicate, object_name]]):
                continue

            # Form a simple sentence
            phrase = f"{subject} {predicate} {object_name}".strip().lower()

            phrases.add(phrase)

    return list(phrases)


# # Load the data
print("Loading data...")
with open("/users/thesofakillers/Downloads/relationships.json") as f:
    data = json.load(f)

# Get phrases
print("Building phrases...")
phrases = build_visual_genome_phrases(data)

print(f"built {len(phrases)} phrases")
print("preview:")
print(phrases[:100])
