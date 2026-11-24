"""Choosing which applicable rule fires next.

LocalResolver implements the restricted siddha principle, the slice-1 design:

1. blocking: a rule listing B in ``blocks`` overrides B where their sites
   overlap (utsarga/apavāda, including collective blocking);
2. para (1.4.2), only for conflicting saṃjñā assignments inside the
   ekasaṃjñā section 1.4.1–2.2.38, as Kiparsky restricts it;
3. nitya: prefer X if X still makes the same change after Y applies, but
   Y no longer does after X (śabdāntaraprāpti: a changed effect doesn't count);
4. ties: if the remaining candidates commute, the lowest sūtra number goes
   first (an arbitrary order with an identical result); otherwise raise
   UnresolvedConflict. The resolver never guesses.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from panini.edits import (AddTags, DeleteSounds, Edit, Ekadesha, InsertSounds, InsertTerm, MarkIt,
                          ReplaceSounds, ReplaceTerm, apply_edit)
from panini.model import Site, State
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
    def __init__(self, rule_ids: tuple[str, ...], sites: tuple[Site, ...], outcomes: tuple[str, ...]):
        self.rule_ids, self.sites, self.outcomes = rule_ids, sites, outcomes
        super().__init__(
            "unresolved conflict between " + " and ".join(rule_ids)
            + ": the order matters (" + " vs ".join(outcomes) + ") and no meta-rule decides it"
        )


class Resolver(Protocol):
    def choose(self, state: State, candidates: Sequence[Candidate], rules: Sequence[Rule]) -> Choice | None: ...


def state_text(state: State) -> str:
    return slp1_to_iast(" + ".join(t.text for t in state.terms if t.sounds))


def blocked_by(state: State, cand: Candidate, rules: Sequence[Rule]) -> str | None:
    """The id of a rule that blocks this candidate here, if any.

    Uses each blocker's raw ``find``: a niṣedha that has already applied still blocks.
    """
    for r in rules:
        if cand.rule.id in r.blocks and any(s.overlaps(cand.site) for s in r.find(state)):
            return r.id
    return None


def _term_key(state: State, i: int) -> tuple:
    if 0 <= i < len(state.terms):
        t = state.terms[i]
        return (t.kind, t.upadesha)
    return ("new", i)


def edit_signature(state: State, edit: Edit) -> tuple:
    """What an edit does, ignoring positions (which shift when other rules insert terms)."""
    sig = []
    for op in edit:
        match op:
            case AddTags(term=i, tags=tags):
                sig.append(("tags", _term_key(state, i), tuple(sorted(tags))))
            case MarkIt(term=i, positions=pos) | DeleteSounds(term=i, positions=pos):
                chars = tuple(state.terms[i].sounds[p].char for p in pos if p < len(state.terms[i].sounds))
                sig.append((type(op).__name__, _term_key(state, i), chars))
            case ReplaceSounds(term=i, start=a, end=b, sounds=new):
                old = tuple(s.char for s in state.terms[i].sounds[a:b])
                sig.append(("replace", _term_key(state, i), old, tuple(s.char for s in new)))
            case InsertSounds(term=i, sounds=new):
                sig.append(("insert", _term_key(state, i), tuple(s.char for s in new)))
            case InsertTerm(term=t):
                sig.append(("insert_term", t.kind, t.upadesha))
            case ReplaceTerm(index=i, term=t):
                sig.append(("replace_term", _term_key(state, i), t.upadesha))
            case Ekadesha(left=l, right=r, sounds=new):
                lt, rt = state.terms[l], state.terms[r]
                sig.append(("ekadesha", lt.antya, rt.adi, tuple(s.char for s in new)))
    return tuple(sig)


def _matching_site(state: State, cand: Candidate, signature: tuple) -> Site | None:
    for site in cand.rule.find(state):
        if edit_signature(state, cand.rule.rewrite(state, site)) == signature:
            return site
    return None


def still_applies(state: State, x: Candidate, after: Candidate) -> bool:
    """Does x still make the same change once ``after`` has applied?"""
    sig = edit_signature(state, x.rule.rewrite(state, x.site))
    s2 = apply_edit(state, after.rule.rewrite(state, after.site))
    return _matching_site(s2, x, sig) is not None


def then(state: State, first: Candidate, second: Candidate) -> State:
    """Apply ``first``, then ``second`` if it still applies (at the matching site, else its first site)."""
    sig = edit_signature(state, second.rule.rewrite(state, second.site))
    s1 = apply_edit(state, first.rule.rewrite(state, first.site))
    site = _matching_site(s1, second, sig)
    if site is None:
        sites = second.rule.find(s1)
        site = sites[0] if sites else None
    return s1 if site is None else apply_edit(s1, second.rule.rewrite(s1, site))


def _site_terms(site: Site) -> frozenset[int]:
    return frozenset(sp.term for sp in site.spans)


class LocalResolver:
    def choose(self, state: State, candidates: Sequence[Candidate], rules: Sequence[Rule]) -> Choice | None:
        losers: list[Loser] = []
        remaining: list[Candidate] = []
        for c in candidates:
            blocker = blocked_by(state, c, rules)
            if blocker is None:
                remaining.append(c)
            else:
                losers.append(Loser(c.rule.id, f"blocked by {blocker}"))

        # Para (1.4.2), restricted to conflicting saṃjñās in the ekasaṃjñā section.
        for a in list(remaining):
            for b in list(remaining):
                if (a is not b and a in remaining and b in remaining
                        and a.rule.assigns and b.rule.assigns and a.rule.assigns != b.rule.assigns
                        and a.rule.in_ekasamjna and b.rule.in_ekasamjna
                        and _site_terms(a.site) & _site_terms(b.site) and a.rule.key < b.rule.key):
                    remaining.remove(a)
                    losers.append(Loser(a.rule.id, f"para: {b.rule.id} comes later in the ekasaṃjñā section (1.4.2)"))

        if not remaining:
            return None
        if len(remaining) == 1:
            return Choice(remaining[0], tuple(losers))

        # Nitya: X dominates Y if X survives Y but Y does not survive X.
        dominated_by: dict[int, Candidate] = {}
        for i, x in enumerate(remaining):
            for j, y in enumerate(remaining):
                if i != j and j not in dominated_by and still_applies(state, x, y) and not still_applies(state, y, x):
                    dominated_by[j] = x
        undominated = [c for k, c in enumerate(remaining) if k not in dominated_by]
        for k, x in dominated_by.items():
            losers.append(Loser(remaining[k].rule.id, f"deferred: {x.rule.id} is nitya"))
        if not undominated:  # cyclic domination; treat all as tied
            undominated = remaining

        undominated.sort(key=lambda c: (c.rule.key, [(sp.term, sp.start) for sp in c.site.spans]))
        first = undominated[0]
        for other in undominated[1:]:
            a, b = then(state, first, other), then(state, other, first)
            if a != b:
                raise UnresolvedConflict((first.rule.id, other.rule.id), (first.site, other.site),
                                         (state_text(a), state_text(b)))
        return Choice(first, tuple(losers))
