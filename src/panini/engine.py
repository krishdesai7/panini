"""The derivation engine: main-body loop, one-pass tripādī, optional rules."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from collections.abc import Mapping

from panini.derivation import Derivation, Status, StepRecord, render_terms
from panini.edits import InsertTerm, ReplaceTerm, apply_edit
from panini.model import Site, State, Term, TermKind
from panini.request import Request, availability
from panini.resolver import Candidate, LocalResolver, Loser, Resolver, UnresolvedConflict, blocked_by
from panini.rules.base import Optionality, Rule
from panini.translit import slp1_to_iast


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


def _join(*parts: str | None) -> str | None:
    kept = [p for p in parts if p]
    return "; ".join(kept) if kept else None


class _Runner:
    def __init__(self, rules: Sequence[Rule], resolver: Resolver, max_steps: int, disabled: frozenset[str]):
        self.all_rules = tuple(rules)
        self.resolver = resolver
        self.max_steps = max_steps
        self.disabled = disabled
        self.rules = tuple(r for r in rules if r.id not in disabled)
        self.main = tuple(r for r in self.rules if not r.in_tripadi)
        self.it_rules = tuple(r for r in self.main if r.is_it_rule)
        self.tripadi = tuple(sorted((r for r in self.rules if r.in_tripadi), key=lambda r: r.key))
        self.steps: list[StepRecord] = []
        self.alternatives: list[str] = []
        self.applied: set[tuple] = set()
        self.near_seen: set[str] = set()
        self.abhiya: list[str] = []
        self.losers_seen: set[Loser] = set()
        self.count = 0

    # -- bookkeeping -------------------------------------------------------

    @staticmethod
    def _fp(state: State, site: Site) -> tuple:
        """The input a rule reads at a site, independent of term indices (which shift when
        terms are inserted) and of tags (saṃjñā tags don't make old material new input)."""
        out = []
        for sp in site.spans:
            t = state.terms[sp.term] if sp.term < len(state.terms) else None
            out.append(None if t is None else (t.kind, t.upadesha, t.sounds, sp.start, sp.end))
        return tuple(out)

    def _guard_key(self, state: State, cand: Candidate) -> tuple:
        return (cand.rule.id, self._fp(state, cand.site))

    def _tick(self) -> None:
        self.count += 1
        if self.count > self.max_steps:
            raise StepLimitExceeded(f"more than {self.max_steps} steps; the rules may be looping")

    # -- phases ------------------------------------------------------------

    def run(self, state: State, *, skip_main: bool = False,
            tripadi_from: tuple[int, int, int] | None = None) -> tuple[State, tuple[StepRecord, ...], tuple[str, ...]]:
        if not skip_main:
            state = self._main(state, self.main, ("main",))
        state = self._tripadi(state, tripadi_from)
        final = final_text(state)
        alts = tuple(dict.fromkeys(a for a in self.alternatives if a != final))
        return state, tuple(self.steps), alts

    def _main(self, state: State, rules: Sequence[Rule], resume: Resume) -> State:
        while True:
            cands = [Candidate(r, s) for r in rules for s in r.find(state)]
            cands = [c for c in cands if self._guard_key(state, c) not in self.applied]
            if not cands:
                return state
            choice = self.resolver.choose(state, cands, self.rules)
            if choice is None:
                return state
            edit = choice.winner.rule.rewrite(state, choice.winner.site)
            state = self._apply(state, choice.winner, choice.losers, resume)
            if rules is not self.it_rules and any(isinstance(op, (InsertTerm, ReplaceTerm)) for op in edit):
                # A newly introduced upadeśa is read with its markers (amendment A2, generalized).
                state = self._main(state, self.it_rules, resume)

    def _tripadi(self, state: State, start: tuple[int, int, int] | None) -> State:
        for rule in self.tripadi:
            if start is not None and rule.key < start:
                continue
            while True:
                free = []
                for site in rule.find(state):
                    cand = Candidate(rule, site)
                    key = self._guard_key(state, cand)
                    if key in self.applied:
                        continue
                    if blocked_by(state, cand, self.rules):
                        self.applied.add(key)
                        continue
                    free.append(cand)
                if not free:
                    break
                state = self._apply(state, free[0], (), ("tripadi", rule.key))
                if rule.reintroduces_upadesha:
                    # Amendment A2: newly introduced upadeśa material gets its
                    # markers identified and deleted right away.
                    state = self._main(state, self.it_rules, ("tripadi", rule.key))
        return state

    # -- applying one rule -------------------------------------------------

    def _alternative(self, state: State, extra_disabled: frozenset[str], resume: Resume) -> tuple[str, ...]:
        alt = _Runner(self.all_rules, self.resolver, self.max_steps, self.disabled | extra_disabled)
        alt.applied = set(self.applied)
        alt.count = self.count
        if resume[0] == "main":
            final, _, alts = alt.run(state)
        else:
            final, _, alts = alt.run(state, skip_main=True, tripadi_from=resume[1])
        return (final_text(final), *alts)

    def _new_losers(self, losers: tuple[Loser, ...]) -> tuple[Loser, ...]:
        """Each competitor is reported once, at the first step where it lost."""
        fresh = tuple(dict.fromkeys(l for l in losers if l not in self.losers_seen))
        self.losers_seen.update(fresh)
        return fresh

    def _apply(self, state: State, cand: Candidate, losers: tuple[Loser, ...], resume: Resume) -> State:
        self._tick()
        rule = cand.rule
        self.applied.add(self._guard_key(state, cand))
        edit = rule.rewrite(state, cand.site)
        note = rule.note(state, cand.site) if rule.note else None
        alternatives: tuple[str, ...] = ()

        match rule.optional:
            case None:
                new = apply_edit(state, edit)
            case Optionality.VA:
                new = apply_edit(state, edit)
                alternatives = self._alternative(state, frozenset({rule.id}), resume)
                note = _join(note, "optional (vā, ‘preferably’ per Kiparsky): also correct: " + ", ".join(alternatives))
            case Optionality.VIBHASHA:
                new = state
                alternatives = self._alternative(apply_edit(state, edit), frozenset({rule.id}), resume)
                note = _join(note, "optional (vibhāṣā, ‘preferably not’ per Kiparsky): not applied; also correct: "
                             + ", ".join(alternatives))
            case Optionality.ANYATARASYAM:
                raise OptionalRuleNotSupported(
                    f"{rule.id} is optional (anyatarasyām, an equal choice); optional rules of this kind "
                    "are not supported yet")

        warnings: list[str] = []
        if rule.in_abhiya:
            others = [a for a in self.abhiya if a != rule.id]
            if others:
                warnings.append(f"6.4.22: {others[0]} and {rule.id} are both in the ābhīya section; "
                                "asiddhavat not modelled in slice 1")
            self.abhiya.append(rule.id)

        near: list[str] = []
        for r in self.rules:
            if r.near_miss is not None:
                msg = r.near_miss(new)
                if msg and msg not in self.near_seen:
                    self.near_seen.add(msg)
                    near.append(msg)

        self.alternatives.extend(alternatives)
        self.steps.append(StepRecord(
            rule_ids=(rule.id,),
            before=render_terms(state.terms),
            after=render_terms(new.terms),
            note=note,
            losers=self._new_losers(losers),
            near_misses=tuple(near),
            warnings=tuple(warnings),
            alternatives=alternatives,
        ))
        return new


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
    record = {"key": req.key, "root": req.root.key, "panini": panini, "pie": pie}
    ref = tuple(reference[req.key]) if reference and req.key in reference else None
    if (why := availability(req)) is not None:
        reason, rule_id = why
        return Derivation(record, Status.UNAVAILABLE, None, (), ref, (), f"{reason} ({rule_id})")
    state = State((Term.from_upadesha(TermKind.ROOT, req.root.upadesha),), req.intent())
    try:
        final, steps, alternatives = run(state, ALL_RULES if rules is None else rules,
                                         resolver=resolver, disabled=disabled)
    except (UnresolvedConflict, StepLimitExceeded, OptionalRuleNotSupported) as e:
        return Derivation(record, Status.ERROR, None, (), ref, (), str(e))
    return Derivation(record, Status.OK, final_text(final), alternatives, ref, steps, None)
