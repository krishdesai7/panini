"""Explicit meta-rules consulted by operational rules.

1.1.56 sthānivad ādeśo 'nalvidhau: a substitute is treated like what it
replaces, except for rules conditioned by a single sound (al-vidhi). Here the
substitute keeps a link to the replaced term; tags and markers are looked up
through it (Term.has_tag / Term.has_marker). Sound-conditioned rules read the
current sounds, so the al-vidhi exception holds automatically.

1.1.46 ādyantau ṭakitau: an augment marked ṭ goes at the beginning of what it
is added to, one marked k at the end.
"""

from __future__ import annotations

from panini.edits import Edit, InsertSounds, InsertTerm
from panini.model import Sound, State, Term, TermKind
from panini.translit import slp1_to_iast

_MARKER_NAMES = {"N": "ṅit", "k": "kit", "p": "pit", "w": "ṭit", "S": "śit", "Y": "ñit"}


def substitute_term(old: Term, kind: TermKind, upadesha: str) -> Term:
    """Replace ``old`` by a new upadeśa that inherits its properties (1.1.56)."""
    new = Term.from_upadesha(kind, upadesha)
    return Term(new.kind, new.upadesha, new.sounds, new.tags, frozenset(), replaced=old)


def sthanivat_note(term: Term) -> str | None:
    """Describe what a substitute inherits, e.g. 'ti counts as ṅit via 1.1.56 (it replaced l)'."""
    if term.replaced is None:
        return None
    inherited = sorted(_MARKER_NAMES[m] for m in term.replaced.markers if m in _MARKER_NAMES)
    old = slp1_to_iast(term.replaced.text or term.replaced.upadesha[:1])
    new = slp1_to_iast(term.text)
    if inherited:
        return f"{new} counts as {', '.join(inherited)} via 1.1.56 (it replaced {old})"
    return f"{new} inherits the properties of {old} via 1.1.56"


def augment_edit(state: State, target: int, augment: Term) -> Edit:
    """Place a ṭit augment before ``target`` or a kit augment after it (1.1.46)."""
    if augment.has_marker("w"):
        return (InsertTerm(target, augment),)
    if augment.has_marker("k"):
        return (InsertTerm(target + 1, augment),)
    raise ValueError(f"augment {augment.upadesha} is neither ṭit nor kit")


def augment_in_term_edit(state: State, term: int, after_pos: int, sounds: tuple[Sound, ...]) -> Edit:
    """Insert a kit augment's sounds right after a sound inside a term (e.g. tuk, 6.1.73)."""
    tagged = tuple(Sound(s.char, agama=True) for s in sounds)
    return (InsertSounds(term, after_pos + 1, tagged),)
