"""The derivation record that the text trace, the tests and the GUI all read."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum

from panini.model import Term
from panini.resolver import Loser
from panini.translit import slp1_to_iast


class Status(Enum):
    OK = "ok"
    EXPECTED_FAILURE = "expected_failure"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


@dataclass(frozen=True)
class TermView:
    """One term as displayed: (IAST sound, is_marker) pairs."""

    chars: tuple[tuple[str, bool], ...]

    def iast(self) -> str:
        """Markers in capitals (first letter of the sound); a nasal vowel keeps its tilde."""
        return "".join(c[:1].upper() + c[1:] if marker else c for c, marker in self.chars)


def render_terms(terms: Iterable[Term]) -> tuple[TermView, ...]:
    views = []
    for t in terms:
        if not t.sounds:
            continue
        views.append(TermView(tuple(
            (slp1_to_iast(s.char + ("~" if s.nasal else "")), s.it) for s in t.sounds
        )))
    return tuple(views)


@dataclass(frozen=True)
class StepRecord:
    rule_ids: tuple[str, ...]
    before: tuple[TermView, ...]
    after: tuple[TermView, ...]
    note: str | None
    losers: tuple[Loser, ...]
    near_misses: tuple[str, ...]
    warnings: tuple[str, ...]
    alternatives: tuple[str, ...] = ()
    kind: str = "change"  # "change" (the form changes), "category" (assigns a label), "prohibition"

    def to_json(self) -> dict:
        from panini.rules.base import sutra_info

        def views(vs: tuple[TermView, ...]) -> list[dict]:
            return [{"iast": v.iast(), "chars": [[c, m] for c, m in v.chars]} for v in vs]

        sutras = []
        for rid in self.rule_ids:
            try:
                text, gloss = sutra_info(rid)
            except KeyError:
                text, gloss = "", ""
            sutras.append({"id": rid, "text": text, "gloss": gloss})
        return {
            "rule_ids": list(self.rule_ids),
            "sutras": sutras,
            "before": views(self.before),
            "after": views(self.after),
            "note": self.note,
            "losers": [{"rule_id": l.rule_id, "reason": l.reason} for l in self.losers],
            "near_misses": list(self.near_misses),
            "warnings": list(self.warnings),
            "alternatives": list(self.alternatives),
            "kind": self.kind,
        }


@dataclass(frozen=True)
class Derivation:
    request: dict
    status: Status
    result: str | None
    alternatives: tuple[str, ...]
    reference: tuple[str, ...] | None
    steps: tuple[StepRecord, ...]
    message: str | None

    def to_json(self) -> dict:
        return {
            "request": dict(self.request),
            "status": self.status.value,
            "result": self.result,
            "alternatives": list(self.alternatives),
            "reference": list(self.reference) if self.reference is not None else None,
            "steps": [s.to_json() for s in self.steps],
            "message": self.message,
        }
