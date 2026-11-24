"""Vowel sandhi between terms inside the word (6.1.77 ff.)."""

from __future__ import annotations

from collections.abc import Callable, Iterator

from panini.edits import Ekadesha, ReplaceSounds
from panini.model import Site, Sound, Span, State
from panini.rules.base import Rule
from panini.sounds import dirgha, guna, is_savarna, is_vowel, pratyahara, vrddhi
from panini.translit import slp1_to_iast

EC = pratyahara("ec")
AK = pratyahara("ak")
_AYADI = {"e": "ay", "o": "av", "E": "Ay", "O": "Av"}


def _sounds(text: str) -> tuple[Sound, ...]:
    return tuple(Sound(c) for c in text)


def junctions(st: State) -> Iterator[tuple[int, int, str, str]]:
    """(left term, right term, left final, right initial) for adjacent non-empty terms."""
    nonempty = [i for i, t in enumerate(st.terms) if t.sounds]
    for a, b in zip(nonempty, nonempty[1:]):
        yield a, b, st.terms[a].sounds[-1].char, st.terms[b].sounds[0].char


def _site(st: State, l: int, r: int) -> Site:
    n = len(st.terms[l].sounds)
    return Site((Span(l, n - 1, n), Span(r, 0, 1)))


def _sandhi_rule(rule_id: str, cond: Callable[[str, str], bool], result: Callable[[str, str], str],
                 describe: str, **kw) -> Rule:
    def find(st: State) -> list[Site]:
        return [_site(st, l, r) for l, r, x, y in junctions(st) if cond(x, y)]

    def rewrite(st: State, site: Site):
        l, r = site.spans[0].term, site.spans[1].term
        x, y = st.terms[l].sounds[-1].char, st.terms[r].sounds[0].char
        return (Ekadesha(l, r, _sounds(result(x, y))),)

    def note(st: State, site: Site) -> str:
        l, r = site.spans[0].term, site.spans[1].term
        x, y = st.terms[l].sounds[-1].char, st.terms[r].sounds[0].char
        return f"{slp1_to_iast(x)} + {slp1_to_iast(y)} → {slp1_to_iast(result(x, y))} ({describe})"

    return Rule(rule_id, find, rewrite, note=note, **kw)


# 6.1.78 eco 'yavāyāvaḥ (not a single substitute: e → ay etc. before a vowel)
def _find_6178(st: State) -> list[Site]:
    return [_site(st, l, r) for l, r, x, y in junctions(st) if x in EC and is_vowel(y)]


def _rewrite_6178(st: State, site: Site):
    sp = site.spans[0]
    x = st.terms[sp.term].sounds[sp.start].char
    return (ReplaceSounds(sp.term, sp.start, sp.end, _sounds(_AYADI[x])),)


R_6_1_78 = Rule("6.1.78", _find_6178, _rewrite_6178,
                note=lambda st, site: f"{slp1_to_iast(st.terms[site.spans[0].term].sounds[-1].char)} before a vowel "
                f"→ {slp1_to_iast(_AYADI[st.terms[site.spans[0].term].sounds[-1].char])}")

# 6.1.87 ād guṇaḥ
R_6_1_87 = _sandhi_rule("6.1.87", lambda x, y: x in "aA" and is_vowel(y), lambda x, y: guna(y),
                        "a and a following vowel are replaced by guṇa")
# 6.1.88 vṛddhir eci
R_6_1_88 = _sandhi_rule("6.1.88", lambda x, y: x in "aA" and y in EC, lambda x, y: vrddhi(y),
                        "a and a following e/o/ai/au are replaced by vṛddhi", blocks=("6.1.87",))
# 6.1.97 ato guṇe — collectively blocks 6.1.87 and 6.1.101 (Kiparsky, Architecture §1.4.2)
R_6_1_97 = _sandhi_rule("6.1.97", lambda x, y: x == "a" and y in "aeo", lambda x, y: y,
                        "short a and a following guṇa vowel are replaced by the second", blocks=("6.1.87", "6.1.101"))
# 6.1.101 akaḥ savarṇe dīrghaḥ
R_6_1_101 = _sandhi_rule("6.1.101", lambda x, y: x in AK and is_vowel(y) and is_savarna(x, y),
                         lambda x, y: dirgha(x), "a vowel and a like vowel are replaced by the long vowel",
                         blocks=("6.1.87",))

RULES = (R_6_1_78, R_6_1_87, R_6_1_88, R_6_1_97, R_6_1_101)
