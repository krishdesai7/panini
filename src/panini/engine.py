"""The derivation engine: main-body loop, one-pass tripādī, optional rules."""

from __future__ import annotations

from copy import copy
from dataclasses import replace
from typing import TYPE_CHECKING, Any, Self
lazy from collections.abc import Callable, Mapping, Sequence

from panini.rules.readings import Aside

from .derivation import Derivation, Status, StepRecord, render_terms
from .edits import AddTags, Edit, InsertTerm, ReplaceTerm, apply_edit
from .model import Site, State, Term, TermKind
from .request import Request, availability
from .resolver import (
    Candidate,
    LocalResolver,
    Loser,
    Resolver,
    UnresolvedConflict,
    blocked_by,
)
from .rules.base import Optionality, Rule
from .translit import slp1_to_iast

if TYPE_CHECKING:
    from typing import Literal

    from .edits import Op
    from .model import Sound
    from .resolver import Choice


class StepLimitExceeded(Exception):
    pass


class OptionalRuleNotSupported(Exception):
    pass


def final_text(state: State) -> str:
    return slp1_to_iast("".join(t.text for t in state.terms))


def run(
    state: State,
    rules: Sequence[Rule],
    *,
    resolver: Resolver | None = None,
    max_steps: int = 400,
    disabled: frozenset[str] = frozenset(),
) -> tuple[State, tuple[StepRecord, ...], tuple[str, ...]]:
    """Derive from ``state``: the main body until nothing applies, then the tripādī once.

    Returns the final state, the recorded steps, and alternative final forms
    produced by optional rules.
    """
    runner = _Runner(rules, resolver or LocalResolver(), max_steps, disabled)
    final, steps, alternatives = runner.run(state)
    return final, steps, alternatives


type Resume = tuple[Literal["main"]] | tuple[Literal["tripadi"], tuple[int, int, int]]


def _step_kind(edit: Edit) -> str:
    """change: the form changes; category: only labels are assigned; prohibition:
    nothing (a niṣedha)."""
    if not edit:
        return "prohibition"
    if all(isinstance(op, AddTags) for op in edit):
        return "category"
    return "change"


def _join(*parts: str | None) -> str | None:
    kept: list[str] = [p for p in parts if p]
    return "; ".join(kept) if kept else None


