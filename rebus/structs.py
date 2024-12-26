from dataclasses import dataclass


@dataclass
class RebusSubstring:
    text: str  # the substring itself
    start: int  # start index in the rebus phrase (without spaces)
    stop: int  # stop index in the rebus phrase (without spaces)


@dataclass
class RebusPuzzle:
    phrase: str
    substrings: list[RebusSubstring]
