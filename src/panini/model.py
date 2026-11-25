"""The derivation state: sounds, terms, the speaker's intent, and sites."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum

from panini.sounds import is_vowel


@dataclass(frozen=True)
class Sound:
    """One phoneme (SLP1 character) with flags.

    ``it``: marked as a marker (it-saṃjñā) by 1.3.2–1.3.8.
    ``nasal``: an anunāsika vowel as recited in an upadeśa (written ``~``).
    ``agama``: inserted as an augment (e.g. tuk).
    """

    char: str
    it: bool = False
    nasal: bool = False
    agama: bool = False
    upos: int | None = None  # position in the recited upadeśa; None for sounds added later
    ekadesha: bool = False  # a single substitute for two sounds (6.1.84), stored at the end of the left term
    ekadesha_rule: str | None = None  # the rule that made that substitute ...
    ekadesha_inputs: tuple[str, str] | None = None  # ... and the two sounds it replaced (left, right)


class TermKind(Enum):
    ROOT = "root"
    LA = "la"
    TIN = "tin"
    VIKARANA = "vikarana"
    AGAMA = "agama"


@dataclass(frozen=True)
class Term:
    """A morpheme-sized unit of the derivation: root, affix or augment."""

    kind: TermKind
    upadesha: str
    sounds: tuple[Sound, ...]
    tags: frozenset[str] = frozenset()
    markers: frozenset[str] = frozenset()
    replaced: Term | None = None

    @classmethod
    def from_upadesha(cls, kind: TermKind, upadesha_slp1: str, tags: frozenset[str] = frozenset()) -> Term:
        """Parse a recited form. ``~`` nasalizes the preceding vowel.

        Accent marks (``\\`` anudātta, ``^`` svarita) are not sounds. On a nasal
        marker vowel they are recorded as the tags ``anudattet``/``svaritet``,
        which pada assignment needs (1.3.12, 1.3.72); elsewhere they are dropped.
        """
        sounds: list[Sound] = []
        extra: set[str] = set()
        for c in upadesha_slp1:
            if c == "~":
                if sounds and is_vowel(sounds[-1].char):
                    sounds[-1] = replace(sounds[-1], nasal=True)
            elif c in "\\^":
                if sounds and sounds[-1].nasal:
                    extra.add("anudattet" if c == "\\" else "svaritet")
                elif sounds and is_vowel(sounds[-1].char):
                    extra.add("anudatta-vowel" if c == "\\" else "svarita-vowel")
            else:
                sounds.append(Sound(c, upos=len(sounds)))
        clean = upadesha_slp1.replace("\\", "").replace("^", "")
        return cls(kind, clean, tuple(sounds), frozenset(tags) | extra)

    @property
    def text(self) -> str:
        return "".join(s.char for s in self.sounds)

    @property
    def upadesha_len(self) -> int:
        """Number of sounds in the recited upadeśa."""
        return sum(1 for c in self.upadesha if c != "~")

    def upadesha_final(self) -> int | None:
        """Current index of the upadeśa's final sound, if still present."""
        last = self.upadesha_len - 1
        return next((k for k, s in enumerate(self.sounds) if s.upos == last), None)

    def upadesha_initial(self) -> int | None:
        """Current index of the upadeśa's first sound, if still present."""
        return next((k for k, s in enumerate(self.sounds) if s.upos == 0), None)

    def has_marker(self, m: str) -> bool:
        """Own markers, else those of the term this one replaced (1.1.56)."""
        if m in self.markers:
            return True
        return self.replaced is not None and self.replaced.has_marker(m)

    def has_tag(self, t: str) -> bool:
        if t in self.tags:
            return True
        return self.replaced is not None and self.replaced.has_tag(t)

    @property
    def adi(self) -> str | None:
        return self.sounds[0].char if self.sounds else None

    @property
    def antya(self) -> str | None:
        return self.sounds[-1].char if self.sounds else None

    @property
    def upadha(self) -> str | None:
        """The penultimate sound (1.1.65 alo 'ntyāt pūrva upadhā)."""
        return self.sounds[-2].char if len(self.sounds) >= 2 else None


class Time(Enum):
    PRESENT = "present"
    PAST_NOT_TODAY = "past not of today"


class Coreference(Enum):
    NONE = "none"
    ADDRESSEE = "addressee"
    SPEAKER = "speaker"


class Number(Enum):
    ONE = 1
    TWO = 2
    MANY = 3


@dataclass(frozen=True)
class Intent:
    """What the speaker means; the meanings the grammar responds to (vivakṣā)."""

    time: Time
    coreference: Coreference
    number: Number
    fruit_to_agent: bool


@dataclass(frozen=True)
class State:
    terms: tuple[Term, ...]
    intent: Intent


@dataclass(frozen=True)
class Span:
    """Half-open range of sound positions inside one term; ``end == -1`` is the whole term."""

    term: int
    start: int
    end: int

    def overlaps(self, other: Span) -> bool:
        if self.term != other.term:
            return False
        if self.end == -1 or other.end == -1:
            return True
        # Empty spans (insertion points) overlap a span that contains them.
        a0, a1 = self.start, max(self.end, self.start + 1)
        b0, b1 = other.start, max(other.end, other.start + 1)
        return a0 < b1 and b0 < a1


@dataclass(frozen=True)
class Site:
    """Where a rule applies: one or more spans (several for sandhi across terms)."""

    spans: tuple[Span, ...] = field(default_factory=tuple)

    def overlaps(self, other: Site) -> bool:
        return any(a.overlaps(b) for a in self.spans for b in other.spans)

    @classmethod
    def term(cls, i: int) -> Site:
        return cls((Span(i, 0, -1),))

    @classmethod
    def at(cls, term: int, start: int, end: int | None = None) -> Site:
        return cls((Span(term, start, start + 1 if end is None else end),))
