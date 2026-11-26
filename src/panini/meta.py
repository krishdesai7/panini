"""Explicit meta-rules consulted by operational rules.

1.1.56 sthānivad ādeśo 'nalvidhau: a substitute is treated like what it
replaces, except for rules conditioned by a single sound (al-vidhi). Here the
substitute keeps a link to the replaced term; tags and markers are looked up
through it (Term.has_tag / Term.has_marker). Sound-conditioned rules read the
current sounds, so the al-vidhi exception holds automatically.

1.1.46 ādyantau ṭakitau: an augment marked ṭ goes at the beginning of what it
is added to, one marked k at the end.

1.1.47 midaco 'ntyāt paraḥ: an augment marked m goes right after the last
vowel of what it is added to.
"""

from __future__ import annotations

lazy from collections.abc import Callable

from panini.edits import EKADESHA_START, Edit, InsertSounds, InsertTerm, ReplaceSounds
from panini.model import Sound, State, Term, TermKind
from panini.sounds import is_vowel
from panini.translit import slp1_to_iast

_MARKER_NAMES = {
    "N": "marked ṅ",
    "k": "marked k",
    "p": "marked p",
    "w": "marked ṭ",
    "S": "marked ś",
    "Y": "marked ñ",
}


def substitute_term(old: Term, kind: TermKind, upadesha: str) -> Term:
    """Replace ``old`` by a new upadeśa that inherits its properties (1.1.56)."""
    new = Term.from_upadesha(kind, upadesha)
    return Term(new.kind, new.upadesha, new.sounds, new.tags, frozenset(), replaced=old)


def sthanivat_note(term: Term) -> str | None:
    """Describe what a substitute inherits, e.g. 'ti counts as ṅit via 1.1.56 (it replaced l)'."""
    if term.replaced is None:
        return None
    inherited = sorted(
        _MARKER_NAMES[m] for m in term.replaced.markers if m in _MARKER_NAMES
    )
    old = slp1_to_iast(term.replaced.text or term.replaced.upadesha[:1])
    new = slp1_to_iast(term.text)
    if inherited:
        return f"{new} counts as {', '.join(inherited)} via 1.1.56 (it replaced {old})"
    return f"{new} inherits the properties of {old} via 1.1.56"


def augment_edit(state: State, target: int, augment: Term) -> Edit:
    """Place a ṭit augment before ``target`` or a kit augment after it (1.1.46).

    1.1.46 refers to the augment as taught, so the marker is read from its upadeśa
    when the it-rules have not yet run on it.
    """
    final = augment.upadesha.rstrip("~")[-1:]
    if augment.has_marker("w") or final == "w":
        return (InsertTerm(target, augment),)
    if augment.has_marker("k") or final == "k":
        return (InsertTerm(target + 1, augment),)
    raise ValueError(f"augment {augment.upadesha} is neither ṭit nor kit")


def augment_in_term_edit(
    state: State, term: int, after_pos: int, sounds: tuple[Sound, ...]
) -> Edit:
    """Insert a kit augment's sounds right after a sound inside a term (e.g. tuk, 6.1.73)."""
    tagged = tuple(Sound(s.char, agama=True) for s in sounds)
    return (InsertSounds(term, after_pos + 1, tagged),)


def mit_position(state: State, term: int) -> int | None:
    """Where 1.1.47 puts an augment marked m in a term: the index right after its last vowel.

    Vowels marked as it do not count. A single substitute stored at the end of the term on
    the left counts as this term's first sound too (6.1.85), so a term whose only vowel went
    into it (ā + andat, laṅ of and) takes the augment at its start. An augment's sounds written
    after that substitute (tuk, 6.1.75: ā t + ch) belong to neither term's own sounds, so they
    are passed over when looking for it.
    """
    t = state.terms[term]
    own = [k for k, s in enumerate(t.sounds) if is_vowel(s.char) and not s.it]
    if own:
        return own[-1] + 1
    left = next((u for u in reversed(state.terms[:term]) if u.sounds), None)
    tail = (
        next((s for s in reversed(left.sounds) if not s.agama), None)
        if left is not None
        else None
    )
    if EKADESHA_START in t.tags and tail is not None and tail.ekadesha:
        return 0
    return None


def mit_augment_edit(state: State, term: int, sounds: tuple[Sound, ...]) -> Edit:
    """Insert a mit augment's sounds right after the last vowel of a term (e.g. num, 7.1.58)."""
    pos = mit_position(state, term)
    if pos is None:
        raise ValueError(
            f"{state.terms[term].text} has no vowel for a mit augment to follow"
        )
    tagged = tuple(Sound(s.char, agama=True) for s in sounds)
    return (InsertSounds(term, pos, tagged),)


def _ekadesha_tail(term: Term) -> int:
    """How many sounds at the end of a term are one recorded ekādeśa substitute."""
    k = 0
    for s in reversed(term.sounds):
        if not (s.ekadesha and s.ekadesha_rule):
            break
        k += 1
    return k


def absorbed_ekadesha(state: State, term: int) -> list[tuple[str, str, str]]:
    """The ekādeśa substitute that swallowed the first sound of this term, as [(rule, left sound,
    right sound)]: 6.1.85 antādivat lets such a substitute count as part of this term as well as of
    the neighbour it is stored with."""
    if EKADESHA_START in state.terms[term].tags:
        left = next((u for u in reversed(state.terms[:term]) if u.sounds), None)
        if left is not None and _ekadesha_tail(left):
            s = left.sounds[-1]
            return [(s.ekadesha_rule, *s.ekadesha_inputs)]
    return []


def substitution_edit(
    state: State,
    term: int,
    stem: str,
    rule_lookup: Callable[[str], object] | None = None,
) -> Edit:
    """Replace a whole term by ``stem`` (a substitution for the sthānin, 1.1.56), taking its place in
    the ekādeśa that had absorbed its first sound: the substitute is an input of that ekādeśa, so
    the rule that made it is applied again, to the stem's first sound instead of the old one.
    E.g. ā + ṛ → ār (6.1.90); ṛ replaced by ṛccha: ā + ṛ → ār again, then ccha.

    Only the start of the term is handled. An ekādeśa at its end (śap's a absorbed into a
    root's a) never has to be undone: a substitution of the whole term is nitya, so the resolver
    lets it go first."""
    if rule_lookup is None:
        from panini.rules import get_rule

        rule_lookup = get_rule
    t = state.terms[term]
    chars = list(stem)
    edits: list = []
    if absorbed := absorbed_ekadesha(state, term):
        rule_id, x, _ = absorbed[0]
        out = rule_lookup(rule_id).merge(x, chars[0])
        if out is None:
            raise ValueError(
                f"{rule_id} does not apply to {x} + {chars[0]}, so the substitute cannot take its place"
            )
        left_i = next(i for i in range(term - 1, -1, -1) if state.terms[i].sounds)
        lt, k = state.terms[left_i], _ekadesha_tail(state.terms[left_i])
        new = tuple(
            Sound(
                c, ekadesha=True, ekadesha_rule=rule_id, ekadesha_inputs=(x, chars[0])
            )
            for c in out
        )
        edits.append(ReplaceSounds(left_i, len(lt.sounds) - k, len(lt.sounds), new))
        chars.pop(0)
    edits.append(ReplaceSounds(term, 0, len(t.sounds), tuple(Sound(c) for c in chars)))
    return tuple(edits)
