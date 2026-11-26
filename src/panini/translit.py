"""IAST ↔ SLP1 transliteration.

SLP1 spells every Sanskrit phoneme with a single ASCII character, which makes
it convenient as the engine's internal encoding. IAST is what the user sees.
SLP1 ``~`` (nasality) is shown in IAST as a tilde over the vowel (ã). Other
characters with no mapping (accent marks, spaces, ``+``) pass through unchanged.
"""

import re
import unicodedata

_PAIRS: tuple[tuple[str, str], ...] = (
    # vowels
    ("a", "a"),
    ("ā", "A"),
    ("i", "i"),
    ("ī", "I"),
    ("u", "u"),
    ("ū", "U"),
    ("ṛ", "f"),
    ("ṝ", "F"),
    ("ḷ", "x"),
    ("ḹ", "X"),
    ("e", "e"),
    ("ai", "E"),
    ("o", "o"),
    ("au", "O"),
    ("ṃ", "M"),
    ("ḥ", "H"),
    # stops and nasals
    ("k", "k"),
    ("kh", "K"),
    ("g", "g"),
    ("gh", "G"),
    ("ṅ", "N"),
    ("c", "c"),
    ("ch", "C"),
    ("j", "j"),
    ("jh", "J"),
    ("ñ", "Y"),
    ("ṭ", "w"),
    ("ṭh", "W"),
    ("ḍ", "q"),
    ("ḍh", "Q"),
    ("ṇ", "R"),
    ("t", "t"),
    ("th", "T"),
    ("d", "d"),
    ("dh", "D"),
    ("n", "n"),
    ("p", "p"),
    ("ph", "P"),
    ("b", "b"),
    ("bh", "B"),
    ("m", "m"),
    # semivowels, sibilants, h
    ("y", "y"),
    ("r", "r"),
    ("l", "l"),
    ("v", "v"),
    ("ś", "S"),
    ("ṣ", "z"),
    ("s", "s"),
    ("h", "h"),
)

_IAST_TO_SLP1 = {iast: slp for iast, slp in _PAIRS}
_SLP1_TO_IAST = {slp: iast for iast, slp in _PAIRS}
# Longest IAST keys first, so "kh" wins over "k" and "ai" over "a".
_IAST_KEYS = sorted(_IAST_TO_SLP1, key=len, reverse=True)


NASAL = "\u0303"  # combining tilde: a nasal vowel (anunāsika), written ~ in SLP1
# A vowel in NFD: a i u e o (optionally with macron), or ṛ ṝ ḷ ḹ (r/l + dot below), then a tilde.
_NASAL_VOWEL = re.compile("([aiueoAIUEO]\u0304?|[rlRL]\u0323\u0304?)\u0303")


def iast_to_slp1(text: str) -> str:
    # A tilde over a vowel is nasality; over n it is part of ñ, so only vowels count.
    nfd = _NASAL_VOWEL.sub(r"\1~", unicodedata.normalize("NFD", text))
    text = unicodedata.normalize("NFC", nfd)
    out: list[str] = []
    i = 0
    while i < len(text):
        for key in _IAST_KEYS:
            if text.startswith(key, i):
                out.append(_IAST_TO_SLP1[key])
                i += len(key)
                break
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def slp1_to_iast(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    out = "".join(NASAL if c == "~" else _SLP1_TO_IAST.get(c, c) for c in text)
    return unicodedata.normalize("NFC", out)
