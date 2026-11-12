"""
Copyright (c) Cutleast
"""

import re
import unicodedata
from collections import Counter
from functools import cache
from typing import Optional

import snowballstemmer

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
def _compile_term(
    term: str, inflected: bool, word_boundaries: bool
) -> Optional[re.Pattern[str]]:
    """
    Compiles the search pattern for a term. The patterns are cached, as the glossary
    searches far more distinct terms than the internal cache of `re` can hold.

    Args:
        term (str): The term to compile the pattern for.
        inflected (bool): Whether to consider inflection suffixes.
        word_boundaries (bool):
            Whether the words of the term must start at word boundaries. If False, the
            term is searched anywhere in the text, ignoring inflection suffixes.

    Returns:
        Optional[re.Pattern[str]]: The pattern or None if the term contains no words.
    """

    words: list[str] = get_words(term)
    if not words:
        return None

    if not word_boundaries:
        return re.compile(r"\W*".join(re.escape(word) for word in words), re.IGNORECASE)

    suffix: str = r"\w*" if inflected else r"(?:e?s|'s)?\b"
    pattern: str = (
        r"\b" + (suffix + r"\W+").join(re.escape(word) for word in words) + suffix
    )

    return re.compile(pattern, re.IGNORECASE)


def find_term(
    text: str,
    term: str,
    start: int = 0,
    inflected: bool = True,
    word_boundaries: bool = True,
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
        word_boundaries (bool, optional):
            Whether the words of the term must start at word boundaries. Must be False
            for languages without spaces between words, like Chinese and Japanese.
            Defaults to True.

    Returns:
        Optional[re.Match[str]]: The first match or None if the term is not found.
    """

    pattern: Optional[re.Pattern[str]] = _compile_term(term, inflected, word_boundaries)
    if pattern is None:
        return None

    return pattern.search(plain_text(text), start)


def find_all_terms(
    text: str, term: str, inflected: bool = True, word_boundaries: bool = True
) -> list[re.Match[str]]:
    """
    Searches a term in a text, ignoring case, markup and inflection suffixes.
    Similar to `find_term`, but returns a list of all matches, instead of just the first
    one.

    Args:
        text (str): The text to search.
        term (str): The term to search for.
        inflected (bool, optional):
            Whether to consider inflection suffixes. Defaults to True.
        word_boundaries (bool, optional):
            Whether the words of the term must start at word boundaries.
            Defaults to True.

    Returns:
        list[re.Match[str]]: The matches or an empty list if the term is not found.
    """

    pattern: Optional[re.Pattern[str]] = _compile_term(term, inflected, word_boundaries)
    if pattern is None:
        return []

    return list(pattern.finditer(plain_text(text)))


def fold_word(word: str) -> str:
    """
    Folds a word for a case- and accent-insensitive comparison, so that "Stäbe" becomes
    "stabe" and "Weißlauf" becomes "weisslauf". Diacritics are only removed from Latin
    letters, since marks in other scripts (e.g. "й" or "が") form distinct letters.

    Args:
        word (str): The word to fold.

    Returns:
        str: The folded word.
    """

    decomposed: str = unicodedata.normalize("NFD", word.casefold())

    folded_chars: list[str] = []
    is_latin_base: bool = False
    for char in decomposed:
        if not unicodedata.combining(char):
            is_latin_base = unicodedata.name(char, "").startswith("LATIN ")
            folded_chars.append(char)
        elif not is_latin_base:
            folded_chars.append(char)

    # Recompose to restore non-Latin letters with their marks and to keep Hangul (Korean)
    # syllables intact, which are decomposed into their jamo (Unicode block)
    return unicodedata.normalize("NFC", "".join(folded_chars))


@cache
def stem_word(word: str, algorithm: Optional[str]) -> str:
    """
    Reduces a word to its folded stem, so that "Daedrafürsten" and "Daedrafürst" share
    the same stem. The stems are cached, as the same words are stemmed repeatedly.

    Args:
        word (str): The word to stem.
        algorithm (Optional[str]):
            The name of the Snowball stemmer algorithm or None to only fold the word.

    Returns:
        str: The folded stem of the word.
    """

    if algorithm is None:
        return fold_word(word)

    # A new stemmer per word, as the stemmers are stateful and not thread-safe
    stemmer = snowballstemmer.stemmer(algorithm)

    return fold_word(stemmer.stemWord(word.lower()))


def get_word_stems(
    word: str, algorithm: Optional[str], loose_suffixes: tuple[str, ...]
) -> list[str]:
    """
    Reduces a word to its folded stem and to the folded stems of the word without each
    of the loose suffixes it ends with, so that "Vaerminas" also yields the stem of
    "Vaermina", although the German stemmer keeps the "s" after vowels.

    Args:
        word (str): The word to stem.
        algorithm (Optional[str]):
            The name of the Snowball stemmer algorithm or None to only fold the word.
        loose_suffixes (tuple[str, ...]):
            The suffixes that the stemmer does not remove from every word.

    Returns:
        list[str]: The stem of the word, followed by the stems without loose suffixes.
    """

    stems: list[str] = [stem_word(word, algorithm)]
    lowered_word: str = word.lower()

    for suffix in loose_suffixes:
        base_word: str = lowered_word.removesuffix(suffix)

        if base_word and base_word != lowered_word:
            stems.append(stem_word(base_word, algorithm))

    return stems


def find_term_stems(
    text: str, term: str, algorithm: Optional[str], min_stem_length: int
) -> bool:
    """
    Checks loosely if a term occurs in a text, by searching the stem of each word of the
    term in the stems of the words of the text. This also finds terms that were
    inflected with a changed stem, like "Stab" in "Stäbe", or that became part of
    compounds, like "Seelenstein" in "Riesenseelensteinen", but may find unrelated words
    as well, like "Mann" in "Kaufmann".

    Args:
        text (str): The text to search.
        term (str): The term to search for.
        algorithm (Optional[str]):
            The name of the Snowball stemmer algorithm or None to only fold the words.
        min_stem_length (int):
            The minimum length of a stem to be searched within words. Shorter stems
            must be at the start of a word.

    Returns:
        bool: True if the stems of all words of the term occur in the text.
    """

    text_stems: list[str] = [
        stem_word(word, algorithm) for word in get_words(plain_text(text))
    ]

    for term_word in get_words(term):
        term_stem: str = stem_word(term_word, algorithm)

        found: bool
        if len(term_stem) >= min_stem_length:
            found = any(term_stem in text_stem for text_stem in text_stems)
        else:
            found = any(text_stem.startswith(term_stem) for text_stem in text_stems)

        if not found:
            return False

    return True


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


def get_placeholders(text: str) -> Occurrences:
    """
    Counts the occurrences of each placeholder in a text.

    Args:
        text (str): Text to search.

    Returns:
        Occurrences: Number of occurrences per placeholder.
    """

    return dict(Counter(PLACEHOLDER_PATTERN.findall(text)))
