"""Edits: the changes a rule makes, as data, applied by the engine.

Keeping edits as data (rather than letting rules mutate state) makes it
possible to apply two rules to the same input simultaneously, which the
slice-2 resolver needs to evaluate siddha relations.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace

from panini.model import Sound, State, Term


class EditConflict(Exception):
    """Two simultaneous edits touch the same material."""


@dataclass(frozen=True)
class AddTags:
    term: int
    tags: frozenset[str]


@dataclass(frozen=True)
class MarkIt:
    term: int
    positions: tuple[int, ...]
    markers: frozenset[str]


@dataclass(frozen=True)
class DeleteSounds:
    term: int
    positions: tuple[int, ...]


@dataclass(frozen=True)
class ReplaceSounds:
    term: int
    start: int
    end: int
    sounds: tuple[Sound, ...]


@dataclass(frozen=True)
class InsertSounds:
    term: int
    at: int
    sounds: tuple[Sound, ...]


@dataclass(frozen=True)
class InsertTerm:
    index: int
    term: Term


@dataclass(frozen=True)
class ReplaceTerm:
    index: int
    term: Term


@dataclass(frozen=True)
class Ekadesha:
    """A single substitute for the last sound of ``left`` and the first of ``right``.

    The substitute is stored at the end of ``left`` and the first sound of
    ``right`` is removed (6.1.84 ekaḥ pūrvaparayoḥ; 6.1.85 antādivac ca lets
    it count as the end of one and the beginning of the other).
    """

    left: int
    right: int
    sounds: tuple[Sound, ...]
    rule: str | None = None  # the rule making it: recorded on the substitute so it can be recomputed


type Op = AddTags | MarkIt | DeleteSounds | ReplaceSounds | InsertSounds | InsertTerm | ReplaceTerm | Ekadesha
type Edit = tuple[Op, ...]


VIKRTA = "vikrta"  # tag: the term's sounds were changed beyond deleting markers
EKADESHA_START = "ekādeśa-start"  # tag: this term begins with the single substitute stored on its left


def _set_term(terms: list[Term], i: int, term: Term) -> None:
    terms[i] = term


def _vikrta(term: Term) -> Term:
    return term if VIKRTA in term.tags else replace(term, tags=term.tags | {VIKRTA})


def _apply_op(terms: list[Term], op: Op) -> None:
    match op:
        case AddTags(term=i, tags=tags):
            _set_term(terms, i, replace(terms[i], tags=terms[i].tags | tags))
        case MarkIt(term=i, positions=pos, markers=markers):
            t = terms[i]
            sounds = tuple(replace(s, it=True) if k in pos else s for k, s in enumerate(t.sounds))
            _set_term(terms, i, replace(t, sounds=sounds, markers=t.markers | markers))
        case DeleteSounds(term=i, positions=pos):
            t = terms[i]
            new_t = replace(t, sounds=tuple(s for k, s in enumerate(t.sounds) if k not in pos))
            if not all(t.sounds[k].it for k in pos if k < len(t.sounds)):
                new_t = _vikrta(new_t)
            _set_term(terms, i, new_t)
        case ReplaceSounds(term=i, start=a, end=b, sounds=new):
            t = terms[i]
            _set_term(terms, i, _vikrta(replace(t, sounds=t.sounds[:a] + tuple(new) + t.sounds[b:])))
        case InsertSounds(term=i, at=a, sounds=new):
            t = terms[i]
            _set_term(terms, i, _vikrta(replace(t, sounds=t.sounds[:a] + tuple(new) + t.sounds[a:])))
        case InsertTerm(index=i, term=term):
            terms.insert(i, term)
        case ReplaceTerm(index=i, term=term):
            _set_term(terms, i, term)
        case Ekadesha(left=l, right=r, sounds=new, rule=rule):
            lt, rt = terms[l], terms[r]
            inputs = (lt.sounds[-1].char, rt.sounds[0].char)
            flagged = tuple(replace(s, ekadesha=True, ekadesha_rule=rule, ekadesha_inputs=inputs) for s in new)
            _set_term(terms, l, _vikrta(replace(lt, sounds=lt.sounds[:-1] + flagged)))
            right = _vikrta(replace(rt, sounds=rt.sounds[1:]))
            _set_term(terms, r, replace(right, tags=right.tags | {EKADESHA_START}))


def apply_edit(state: State, edit: Edit) -> State:
    """Apply the ops of one edit in order."""
    terms = list(state.terms)
    for op in edit:
        _apply_op(terms, op)
    return replace(state, terms=tuple(terms))


def _footprint(state: State, op: Op) -> set[tuple]:
    """The material an op touches: ("s", term, pos) for sounds, ("t", index) for term slots."""
    match op:
        case AddTags(term=i):
            return {("tags", i)}
        case MarkIt(term=i, positions=pos) | DeleteSounds(term=i, positions=pos):
            return {("s", i, p) for p in pos}
        case ReplaceSounds(term=i, start=a, end=b):
            return {("s", i, p) for p in range(a, max(b, a + 1))}
        case InsertSounds(term=i, at=a):
            return {("s", i, a)}
        case InsertTerm(index=i) | ReplaceTerm(index=i):
            return {("t", i)}
        case Ekadesha(left=l, right=r):
            return {("s", l, len(state.terms[l].sounds) - 1), ("s", r, 0)}


def _sort_key(op: Op) -> tuple[int, int]:
    """Descending application order: later terms and later positions first."""
    match op:
        case InsertTerm(index=i) | ReplaceTerm(index=i):
            return (i, 10**6)
        case Ekadesha(left=l):
            return (l, 10**6 - 1)
        case ReplaceSounds(term=i, start=a) | InsertSounds(term=i, at=a):
            return (i, a)
        case MarkIt(term=i, positions=p) | DeleteSounds(term=i, positions=p):
            return (i, max(p, default=0))
        case AddTags(term=i):
            return (i, -1)


def apply_simultaneous(state: State, edits: Sequence[Edit]) -> State:
    """Apply several edits to the same input as if at once.

    Raises EditConflict when two edits touch the same sound or term slot.
    """
    seen: set[tuple] = set()
    for edit in edits:
        fp: set[tuple] = set()
        for op in edit:
            fp |= _footprint(state, op)
        if fp & seen:
            raise EditConflict(f"overlapping edits at {sorted(fp & seen)}")
        seen |= fp
    ops = [op for edit in edits for op in edit]
    terms = list(state.terms)
    for op in sorted(ops, key=_sort_key, reverse=True):
        _apply_op(terms, op)
    return replace(state, terms=tuple(terms))