class _Runner:
    def __init__(
        self,
        rules: Sequence[Rule],
        resolver: Resolver,
        max_steps: int,
        disabled: frozenset[str],
    ) -> None:
        self.all_rules: tuple[Rule, ...] = tuple(rules)
        self.resolver: Resolver = resolver
        self.max_steps: int = max_steps
        self.disabled: frozenset[str] = disabled
        self.rules: tuple[Rule, ...] = tuple(r for r in rules if r.id not in disabled)
        self.main: tuple[Rule, ...] = tuple(r for r in self.rules if not r.in_tripadi)
        self.it_rules: tuple[Rule, ...] = tuple(r for r in self.main if r.is_it_rule)
        self.tripadi: tuple[Rule, ...] = tuple(
            sorted((r for r in self.rules if r.in_tripadi), key=lambda r: r.key)
        )
        self.steps: list[StepRecord] = []
        self.alternatives: list[str] = []
        self.declined: set[Any] = (
            set()
        )  # (rule id, terms) where an optional rule chose not to apply
        self.applied: set[Any] = set()
        self.near_seen: set[str] = set()
        self.abhiya: list[str] = []
        self.losers_seen: set[Loser] = set()
        self.count = 0
        self.nested = False  # lookahead runners don't look ahead again
        # _settle results, shared with this derivation's lookahead runners:
        # (state, edit, disabled) -> state
        self.settle_cache: dict[tuple[State, Edit, frozenset[str]], State] = {}

    @property
    def _effective(self) -> tuple[Rule, ...]:
        """The rules as blockers: a rule that declined to apply (vibhāṣā, a sense
        condition) blocks nothing at that site, so the general rule it would have
        overridden applies after all."""
        if not self.declined:
            return self.rules
        declined: set[tuple[str, tuple[TermKind, str]]] = self.declined

        def undeclined(r: Rule) -> Callable[[State], list[Site]]:
            return lambda st: [
                s for s in r.find(st) if (r.id, self._terms_key(st, s)) not in declined
            ]

        ids: set[str] = {rid for rid, _ in declined}
        return tuple(
            replace(r, find=undeclined(r)) if r.id in ids else r for r in self.rules
        )

    @staticmethod
    def _terms_key(state: State, site: Site) -> tuple[tuple[TermKind, str], ...]:
        return tuple(
            (state.terms[sp.term].kind, state.terms[sp.term].upadesha)
            for sp in site.spans
            if sp.term < len(state.terms)
        )

    def _was_declined(self, state: State, cand: Candidate) -> bool:
        return (cand.rule.id, self._terms_key(state, cand.site)) in self.declined

    # -- bookkeeping -------------------------------------------------------

    @staticmethod
    def _fp(
        state: State, site: Site
    ) -> tuple[tuple[TermKind, str, tuple[Sound, ...], int, int] | None, ...]:
        """The input a rule reads at a site, independent of term indices (which shift
        when terms are inserted) and of tags (saṃjñā tags don't make old material new
        input)."""
        out: list[tuple[TermKind, str, tuple[Sound, ...], int, int] | None] = []
        for sp in site.spans:
            t: Term | None = (
                state.terms[sp.term] if sp.term < len(state.terms) else None
            )
            out.append(
                None if t is None else (t.kind, t.upadesha, t.sounds, sp.start, sp.end)
            )
        return tuple(out)

    def _guard_key(
        self, state: State, cand: Candidate
    ) -> tuple[
        str, tuple[tuple[TermKind, str, tuple[Sound, ...], int, int] | None, ...]
    ]:
        return (cand.rule.id, self._fp(state, cand.site))

    def _tick(self) -> None:
        self.count += 1
        if self.count > self.max_steps:
            raise StepLimitExceeded(
                f"more than {self.max_steps} steps; the rules may be looping"
            )

    # -- phases ------------------------------------------------------------

    def run(
        self,
        state: State,
        *,
        skip_main: bool = False,
        tripadi_from: tuple[int, int, int] | None = None,
    ) -> tuple[State, tuple[StepRecord, ...], tuple[str, ...]]:
        if not skip_main:
            state = self._main(state, self.main, ("main",))
        state: State = self._tripadi(state, tripadi_from)
        final: str = final_text(state)
        alts: tuple[str, ...] = tuple(
            dict.fromkeys(a for a in self.alternatives if a != final)
        )
        return state, tuple(self.steps), alts

    def _main(self, state: State, rules: Sequence[Rule], resume: Resume) -> State:
        while True:
            cands: list[Candidate] = [
                Candidate(r, s) for r in rules for s in r.find(state)
            ]
            cands: list[Candidate] = [
                c
                for c in cands
                if self._guard_key(state, c) not in self.applied
                and not self._was_declined(state, c)
            ]
            if not cands:
                return state
            choice: Choice | None = self.resolver.choose(
                state,
                cands,
                self._effective,
                finish=self._finish if not self.nested else None,
                settle=self._settle,
            )
            if choice is None:
                return state
            state, edit = self._apply(state, choice.winner, choice.losers, resume)
            if rules is not self.it_rules and any(
                isinstance(op, (InsertTerm, ReplaceTerm)) for op in edit
            ):
                # A newly introduced upadeśa is read with its markers (amendment A2).
                state: State = self._main(state, self.it_rules, resume)

    def _tripadi(self, state: State, start: tuple[int, int, int] | None) -> State:
        for rule in self.tripadi:
            if start is not None and rule.key < start:
                continue
            while True:
                free: list[Candidate] = []
                for site in rule.find(state):
                    cand = Candidate(rule, site)
                    key: tuple[
                        str,
                        tuple[
                            tuple[TermKind, str, tuple[Sound, ...], int, int] | None,
                            ...,
                        ],
                    ] = self._guard_key(state, cand)
                    if key in self.applied:
                        continue
                    if blocked_by(state, cand, self._effective):
                        self.applied.add(key)
                        continue
                    free.append(cand)
                if not free:
                    break
                state: State = self._apply(state, free[0], (), ("tripadi", rule.key))[0]
                if rule.reintroduces_upadesha:
                    # Amendment A2: newly introduced upadeśa material gets its
                    # markers identified and deleted right away.
                    state: State = self._main(
                        state, self.it_rules, ("tripadi", rule.key)
                    )
        return state

    # -- applying one rule -------------------------------------------------

    def _settle(self, state: State, edit: Edit) -> State:
        """Apply an edit as ``_main`` does, without recording it: the edit, then the
        reading of a new upadeśa's markers (amendment A2). The resolver's one-step
        checks use it."""
        new: State = apply_edit(state, edit)
        if not any(isinstance(op, (InsertTerm, ReplaceTerm)) for op in edit):
            return new
        key: tuple[State, tuple[Op, ...], frozenset[str]] = (state, edit, self.disabled)
        if key not in self.settle_cache:
            self.settle_cache[key] = self._read_new_markers(new, edit)
        return self.settle_cache[key]

    def _read_new_markers(self, new: State, edit: Edit) -> State:
        introduced: list[Term] = [
            op.term for op in edit if isinstance(op, (InsertTerm, ReplaceTerm))
        ]
        fresh: frozenset[int] = frozenset(
            i for i, t in enumerate(new.terms) if any(t is u for u in introduced)
        )
        if not fresh:
            return new

        def on_fresh(r: Rule) -> Rule:
            # Only the new upadeśa is read here; markers elsewhere wait for own step.
            return replace(
                r,
                find=lambda st: [
                    s for s in r.find(st) if all(sp.term in fresh for sp in s.spans)
                ],
            )

        sub: _Runner = self._lookahead_runner()
        return sub._main(new, tuple(on_fresh(r) for r in sub.it_rules), ("main",))

    def _lookahead_runner(self) -> _Runner:
        """A runner for a silent lookahead from the current state: same rules,
        nothing recorded here."""
        sub: Self = copy(
            self
        )  # shares the rule tuples; the mutable bookkeeping is replaced below
        sub.steps = []
        sub.alternatives = []
        sub.abhiya = []
        sub.applied = set(self.applied)
        sub.declined = set(self.declined)
        sub.near_seen = set(self.near_seen)
        sub.losers_seen = set(self.losers_seen)
        sub.nested = True
        return sub

    def _finish(self, state: State) -> str:
        """Final form reached from `state` (lookahead for resolver's conflict check)."""
        final: State = self._lookahead_runner().run(state)[0]
        return final_text(final)

    def _alternative(
        self, state: State, extra_disabled: frozenset[str], resume: Resume
    ) -> tuple[str, ...]:
        alt = _Runner(
            self.all_rules,
            self.resolver,
            self.max_steps,
            self.disabled | extra_disabled,
        )
        alt.applied = set(self.applied)
        alt.declined = set(self.declined)
        alt.count = self.count
        if resume[0] == "main":
            final, _, alts = alt.run(state)
        else:
            final, _, alts = alt.run(state, skip_main=True, tripadi_from=resume[1])
        return (final_text(final), *alts)

    def _new_losers(self, losers: tuple[Loser, ...]) -> tuple[Loser, ...]:
        """Each competitor is reported once, at the first step where it lost."""
        fresh: tuple[Loser, ...] = tuple(
            dict.fromkeys(loser for loser in losers if loser not in self.losers_seen)
        )
        self.losers_seen.update(fresh)
        return fresh

    def _apply(
        self, state: State, cand: Candidate, losers: tuple[Loser, ...], resume: Resume
    ) -> tuple[State, Edit]:
        self._tick()
        rule: Rule = cand.rule
        self.applied.add(self._guard_key(state, cand))
        edit: tuple[Op, ...] = rule.rewrite(state, cand.site)
        note: str | None = rule.note(state, cand.site) if rule.note else None
        alternatives: tuple[str, ...] = ()

        match rule.optional:
            case None:
                new: State = apply_edit(state, edit)
            case Optionality.VA:
                new: State = apply_edit(state, edit)
                alternatives: tuple[str, ...] = self._alternative(
                    state, frozenset({rule.id}), resume
                )
                note: str | None = _join(
                    note, "{preferably|vā}; also correct: " + ", ".join(alternatives)
                )
            case Optionality.VIBHASHA | Optionality.SENSE:
                new = state
                self.declined.add((rule.id, self._terms_key(state, cand.site)))
                alternatives = self._alternative(
                    apply_edit(state, edit), frozenset({rule.id}), resume
                )
                note = _join(
                    note,
                    (rule.optional_phrase or "{preferably not|vibhāṣā}, so not applied")
                    + "; also correct: "
                    + ", ".join(alternatives),
                )
            case Optionality.ANYATARASYAM:
                raise OptionalRuleNotSupported(
                    f"{rule.id} is optional (anyatarasyām, an equal choice); optional"
                    "rules of this kind are not supported yet"
                )

        warnings: list[str] = []
        if rule.in_abhiya:
            others: list[str] = [a for a in self.abhiya if a != rule.id]
            if others:
                warnings.append(
                    f"6.4.22: {others[0]} and {rule.id} are both in the ābhīya section;"
                    " asiddhavat not modelled in slice 1"
                )
            self.abhiya.append(rule.id)

        near: list[str] = []
        for r in self.rules:
            if r.near_miss is not None:
                msg = r.near_miss(new)
                if msg and msg not in self.near_seen:
                    self.near_seen.add(msg)
                    near.append(msg)

        aside: Aside | None = rule.history(state, cand.site) if rule.history else None
        # A later choice varies fastest, so its alternatives come before earlier ones'.
        self.alternatives[:0] = alternatives
        self.steps.append(
            StepRecord(
                rule_ids=(rule.id,),
                before=render_terms(state.terms),
                after=render_terms(new.terms),
                note=note,
                losers=self._new_losers(losers),
                near_misses=tuple(near),
                warnings=tuple(warnings),
                alternatives=alternatives,
                kind=_step_kind(edit),
                reads=rule.reads if rule.section_override is None else (),
                history=aside.text if aside else None,
                history_italic=aside.italic if aside else (),
            )
        )
        return new, edit


