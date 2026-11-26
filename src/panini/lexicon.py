"""The lexicon: the bhvādi section of the dhātupāṭha, upadeśas in SLP1 as in Vidyut's list."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from importlib.resources import files
from typing import Literal

from panini.model import Term, TermKind
from panini.translit import slp1_to_iast

# Initial markers (it-sounds before the root proper): ḍu, ṭu, ñi.
_INITIAL_MARKERS = ("qu", "wu", "Yi")
# Nasal that agrees with a consonant's place of articulation (SLP1): ṃ before a sibilant or h.
_NASAL_FOR = {**dict.fromkeys("kKgGN", "N"), **dict.fromkeys("cCjJY", "Y"), **dict.fromkeys("wWqQR", "R"),
              **dict.fromkeys("pPbBm", "m"), **dict.fromkeys("Szsh", "M")}


def citation_name(upadesha_slp1: str) -> str:
    """The root as it is usually quoted (IAST), e.g. ``ga\\mx~`` -> gam, ``kradi~`` -> krand.

    Only a display label, so it uses plain string logic rather than the it-rules.
    """
    sounds = [(s.char, s.nasal) for s in Term.from_upadesha(TermKind.ROOT, upadesha_slp1).sounds]
    for marker in _INITIAL_MARKERS:  # ḍu, ṭu, ñi
        if "".join(c for c, _ in sounds[:2]) == marker and len(sounds) > 2:
            sounds = sounds[2:]
            break
    if len(sounds) > 1 and sounds[0][1]:  # an initial nasal vowel (o~, u~) is a marker too
        sounds = sounds[1:]
    nasal_vowels = [k for k, (_, nasal) in enumerate(sounds) if nasal]
    # A final i~ marks the root idit; i~r (dṛś, df\Si~r) is the marker ir, which adds no nasal.
    idit = bool(nasal_vowels) and nasal_vowels[-1] == len(sounds) - 1 and sounds[-1][0] == "i"
    if nasal_vowels:  # the last nasal vowel and whatever follows it are markers
        sounds = sounds[: nasal_vowels[-1]]
    elif len(sounds) > 1 and sounds[-1][0] in "NY":  # ṅ, ñ marker
        sounds = sounds[:-1]
    text = "".join(c for c, _ in sounds)
    if text.startswith("z"):
        text = "s" + text[1:]
        text = text[:1] + {"w": "t", "W": "T", "R": "n"}.get(text[1:2], text[1:2]) + text[2:]
    elif text.startswith("R"):
        text = "n" + text[1:]
    if idit and len(text) > 1 and text[-2] not in "nNYRmM":  # kradi~ -> krand
        text = text[:-1] + _NASAL_FOR.get(text[-1], "n") + text[-1]
    # A taught n before a consonant is quoted as the nasal of that consonant's place (sañj, tump,
    # śranbh -> śrambh), or as ṃ before a sibilant or h (daṃś); before a dental it stays n.
    text = "".join(_NASAL_FOR.get(nxt, c) if c == "n" else c for c, nxt in zip(text, text[1:] + " "))
    return slp1_to_iast(text)


@dataclass(frozen=True)
class Root:
    code: str  # position in the dhātupāṭha, e.g. "01.0381"
    upadesha: str  # SLP1, with ~ for nasal markers and \ ^ for accents
    meaning: str
    meaning_kind: Literal["english", "traditional"]

    @property
    def key(self) -> str:
        return self.code

    @property
    def gana(self) -> str:
        return "bhvādi"

    @property
    def name(self) -> str:
        return citation_name(self.upadesha)

    @property
    def upadesha_iast(self) -> str:
        return slp1_to_iast(self.upadesha.replace("\\", "").replace("^", ""))

    @property
    def pada(self) -> Literal["P", "A", "U"]:
        """Which voices the markers allow: anudātta vowel or ṅ gives middle (1.3.12); svarita
        vowel or ñ gives both (1.3.72); otherwise active (1.3.78)."""
        term = Term.from_upadesha(TermKind.ROOT, self.upadesha)
        if "anudattet" in term.tags or term.upadesha.endswith("N"):
            return "A"
        if "svaritet" in term.tags or term.upadesha.endswith("Y"):
            return "U"
        return "P"


# English glosses for the roots the explorer features; the rest keep the list's own artha.
ENGLISH = {
    "01.0001": "to be, become",
    "01.0381": "to speak clearly, recite",
    "01.1137": "to go",
    "01.0919": "to remember",
    "01.0002": "to grow, prosper",
    "01.1049": "to lead",
    "01.1151": "to cook",
}

# The slice-1 seven, then the 7.3.78 roots.
FEATURED: tuple[str, ...] = (
    "01.0001", "01.0381", "01.1137", "01.0919", "01.0002", "01.1049", "01.1151",
    "01.1074", "01.1075", "01.1076", "01.1077", "01.1078", "01.1079", "01.0990", "01.0991", "01.1086", "01.1143",
)


def _load() -> dict[str, Root]:
    text = files("panini.data").joinpath("dhatupatha_bhvadi.tsv").read_text(encoding="utf-8")
    roots = {}
    for line in text.splitlines()[1:]:
        code, upadesha, artha = line.split("\t")
        if code in ENGLISH:
            root = Root(code, upadesha, ENGLISH[code], "english")
        else:
            root = Root(code, upadesha, slp1_to_iast(artha), "traditional")
        roots[code] = root
    return roots


ROOTS: dict[str, Root] = _load()


class UnknownRoot(LookupError):
    def __init__(self, text: str, available: tuple[str, ...]):
        self.text, self.available = text, available
        shown = ", ".join(available[:12]) + (", …" if len(available) > 12 else "")
        super().__init__(f"unknown root: {text!r}; try a root such as {shown}, or a code like 01.0001")


class AmbiguousRoot(UnknownRoot):
    def __init__(self, text: str, codes: tuple[str, ...]):
        self.text, self.codes, self.available = text, codes, codes
        listing = "; ".join(f'{c} {ROOTS[c].name} "{ROOTS[c].meaning}"' for c in codes)
        LookupError.__init__(self, f"{text!r} names several roots; use a code: {listing}")


def _fold(s: str) -> str:
    bare = unicodedata.normalize("NFD", s).replace("̃", "").replace("~", "")
    return unicodedata.normalize("NFC", bare).strip().removesuffix("-").casefold()


def lookup_root(text: str) -> Root:
    """Find a root by code, name or IAST upadeśa, ignoring Unicode form, spaces and a trailing hyphen.

    A name shared by several roots resolves to the featured one if exactly one is featured."""
    norm = _fold(text)
    if text.strip() in ROOTS:
        return ROOTS[text.strip()]
    found = [r for r in ROOTS.values() if norm in (_fold(r.name), _fold(r.upadesha_iast))]
    if not found:
        raise UnknownRoot(text, tuple(r.name for r in (ROOTS[c] for c in FEATURED)))
    if len(found) > 1:
        featured = [r for r in found if r.code in FEATURED]
        if len(featured) != 1:
            raise AmbiguousRoot(text, tuple(r.code for r in found))
        return featured[0]
    return found[0]
