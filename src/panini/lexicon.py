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
_NASAL_FOR: dict[str, str] = {
    **dict.fromkeys("kKgGN", "N"),
    **dict.fromkeys("cCjJY", "Y"),
    **dict.fromkeys("wWqQR", "R"),
    **dict.fromkeys("pPbBm", "m"),
    **dict.fromkeys("Szsh", "M"),
}


type _Recited = list[tuple[str, bool]]  # (SLP1 sound, recited nasal)


def _strip_initial_markers(sounds: _Recited) -> _Recited:
    for marker in _INITIAL_MARKERS:  # ḍu, ṭu, ñi
        if "".join(c for c, _ in sounds[:2]) == marker and len(sounds) > 2:
            sounds = sounds[2:]
            break
    if (
        len(sounds) > 1 and sounds[0][1]
    ):  # an initial nasal vowel (o~, u~) is a marker too
        sounds = sounds[1:]
    return sounds


def _strip_markers(sounds: _Recited) -> tuple[_Recited, bool]:
    """The root without its marker sounds, and whether a final i~ made it idit."""
    sounds = _strip_initial_markers(sounds)
    nasal_vowels = [k for k, (_, nasal) in enumerate(sounds) if nasal]
    if not nasal_vowels:
        if len(sounds) > 1 and sounds[-1][0] in "NY":  # ṅ, ñ marker
            sounds = sounds[:-1]
        return sounds, False
    # A final i~ marks the root idit; i~r (dṛś, df\Si~r) is the marker ir, which adds no nasal.
    idit = nasal_vowels[-1] == len(sounds) - 1 and sounds[-1][0] == "i"
    # The last nasal vowel and whatever follows it are markers.
    return sounds[: nasal_vowels[-1]], idit


def _respell(text: str, idit: bool) -> str:
    """Quote the bare root as the grammar's spelling rules would leave it (SLP1)."""
    if text.startswith("z"):  # ṣ → s, and a following ṭ, ṭh, ṇ back to dental
        text = "s" + {"w": "t", "W": "T", "R": "n"}.get(text[1:2], text[1:2]) + text[2:]
    elif text.startswith("R"):
        text = "n" + text[1:]
    if idit and len(text) > 1 and text[-2] not in "nNYRmM":  # kradi~ -> krand
        text = text[:-1] + _NASAL_FOR.get(text[-1], "n") + text[-1]
    # A taught n before a consonant is quoted as the nasal of that consonant's place (sañj, tump,
    # śranbh -> śrambh), or as ṃ before a sibilant or h (daṃś); before a dental it stays n.
    return "".join(
        _NASAL_FOR.get(nxt, c) if c == "n" else c
        for c, nxt in zip(text, text[1:] + " ", strict=False)
    )


def citation_name(upadesha_slp1: str) -> str:
    r"""The root as it is usually quoted (IAST), e.g. ``ga\mx~`` -> gam, ``kradi~`` -> krand.

    Only a display label, so it uses plain string logic rather than the it-rules.
    """
    recited = [
        (s.char, s.nasal)
        for s in Term.from_upadesha(TermKind.ROOT, upadesha_slp1).sounds
    ]
    sounds, idit = _strip_markers(recited)
    return slp1_to_iast(_respell("".join(c for c, _ in sounds), idit))


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
        return GANAS[self.code[:2]]

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
        if middle_voice_markers(term):
            return "A"
        if "svaritet" in term.tags or term.upadesha.endswith("Y"):
            return "U"
        return "P"


def middle_voice_markers(root: Term) -> tuple[str, ...]:
    """The markers by which 1.3.12 anudāttaṅita ātmanepadam gives a root middle endings: "anudātta"
    (its marker vowel is unaccented) and/or "ṅ" (it is marked ṅ)."""
    found = (
        ("anudātta", "anudattet" in root.tags),
        ("ṅ", root.has_marker("N") or root.upadesha.endswith("N")),
    )
    return tuple(name for name, present in found if present)


def middle_voice_reason(
    root: Term, subject: str = "the root", markup: bool = True
) -> str:
    """Why 1.3.12 applies, e.g. "the root's marker vowel is {unaccented|anudātta}" or "the root is
    marked ṅ". ``subject`` "it" gives "its marker vowel …" / "it is marked ṅ"."""
    unaccented = "{unaccented|anudātta}" if markup else "unaccented (anudātta)"
    possessive = "its" if subject == "it" else f"{subject}'s"
    phrases = {
        "anudātta": f"{possessive} marker vowel is {unaccented}",
        "ṅ": f"{subject} is marked ṅ",
    }
    return " and ".join(phrases[m] for m in middle_voice_markers(root))


