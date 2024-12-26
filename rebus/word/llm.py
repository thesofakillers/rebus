from nltk.corpus import wordnet
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
import anthropic
import re

from rebus.word.prompts import IS_VISUAL_WORD_PROMPT


ANTHROPIC_TIMEOUT_EXCEPTIONS = (
    anthropic.RateLimitError,
    anthropic.APIConnectionError,
    anthropic.APITimeoutError,
    anthropic.InternalServerError,
)

client = anthropic.AsyncAnthropic(max_retries=0)


@retry(
    retry=retry_if_exception_type(ANTHROPIC_TIMEOUT_EXCEPTIONS),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
)
async def _ask_if_visual_word(word: str) -> bool:
    """Ask claude whether a word is a 'visual' word according to our spec"""
    response = await client.messages.create(
        model="claude-3-5-sonnet-20241022",
        messages=[{"role": "user", "content": IS_VISUAL_WORD_PROMPT.format(word=word)}],
        temperature=0,
        max_tokens=256,
    )
    response_text = response.content[0].text
    # print(response_text)

    # Extract answer using regex
    if match := re.search(r"<answer>?(yes|no)?</answer>", response_text.lower()):
        return match.group(1) == "yes"
    return False


visual_word_cache = {}


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

    result = await _ask_if_visual_word(substring)
    visual_word_cache[substring] = result
    return result
if __name__ == "__main__":
    import asyncio
    print("is_visual_word(gar)", asyncio.run(is_visual_word("gar")))
    print("is_visual_word(den)", asyncio.run(is_visual_word("den")))
