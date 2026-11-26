"""The derivation record that the text trace, the tests and the GUI all read."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING
lazy from collections.abc import Iterable

from panini.translit import slp1_to_iast
lazy from panini.model import Term
lazy from panini.resolver import Loser

if TYPE_CHECKING:
    from typing import Any


class Status(Enum):
    OK = "ok"
    EXPECTED_FAILURE = "expected_failure"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


@dataclass(frozen=True)
class TermView:
    """One term as displayed: (IAST sound, is_marker) pairs."""

    chars: tuple[tuple[str, bool], ...]
    upadesha: str = (
        ""  # the term as taught, in IAST (lets the page explain its markers)
    )

    def iast(self) -> str:
        """Markers in capitals; a nasal vowel keeps its tilde."""
        return "".join(
            c[:1].upper() + c[1:] if marker else c for c, marker in self.chars
        )


def render_terms(terms: Iterable[Term]) -> tuple[TermView, ...]:
    views: list[TermView] = []
    for t in terms:
        if not t.sounds:
            continue
        views.append(
            TermView(
                tuple(
                    (slp1_to_iast(s.char + ("~" if s.nasal else "")), s.it)
                    for s in t.sounds
                ),
                slp1_to_iast(t.upadesha),
            )
        )
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
    reads: tuple[tuple[str, str], ...] = ()
    # "change" (the form changes), "category" (assigns a label), "prohibition"
    kind: str = "change"
    history: str | None = (
        None  # a historical aside about the step (not part of Pāṇini's account)
    )
    history_italic: tuple[
        str, ...
    ] = ()  # words of the aside to set in italics (Latin, Greek)

    def to_json(self) -> dict[str, Any]:
        from panini.rules.base import sutra_info

        def views(vs: tuple[TermView, ...]) -> list[dict[str, Any]]:
            return [
                {
                    "iast": v.iast(),
                    "chars": [[c, m] for c, m in v.chars],
                    "upadesha": v.upadesha,
                }
                for v in vs
            ]

        sutras: list[dict[str, str]] = []
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
            "losers": [
                {"rule_id": loser.rule_id, "reason": loser.reason}
                for loser in self.losers
            ],
            "near_misses": list(self.near_misses),
            "warnings": list(self.warnings),
            "alternatives": list(self.alternatives),
            "kind": self.kind,
            "reads": [{"id": i, "note": n} for i, n in self.reads],
            "history": self.history,
            "history_italic": list(self.history_italic),
        }


@dataclass(frozen=True)
class Derivation:
    request: dict[str, Any]
    status: Status
    result: str | None
    alternatives: tuple[str, ...]
    reference: tuple[str, ...] | None
    steps: tuple[StepRecord, ...]
    message: str | None

    def to_json(self) -> dict[str, Any]:
        return {
            "request": dict(self.request),
            "status": self.status.value,
            "result": self.result,
            "alternatives": list(self.alternatives),
            "reference": list(self.reference) if self.reference is not None else None,
            "steps": [s.to_json() for s in self.steps],
            "message": self.message,
        }