# English glosses for the roots the explorer features; the rest keep the list's own artha.
ENGLISH = {
    "01.0001": "to be, become",
    "01.0381": "to speak clearly, recite",
    "01.1137": "to go",
    "01.0919": "to remember",
    "01.0002": "to grow, prosper",
    "01.1049": "to lead",
    "01.1151": "to cook",
    "06.0001": "to strike, push",
    "06.0003": "to point, show",
    "06.0166": "to release",
    "06.0149": "to ask",
    "06.0145": "to scatter",
    "06.0139": "to die",
}

# The slice-1 seven, then the 7.3.78 roots, then six tudādi roots (slice 1.6).
FEATURED: tuple[str, ...] = (
    "01.0001",
    "01.0381",
    "01.1137",
    "01.0919",
    "01.0002",
    "01.1049",
    "01.1151",
    "01.1074",
    "01.1075",
    "01.1076",
    "01.1077",
    "01.1078",
    "01.1079",
    "01.0990",
    "01.0991",
    "01.1086",
    "01.1143",
    "06.0001",
    "06.0003",
    "06.0166",
    "06.0149",
    "06.0145",
    "06.0139",
)

# The upadeśas as the dhātupāṭha teaches them, for roots stored in another spelling
# (scripts/vendor_dhatupatha.py): yuch and uch are stored with cch. Lookup accepts either.
TAUGHT_AS: dict[str, tuple[str, ...]] = {
    "01.0242": ("yuch", "yuchã"),
    "01.0244": ("uch", "uchī̃"),
}


# The sections of the root list in scope: list-code prefix -> gaṇa, and the vendored file of each
# (scripts/vendor_dhatupatha.py).
GANAS: dict[str, str] = {"01": "bhvādi", "06": "tudādi"}
SECTION_FILES: dict[str, str] = {
    "01": "dhatupatha_bhvadi.tsv",
    "06": "dhatupatha_tudadi.tsv",
}


def _load() -> dict[str, Root]:
    lines = [
        line
        for name in SECTION_FILES.values()
        for line in files("panini.data")
        .joinpath(name)
        .read_text(encoding="utf-8")
        .splitlines()[1:]
    ]
    roots: dict[str, Root] = {}
    for line in lines:
        code, upadesha, artha = line.split("\t")
        if code in ENGLISH:
            root = Root(code, upadesha, ENGLISH[code], "english")
        else:
            root = Root(code, upadesha, slp1_to_iast(artha), "traditional")
        roots[code] = root
    return roots


ROOTS: dict[str, Root] = _load()


class UnknownRoot(LookupError):
    def __init__(self, text: str, available: tuple[str, ...]) -> None:
        self.text, self.available = text, available
        shown = ", ".join(available[:12]) + (", …" if len(available) > 12 else "")
        super().__init__(
            f"unknown root: {text!r}; try a root such as {shown}, or a code like 01.0001"
        )


class AmbiguousRoot(UnknownRoot):
    def __init__(self, text: str, codes: tuple[str, ...]) -> None:
        self.text, self.codes, self.available = text, codes, codes
        listing = "; ".join(f'{c} {ROOTS[c].name} "{ROOTS[c].meaning}"' for c in codes)
        LookupError.__init__(
            self, f"{text!r} names several roots; use a code: {listing}"
        )


def _fold(s: str) -> str:
    """Lookup key: no nasal sign (tilde or ~), no trailing hyphen, any case; other diacritics kept."""
    bare = unicodedata.normalize("NFD", s).replace("\u0303", "").replace("~", "")
    return unicodedata.normalize("NFC", bare).strip().removesuffix("-").casefold()


def _fold_ascii(s: str) -> str:
    """Looser key, like the explorer's search: every combining mark dropped (ṃ → m, ā → a, ṭ → t)."""
    return "".join(
        c
        for c in unicodedata.normalize("NFD", _fold(s))
        if not unicodedata.combining(c)
    )


def lookup_root(text: str) -> Root:
    """Find a root by code, name or IAST upadeśa, ignoring Unicode form, spaces and a trailing hyphen.

    A spelling with its diacritics is matched first; failing that, one without them (sanj, stha).
    A name shared by several roots resolves to the featured one if exactly one is featured."""
    if text.strip() in ROOTS:
        return ROOTS[text.strip()]
    found: list[Root] = []
    for fold in (_fold, _fold_ascii):
        norm = fold(text)
        found = [
            r
            for r in ROOTS.values()
            if norm
            in (
                fold(r.name),
                fold(r.upadesha_iast),
                *map(fold, TAUGHT_AS.get(r.code, ())),
            )
        ]
        if found:
            break
    if not found:
        raise UnknownRoot(text, tuple(r.name for r in (ROOTS[c] for c in FEATURED)))
    if len(found) > 1:
        featured = [r for r in found if r.code in FEATURED]
        if len(featured) != 1:
            raise AmbiguousRoot(text, tuple(r.code for r in found))
        return featured[0]
    return found[0]