def derive(
    req: Request,
    *,
    resolver: Resolver | None = None,
    rules: Sequence[Rule] | None = None,
    disabled: frozenset[str] = frozenset(),
    reference: Mapping[str, list[str]] | None = None,
) -> Derivation:
    """Derive the form a request asks for, with its full step-by-step record."""
    from panini.rules import ALL_RULES

    panini, pie = req.describe()
    record: dict[str, str] = {
        "key": req.key,
        "root": req.root.name,
        "panini": panini,
        "pie": pie,
    }
    ref: tuple[str, ...] | None = (
        tuple(reference[req.key]) if reference and req.key in reference else None
    )
    if (why := availability(req)) is not None:
        reason, rule_id = why
        return Derivation(
            record, Status.UNAVAILABLE, None, (), ref, (), f"{reason} ({rule_id})"
        )
    state = State((Term.from_upadesha(TermKind.ROOT, req.root.upadesha),), req.intent())
    try:
        final, steps, alternatives = run(
            state,
            ALL_RULES if rules is None else rules,
            resolver=resolver,
            disabled=disabled,
        )
    except (UnresolvedConflict, StepLimitExceeded, OptionalRuleNotSupported) as e:
        return Derivation(record, Status.ERROR, None, (), ref, (), str(e))
    return Derivation(
        record, Status.OK, final_text(final), alternatives, ref, steps, None
    )
