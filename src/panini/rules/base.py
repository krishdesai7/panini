"""The Rule type, sūtra metadata, and helpers shared by rule modules."""

from __future__ import annotations

import tomllib
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from functools import cache
from importlib.resources import files

from panini.edits import VIKRTA, Edit
from panini.model import Site, State, Term, TermKind


class Optionality(Enum):
    VA = "vā"                   # preferably (Kiparsky): applies, alternative noted
    VIBHASHA = "vibhāṣā"        # preferably not: skipped, alternative noted
    ANYATARASYAM = "anyatarasyām"  # equal: not supported in slice 1


@cache
def _sutras() -> dict[str, dict[str, str]]:
    return tomllib.loads(files("panini.data").joinpath("sutras.toml").read_text(encoding="utf-8"))


def sutra_info(rule_id: str) -> tuple[str, str]:
    """(IAST text, plain-English gloss) for a sūtra. Raises KeyError if absent."""
    entry = _sutras()[rule_id]
    return entry["text"], entry["gloss"]


def sutra_key(rule_id: str) -> tuple[int, int, int]:
    a, b, c = (int(x) for x in rule_id.split("."))
    return (a, b, c)


@dataclass(frozen=True)
class Rule:
    """One sūtra as an operation: where it applies (find) and what it does (rewrite)."""

    id: str
    find: Callable[[State], list[Site]]
    rewrite: Callable[[State, Site], Edit]
    blocks: tuple[str, ...] = ()
    near_miss: Callable[[State], str | None] | None = None
    note: Callable[[State, Site], str | None] | None = None
    optional: Optionality | None = None
    assigns: str | None = None
    tuk_or_satva: bool = False
    reintroduces_upadesha: bool = False
    section_override: str | None = None  # tests only: "tripadi" or "main"

    @property
    def key(self) -> tuple[int, int, int]:
        return sutra_key(self.id)

    @property
    def in_tripadi(self) -> bool:
        if self.section_override is not None:
            return self.section_override == "tripadi"
        return (8, 2, 1) <= self.key <= (8, 4, 68)

    @property
    def in_ekasamjna(self) -> bool:
        return (1, 4, 1) <= self.key <= (2, 2, 38)

    @property
    def in_6_1_86_domain(self) -> bool:
        return (6, 1, 87) <= self.key <= (6, 1, 110)

    @property
    def in_abhiya(self) -> bool:
        return (6, 4, 23) <= self.key <= (6, 4, 175)

    @property
    def is_it_rule(self) -> bool:
        return (1, 3, 2) <= self.key <= (1, 3, 9)

    @property
    def text(self) -> str:
        return sutra_info(self.id)[0]

    @property
    def gloss(self) -> str:
        return sutra_info(self.id)[1]


# -- helpers shared by rule modules ---------------------------------------

PRATYAYA_KINDS = frozenset({TermKind.LA, TermKind.TIN, TermKind.VIKARANA})


def is_upadesha(term: Term) -> bool:
    """Still in its recited form (only markers removed), so the it-rules may read it."""
    return VIKRTA not in term.tags


def is_pratyaya(term: Term) -> bool:
    return term.kind in PRATYAYA_KINDS


def dhatu_index(state: State) -> int | None:
    for i, t in enumerate(state.terms):
        if t.kind is TermKind.ROOT:
            return i
    return None


def unmarked(term: Term) -> list[int]:
    """Positions of sounds not yet marked as it."""
    return [k for k, s in enumerate(term.sounds) if not s.it]


def word_text(state: State) -> str:
    return "".join(t.text for t in state.terms)
