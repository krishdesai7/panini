"""Changes to the person/number endings (3.4.79 ff.) and the past-tense augments."""

from __future__ import annotations

from panini.edits import VIKRTA, AddTags, DeleteSounds, ReplaceSounds, ReplaceTerm
from panini.meta import augment_edit, sthanivat_note, substitute_term
from panini.model import Site, Sound, State, Term, TermKind
from panini.rules.base import Rule
from panini.sounds import is_vowel
from panini.translit import slp1_to_iast


TER_E_DONE = "ṭer-e-done"  # the ending's final part has been dealt with (3.4.79 or 3.4.80)


def _sounds(text: str) -> tuple[Sound, ...]:
    return tuple(Sound(c) for c in text)


def _ti_start(t: Term) -> int | None:
    """Start of the ṭi: the last vowel and what follows it (1.1.64 aco 'ntyādi ṭi)."""
    return next((k for k in range(len(t.sounds) - 1, -1, -1) if is_vowel(t.sounds[k].char)), None)


def lakara_of(t: Term) -> Term | None:
    """The lakāra an ending stands in place of, following substitutions back (1.1.56)."""
    while t.replaced is not None:
        t = t.replaced
        if t.kind is TermKind.LA:
            return t
    return None


def _in_tit_lakara(t: Term) -> bool:
    """The ending replaced a lakāra marked with ṭ (laṭ). Only the lakāra's markers count,
    not the ending's own (iṭ is itself ṭit)."""
    la = lakara_of(t)
    return la is not None and la.has_marker("w")


# 3.4.79 ṭita ātmanepadānāṃ ṭer e
def _find_3479(st: State) -> list[Site]:
    out = []
    for i, t in enumerate(st.terms):
        if (t.kind is TermKind.TIN and t.has_tag("ātmanepada") and _in_tit_lakara(t)
                and TER_E_DONE not in t.tags and (k := _ti_start(t)) is not None):
            out.append(Site.at(i, k, len(t.sounds)))
    return out


R_3_4_79 = Rule("3.4.79", _find_3479,
                lambda st, site: (ReplaceSounds(site.spans[0].term, site.spans[0].start, site.spans[0].end,
                                                (Sound("e"),)),
                                  AddTags(site.spans[0].term, frozenset({TER_E_DONE}))),
                note=lambda st, site: "in laṭ (marked ṭ), the last vowel and what follows it (ṭi, 1.1.64) of a {middle|ātmanepada} "
                f"ending, {slp1_to_iast(''.join(s.char for s in st.terms[site.spans[0].term].sounds[site.spans[0].start:]))}, "
                "becomes e")


# 3.4.80 thāsaḥ se
def _find_3480(st: State) -> list[Site]:
    return [Site.at(i, 0, len(t.sounds)) for i, t in enumerate(st.terms)
            if t.kind is TermKind.TIN and t.text == "TAs" and _in_tit_lakara(t)]


R_3_4_80 = Rule("3.4.80", _find_3480,
                lambda st, site: (ReplaceSounds(site.spans[0].term, 0, site.spans[0].end, _sounds("se")),
                                  AddTags(site.spans[0].term, frozenset({TER_E_DONE}))),
                blocks=("3.4.79",),
                note=lambda st, site: "in laṭ, the ending thās is replaced by se")

RULES = (R_3_4_79, R_3_4_80)


# -- laṅ -------------------------------------------------------------------

def _in_nit_lakara(t: Term) -> bool:
    """The ending stands in place of a lakāra marked with ṅ (laṅ), known through 1.1.56.
    Only the lakāra's markers count, not the ending's own (mahiṅ is itself ṅit)."""
    la = lakara_of(t)
    return la is not None and la.has_marker("N")


def _lan_in_word(st: State) -> bool:
    return any((t.kind is TermKind.LA and t.upadesha == "la~N")
               or (t.kind is TermKind.TIN and _in_nit_lakara(t)) for t in st.terms)


def _ending_note(st: State, i: int, what: str) -> str:
    return f"{what}; {sthanivat_note(st.terms[i])}"


