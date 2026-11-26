"""Choosing which applicable rule fires next.

LocalResolver implements the restricted siddha principle, the slice-1 design:

1. blocking: a rule listing B in ``blocks`` overrides B where their sites
   overlap (utsarga/apavāda, including collective blocking);
2. para (1.4.2), only for conflicting saṃjñā assignments inside the
   ekasaṃjñā section 1.4.1–2.2.38, as Kiparsky restricts it;
3. nitya: prefer X if X still makes the same change after Y applies, but
   Y no longer does after X (śabdāntaraprāpti: a changed effect doesn't count);
4. ties: the lowest-numbered candidate that commutes with all the others goes
   first (an arbitrary order with an identical result); if none commutes with
   all the others, raise UnresolvedConflict. The resolver never guesses.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from panini.edits import (
    AddTags,
    DeleteSounds,
    Edit,
    Ekadesha,
    InsertSounds,
    InsertTerm,
    MarkIt,
    ReplaceSounds,
    ReplaceTerm,
    apply_edit,
)
from panini.model import Site, State, TermKind
from panini.translit import slp1_to_iast

if TYPE_CHECKING:
    from panini.rules.base import Rule


@dataclass(frozen=True)
class Candidate:
    rule: Rule
    site: Site


@dataclass(frozen=True)
class Loser:
    rule_id: str
    reason: str


@dataclass(frozen=True)
class Choice:
    winner: Candidate
    losers: tuple[Loser, ...]


class UnresolvedConflict(Exception):
    def __init__(
        self,
        rule_ids: tuple[str, ...],
        sites: tuple[Site, ...],
        outcomes: tuple[str, ...],
    ) -> None:
        self.rule_ids, self.sites, self.outcomes = rule_ids, sites, outcomes
        super().__init__(
            "unresolved conflict between "
            + " and ".join(rule_ids)
            + ": the order matters ("
            + " vs ".join(outcomes)
            + ") and no meta-rule decides it"
        )


type Finish = Callable[[State], str]
# Applies an edit as the engine would: the edit, then the reading of any new upadeśa's markers
# (amendment A2). The one-step checks below use it so that they compare the states the engine
# would actually reach.
type Settle = Callable[[State, Edit], State]


class Resolver(Protocol):
    def choose(
        self,
        state: State,
        candidates: Sequence[Candidate],
        rules: Sequence[Rule],
        finish: Finish | None = None,
        settle: Settle | None = None,
    ) -> Choice | None: ...


def state_text(state: State) -> str:
    return slp1_to_iast(" + ".join(t.text for t in state.terms if t.sounds))


def blocked_by(state: State, cand: Candidate, rules: Sequence[Rule]) -> str | None:
    """The id of a rule that blocks this candidate here, if any.

    Uses each blocker's raw ``find``: a niṣedha that has already applied still blocks.
    """
    for r in rules:
        if cand.rule.id in r.blocks and any(
            s.overlaps(cand.site) for s in r.find(state)
        ):
            return r.id
    return None


type _TermKey = tuple[TermKind, str] | tuple[str, int]
# What an edit does, op by op: a tag naming the op, then what it reads and writes.
type EditSignature = tuple[tuple[object, ...], ...]


def _term_key(state: State, i: int) -> _TermKey:
    if 0 <= i < len(state.terms):
        t = state.terms[i]
        return (t.kind, t.upadesha)
    return ("new", i)


def edit_signature(state: State, edit: Edit) -> EditSignature:
    """What an edit does, ignoring positions (which shift when other rules insert terms)."""
    sig: list[tuple[object, ...]] = []
    for op in edit:
        match op:
            case AddTags(term=i, tags=tags):
                sig.append(("tags", _term_key(state, i), tuple(sorted(tags))))
            case MarkIt(term=i, positions=pos) | DeleteSounds(term=i, positions=pos):
                chars = tuple(
                    state.terms[i].sounds[p].char
                    for p in pos
                    if p < len(state.terms[i].sounds)
                )
                sig.append((type(op).__name__, _term_key(state, i), chars))
            case ReplaceSounds(term=i, start=a, end=b, sounds=new):
                old = tuple(s.char for s in state.terms[i].sounds[a:b])
                sig.append(
                    ("replace", _term_key(state, i), old, tuple(s.char for s in new))
                )
            case InsertSounds(term=i, sounds=new):
                sig.append(("insert", _term_key(state, i), tuple(s.char for s in new)))
            case InsertTerm(term=t):
                sig.append(("insert_term", t.kind, t.upadesha))
            case ReplaceTerm(index=i, term=t):
                sig.append(("replace_term", _term_key(state, i), t.upadesha))
            case Ekadesha(left=l, right=r, sounds=new):
                lt, rt = state.terms[l], state.terms[r]
                # The terms are part of what it does: a + a → a between the root and śap is a
                # different change from a + a → a between the root and the ending.
                sig.append(
                    (
                        "ekadesha",
                        _term_key(state, l),
                        _term_key(state, r),
                        lt.antya,
                        rt.adi,
                        tuple(s.char for s in new),
                    )
                )
    return tuple(sig)


def _matching_site(
    state: State, cand: Candidate, signature: EditSignature
) -> Site | None:
    for site in cand.rule.find(state):
        if edit_signature(state, cand.rule.rewrite(state, site)) == signature:
            return site
    return None


def still_applies(
    state: State, x: Candidate, after: Candidate, settle: Settle = apply_edit
) -> bool:
    """Does x still make the same change once ``after`` has applied?"""
    sig = edit_signature(state, x.rule.rewrite(state, x.site))
    s2 = settle(state, after.rule.rewrite(state, after.site))
    return _matching_site(s2, x, sig) is not None


def then(
    state: State, first: Candidate, second: Candidate, settle: Settle = apply_edit
) -> State:
    """Apply ``first``, then ``second`` if it still applies (at the matching site, else its first site)."""
    sig = edit_signature(state, second.rule.rewrite(state, second.site))
    s1 = settle(state, first.rule.rewrite(state, first.site))
    site = _matching_site(s1, second, sig)
    if site is None:
        sites = second.rule.find(s1)
        site = sites[0] if sites else None
    return s1 if site is None else settle(s1, second.rule.rewrite(s1, site))


def _site_terms(site: Site) -> frozenset[int]:
    return frozenset(sp.term for sp in site.spans)


# Two orders that give different states: (first, second, first-then-second, second-then-first).
type _Conflict = tuple[Candidate, Candidate, State, State]


def _unblocked(
    state: State,
    candidates: Sequence[Candidate],
    rules: Sequence[Rule],
    losers: list[Loser],
) -> list[Candidate]:
    """Step 1: drop candidates another rule blocks here, recording each as a loser."""
    remaining: list[Candidate] = []
    for c in candidates:
        blocker = blocked_by(state, c, rules)
        if blocker is None:
            remaining.append(c)
        else:
            losers.append(Loser(c.rule.id, f"blocked by {blocker}"))
    return remaining


def _loses_by_para(a: Candidate, b: Candidate) -> bool:
    """Does ``a`` give way to ``b`` under para: conflicting saṃjñās in the ekasaṃjñā section?"""
    return bool(
        a.rule.assigns
        and b.rule.assigns
        and a.rule.assigns != b.rule.assigns
        and a.rule.in_ekasamjna
        and b.rule.in_ekasamjna
        and _site_terms(a.site) & _site_terms(b.site)
        and a.rule.key < b.rule.key
    )


def _drop_para_losers(remaining: list[Candidate], losers: list[Loser]) -> None:
    """Step 2: para (1.4.2), restricted to conflicting saṃjñās in the ekasaṃjñā section."""
    for a in list(remaining):
        for b in list(remaining):
            if a is b or a not in remaining or b not in remaining:
                continue
            if _loses_by_para(a, b):
                remaining.remove(a)
                losers.append(
                    Loser(
                        a.rule.id,
                        f"para: {b.rule.id} comes later in the ekasaṃjñā section (1.4.2)",
                    )
                )


def _nitya_domination(
    state: State, remaining: list[Candidate], settle: Settle
) -> dict[int, Candidate]:
    """Step 3: index of each dominated candidate -> the candidate that dominates it.

    X dominates Y if X survives Y but Y does not survive X.
    """
    dominated_by: dict[int, Candidate] = {}
    for i, x in enumerate(remaining):
        for j, y in enumerate(remaining):
            if (
                i != j
                and j not in dominated_by
                and still_applies(state, x, y, settle)
                and not still_applies(state, y, x, settle)
            ):
                dominated_by[j] = x
    return dominated_by


def _first_conflict(
    state: State, c: Candidate, others: list[Candidate], settle: Settle
) -> _Conflict | None:
    for other in others:
        if other is c:
            continue
        a, b = then(state, c, other, settle), then(state, other, c, settle)
        if a != b:
            return (c, other, a, b)
    return None


def _first_commuting(
    state: State, ordered: list[Candidate], settle: Settle
) -> Candidate | _Conflict:
    """Step 4: the first candidate that commutes with every other one, else the first conflict.

    Its order is immaterial, so it decides nothing, and it may give the next step the
    information (a new blocker, a nitya relation) that settles a remaining conflict.
    """
    conflicts: list[_Conflict] = []
    for c in ordered:
        found = _first_conflict(state, c, ordered, settle)
        if found is None:
            return c
        conflicts.append(found)
    return conflicts[0]


def _final_forms(
    finish: Finish | None, a: State, b: State
) -> tuple[str | None, str | None]:
    if finish is None:
        return None, None
    try:
        return finish(a), finish(b)
    except UnresolvedConflict:
        return None, None


def _accept_if_same_result(
    conflict: _Conflict, finish: Finish | None, losers: list[Loser]
) -> None:
    """Return if both orders reach the same final form; otherwise raise UnresolvedConflict.

    The immediate states differ, but if both orders still lead to the same final form the
    order is immaterial to the result (the siddha definition compares results).
    """
    c, other, a, b = conflict
    ids, sites = (c.rule.id, other.rule.id), (c.site, other.site)
    fa, fb = _final_forms(finish, a, b)
    if fa is None:
        raise UnresolvedConflict(ids, sites, (state_text(a), state_text(b)))
    if fa != fb:
        raise UnresolvedConflict(ids, sites, (fa, fb or "?"))
    if other.rule.id != c.rule.id:
        losers.append(
            Loser(
                other.rule.id,
                f"order with {c.rule.id} is immaterial: both orders give {fa}; "
                "the lower-numbered rule goes first",
            )
        )


def _with_nitya_losers(
    winner: Candidate,
    remaining: list[Candidate],
    dominated_by: dict[int, Candidate],
    losers: list[Loser],
) -> Choice:
    # "Deferred because X is nitya" is reported on the step where X applies.
    # A rule at two sites is not two rules competing: both applications appear as steps.
    extra = [
        Loser(
            remaining[k].rule.id,
            f"deferred: {x.rule.id} {{applies either way|nitya}}",
        )
        for k, x in dominated_by.items()
        if x is winner and remaining[k].rule.id != winner.rule.id
    ]
    return Choice(winner, tuple(losers + extra))


class LocalResolver:
    def choose(
        self,
        state: State,
        candidates: Sequence[Candidate],
        rules: Sequence[Rule],
        finish: Finish | None = None,
        settle: Settle | None = None,
    ) -> Choice | None:
        settle = settle or apply_edit
        losers: list[Loser] = []
        remaining = _unblocked(state, candidates, rules, losers)
        _drop_para_losers(remaining, losers)
        if not remaining:
            return None
        if len(remaining) == 1:
            return Choice(remaining[0], tuple(losers))

        dominated_by = _nitya_domination(state, remaining, settle)
        # Cyclic domination leaves nothing undominated; treat all as tied.
        undominated = [
            c for k, c in enumerate(remaining) if k not in dominated_by
        ] or list(remaining)
        undominated.sort(
            key=lambda c: (c.rule.key, [(sp.term, sp.start) for sp in c.site.spans])
        )
        found = _first_commuting(state, undominated, settle)
        if isinstance(found, Candidate):
            return _with_nitya_losers(found, remaining, dominated_by, losers)
        _accept_if_same_result(found, finish, losers)
        return _with_nitya_losers(found[0], remaining, dominated_by, losers)
