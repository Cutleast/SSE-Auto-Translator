"""
Copyright (c) Cutleast
"""

import re
from collections import Counter
from functools import cache
from typing import Optional

WORD_PATTERN: re.Pattern[str] = re.compile(r"[^\W\d_]+")
"""Pattern for the natural-language words of a text."""

MARKUP_PATTERN: re.Pattern[str] = re.compile(r"<[^>]*>|\[[^\]]*\]|\{[^}]*\}")
"""Pattern for markup and placeholders that are not considered natural-language text."""

NON_TEXT_PATTERN: re.Pattern[str] = re.compile(r"[^\w\s'’-]|[\d_]")
"""Pattern for numbers and special characters that are not part of words."""

PLACEHOLDER_PATTERN: re.Pattern[str] = re.compile(
    # Tags like <Alias=Player>, <Global=X>, <mag>, <dur> or HTML markup in books.
    r"<[^<>\n]+>"
    r"|\[pagebreak\]"
    # Format specifiers in interface strings like {0} or {}.
    r"|\{\d*\}"
    r"|%\d*(?:\.\d+)?[sdif]",
    re.IGNORECASE,
)
"""Pattern matching a single placeholder."""

SENTENCE_END_CHARACTERS: str = ".!?:…"
"""Characters ending a sentence, so that the following word starts a new one."""

LINE_BREAK_CHARACTERS: str = "\r\n"
"""Characters ending a line, so that the following word starts a new one."""

OPENING_CHARACTERS: str = "\"'“”„‘’‚«»([{-–—*•"
"""Characters that may precede the first word of a sentence, like quotes or bullets."""

type Occurrences = dict[str, int]
"""A dictionary of terms and occurence count."""


def plain_text(text: str) -> str:
    """
    Cleans a text of all markup and placeholders.

    Args:
        text (str): The text to clean.

    Returns:
        str: The plain text.
    """

    return MARKUP_PATTERN.sub(" ", text)


def remove_non_text(text: str) -> str:
    """
    Removes all markup, numbers and special characters from a text, except for
    apostrophes and hyphens within words, and collapses the remaining whitespace.

    Args:
        text (str): The text to clean.

    Returns:
        str: The text consisting only of words.
    """

    return " ".join(NON_TEXT_PATTERN.sub(" ", plain_text(text)).split()).strip(" '’-")


def normalize_word(word: str) -> str:
    """
    Normalizes a word, so that English plurals like "Spheres" or "Boxes" are the same as
    their singular.

    Args:
        word (str): The word to normalize.

    Returns:
        str: The normalized word.
    """

    return word.lower().rstrip("s").removesuffix("e")


def get_words(text: str) -> list[str]:
    """
    Args:
        text (str): The text to split.

    Returns:
        list[str]: A list of all natural-language words from the text.
    """

    return WORD_PATTERN.findall(text)


@cache
def _compile_term(term: str, inflected: bool) -> Optional[re.Pattern[str]]:
    """
    Compiles the search pattern for a term. The patterns are cached, as the glossary
    searches far more distinct terms than the internal cache of `re` can hold.

    Args:
        term (str): The term to compile the pattern for.
        inflected (bool): Whether to consider inflection suffixes.

    Returns:
        Optional[re.Pattern[str]]: The pattern or None if the term contains no words.
    """

    words: list[str] = get_words(term)
    if not words:
        return None

    suffix: str = r"\w*" if inflected else r"(?:e?s|'s)?\b"
    pattern: str = (
        r"\b" + (suffix + r"\W+").join(re.escape(word) for word in words) + suffix
    )

    return re.compile(pattern, re.IGNORECASE)


def find_term(
    text: str, term: str, start: int = 0, inflected: bool = True
) -> Optional[re.Match[str]]:
    """
    Searches a term in a text, ignoring case, markup and inflection suffixes. Each word
    of the term must start at a word boundary and may be followed by a suffix, so that
    "Dark Brotherhood" matches "Dunklen Bruderschaft" for the term "Dunkle Bruderschaft"
    and "Weißlauf" matches "Weißlaufs".

    Args:
        text (str): The text to search.
        term (str): The term to search for.
        start (int, optional): The position to start searching from. Defaults to 0.
        inflected (bool, optional):
            Whether to consider inflection suffixes. Defaults to True.

    Returns:
        Optional[re.Match[str]]: The first match or None if the term is not found.
    """

    pattern: Optional[re.Pattern[str]] = _compile_term(term, inflected)
    if pattern is None:
        return None

    return pattern.search(plain_text(text), start)


def find_all_terms(text: str, term: str, inflected: bool = True) -> list[re.Match[str]]:
    """
    Searches a term in a text, ignoring case, markup and inflection suffixes.
    Similar to `find_term`, but returns a list of all matches, instead of just the first
    one.

    Args:
        text (str): The text to search.
        term (str): The term to search for.
        inflected (bool, optional):
            Whether to consider inflection suffixes. Defaults to True.

    Returns:
        list[re.Match[str]]: The matches or an empty list if the term is not found.
    """

    pattern: Optional[re.Pattern[str]] = _compile_term(term, inflected)
    if pattern is None:
        return []

    return list(pattern.finditer(plain_text(text)))


def is_at_sentence_start(text: str, match: re.Match[str]) -> bool:
    """
    Checks if a match is at the start of a sentence. This is the case if it is only
    preceded by whitespace and opening characters, like quotes, brackets or bullets,
    which follow the start of the text, a line break or a sentence-ending punctuation.

    Args:
        text (str): The text that was searched for the match.
        match (re.Match[str]): The match to check.

    Returns:
        bool: True if the match is at the start of a sentence, False otherwise.
    """

    for character in reversed(text[: match.start()]):
        if character in LINE_BREAK_CHARACTERS:
            return True

        if character.isspace() or character in OPENING_CHARACTERS:
            continue

        return character in SENTENCE_END_CHARACTERS

    return True


def count_words(text: str, to_count: list[str]) -> Occurrences:
    """
    Counts the occurences of terms in a text.

    Args:
        text (str): The text.
        to_count (list[str]): The terms to count.

    Returns:
        Occurences:
            The occurence count per term. Omitted terms did not occur in the text.
    """

    return dict(Counter(w for w in get_words(text) if w in to_count))


def get_placeholders(text: str) -> Occurrences:
    """
    Counts the occurrences of each placeholder in a text.

    Args:
        text (str): Text to search.

    Returns:
        Occurrences: Number of occurrences per placeholder.
    """

    return dict(Counter(PLACEHOLDER_PATTERN.findall(text)))