# 6.4.71 luṅlaṅlṛṅkṣv aḍ udāttaḥ / 6.4.72 āḍ ajādīnām
def _augment_find(vowel_initial: bool):
    def find(st: State) -> list[Site]:
        d = next((i for i, t in enumerate(st.terms) if t.kind is TermKind.ROOT), None)
        if d is None or not _lan_in_word(st) or "aṅga" not in st.terms[d].tags:
            return []
        if d > 0 and st.terms[d - 1].kind is TermKind.AGAMA:
            return []
        if vowel_initial and not is_vowel(st.terms[d].adi or ""):
            return []
        return [Site.term(d)]
    return find


def _augment_rewrite(upadesha: str):
    return lambda st, site: augment_edit(st, site.spans[0].term, Term.from_upadesha(TermKind.AGAMA, upadesha))


R_6_4_71 = Rule("6.4.71", _augment_find(False), _augment_rewrite("aw"),
                note=lambda st, site: "before laṅ, the base gets the augment aṭ; marked ṭ, it goes at the "
                "beginning (1.1.46)")
R_6_4_72 = Rule("6.4.72", _augment_find(True), _augment_rewrite("Aw"), blocks=("6.4.71",),
                note=lambda st, site: "a base beginning with a vowel gets āṭ instead; marked ṭ, it goes at the "
                "beginning (1.1.46)")


# 3.4.99 nityaṃ ṅitaḥ
def _find_3499(st: State) -> list[Site]:
    return [Site.at(i, len(t.sounds) - 1) for i, t in enumerate(st.terms)
            if t.kind is TermKind.TIN and _in_nit_lakara(t) and t.upadesha in ("vas", "mas") and t.antya == "s"]


R_3_4_99 = Rule("3.4.99", _find_3499,
                lambda st, site: (DeleteSounds(site.spans[0].term, (site.spans[0].start,)),),
                note=lambda st, site: _ending_note(st, site.spans[0].term,
                                                   "in laṅ (marked ṅ), the final s of a first-person ending is dropped"))


# 3.4.100 itaś ca
def _find_34100(st: State) -> list[Site]:
    return [Site.at(i, len(t.sounds) - 1) for i, t in enumerate(st.terms)
            if t.kind is TermKind.TIN and _in_nit_lakara(t) and t.has_tag("parasmaipada") and t.antya == "i"]


R_3_4_100 = Rule("3.4.100", _find_34100,
                 lambda st, site: (DeleteSounds(site.spans[0].term, (site.spans[0].start,)),),
                 note=lambda st, site: _ending_note(st, site.spans[0].term,
                                                    "in laṅ (marked ṅ), the final i of an {active|parasmaipada} ending is dropped"))


# 3.4.101 tasthasthamipāṃ tāṃtaṃtāmaḥ — apavāda of 3.4.100 for mip
_TAM = {"tas": "tAm", "Tas": "tam", "Ta": "ta", "mip": "am"}


def _find_34101(st: State) -> list[Site]:
    return [Site.term(i) for i, t in enumerate(st.terms)
            if t.kind is TermKind.TIN and _in_nit_lakara(t) and t.upadesha in _TAM and VIKRTA not in t.tags]


def _rewrite_34101(st: State, site: Site):
    i = site.spans[0].term
    t = st.terms[i]
    return (ReplaceTerm(i, substitute_term(t, TermKind.TIN, _TAM[t.upadesha])),)


R_3_4_101 = Rule("3.4.101", _find_34101, _rewrite_34101, blocks=("3.4.100",),
                 note=lambda st, site: _ending_note(
                     st, site.spans[0].term,
                     f"in laṅ (marked ṅ), {slp1_to_iast(st.terms[site.spans[0].term].upadesha)} is replaced by "
                     f"{slp1_to_iast(_TAM[st.terms[site.spans[0].term].upadesha])}"))

RULES = (*RULES, R_6_4_71, R_6_4_72, R_3_4_99, R_3_4_100, R_3_4_101)
