"""Changes to the person/number endings (3.4.79 ff.) and the past-tense augments."""

from __future__ import annotations

from panini.edits import AddTags, ReplaceSounds
from panini.model import Site, Sound, State, Term, TermKind
from panini.rules.base import Rule
from panini.sounds import is_vowel
from panini.translit import slp1_to_iast


def _sounds(text: str) -> tuple[Sound, ...]:
    return tuple(Sound(c) for c in text)


def _ti_start(t: Term) -> int | None:
    """Start of the ṭi: the last vowel and what follows it (1.1.64 aco 'ntyādi ṭi)."""
    return next((k for k in range(len(t.sounds) - 1, -1, -1) if is_vowel(t.sounds[k].char)), None)


def _in_tit_lakara(t: Term) -> bool:
    """The ending replaced a lakāra marked with ṭ (laṭ); known through 1.1.56."""
    return t.replaced is not None and t.replaced.has_marker("w")


# 3.4.79 ṭita ātmanepadānāṃ ṭer e
def _find_3479(st: State) -> list[Site]:
    out = []
    for i, t in enumerate(st.terms):
        if (t.kind is TermKind.TIN and t.has_tag("ātmanepada") and _in_tit_lakara(t)
                and "3.4.79" not in t.tags and (k := _ti_start(t)) is not None):
            out.append(Site.at(i, k, len(t.sounds)))
    return out


R_3_4_79 = Rule("3.4.79", _find_3479,
                lambda st, site: (ReplaceSounds(site.spans[0].term, site.spans[0].start, site.spans[0].end,
                                                (Sound("e"),)),
                                  AddTags(site.spans[0].term, frozenset({"3.4.79"}))),
                note=lambda st, site: "in laṭ (marked ṭ), the last vowel-and-after (ṭi, 1.1.64) of an ātmanepada "
                f"ending, {slp1_to_iast(''.join(s.char for s in st.terms[site.spans[0].term].sounds[site.spans[0].start:]))}, "
                "becomes e")


# 3.4.80 thāsaḥ se
def _find_3480(st: State) -> list[Site]:
    return [Site.at(i, 0, len(t.sounds)) for i, t in enumerate(st.terms)
            if t.kind is TermKind.TIN and t.text == "TAs" and _in_tit_lakara(t)]


R_3_4_80 = Rule("3.4.80", _find_3480,
                lambda st, site: (ReplaceSounds(site.spans[0].term, 0, site.spans[0].end, _sounds("se")),
                                  AddTags(site.spans[0].term, frozenset({"3.4.79"}))),
                blocks=("3.4.79",),
                note=lambda st, site: "in laṭ, the ending thās is replaced by se")

RULES = (R_3_4_79, R_3_4_80)
