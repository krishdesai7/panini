"""Vowel sandhi between terms inside the word (6.1.77 ff.)."""

from __future__ import annotations

from panini.edits import ReplaceSounds
from panini.edits import Ekadesha
from collections.abc import Callable, Iterator

from panini.edits import DeleteSounds, Ekadesha, ReplaceSounds
from panini.model import Site, Sound, Span, State, TermKind
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
                 describe: str, word_internal: bool = False, **kw) -> Rule:
    def find(st: State) -> list[Site]:
        return [_site(st, l, r) for l, r, x, y in junctions(st) if cond(x, y)
                and not (word_internal and "pada" in st.terms[l].tags)]

    def rewrite(st: State, site: Site) -> tuple[Ekadesha]:
        l, r = site.spans[0].term, site.spans[1].term
        x, y = st.terms[l].sounds[-1].char, st.terms[r].sounds[0].char
        return (Ekadesha(l, r, _sounds(result(x, y)), rule_id),)

    def note(st: State, site: Site) -> str:
        l, r = site.spans[0].term, site.spans[1].term
        x, y = st.terms[l].sounds[-1].char, st.terms[r].sounds[0].char
        return f"{slp1_to_iast(x)} + {slp1_to_iast(y)} → {slp1_to_iast(result(x, y))} ({describe})"

    return Rule(rule_id, find, rewrite, note=note, merge=lambda x, y: result(x, y) if cond(x, y) else None, **kw)


# 6.1.78 eco 'yavāyāvaḥ (not a single substitute: e → ay etc. before a vowel)
def _find_6178(st: State) -> list[Site]:
    return [_site(st, l, r) for l, r, x, y in junctions(st) if x in EC and is_vowel(y)]


def _rewrite_6178(st: State, site: Site) -> tuple[ReplaceSounds]:
    sp = site.spans[0]
    x = st.terms[sp.term].sounds[sp.start].char
    return (ReplaceSounds(sp.term, sp.start, sp.end, _sounds(_AYADI[x])),)


R_6_1_78 = Rule("6.1.78", _find_6178, _rewrite_6178,
                note=lambda st, site: f"{slp1_to_iast(st.terms[site.spans[0].term].sounds[-1].char)} before a vowel "
                f"→ {slp1_to_iast(_AYADI[st.terms[site.spans[0].term].sounds[-1].char])}")

# 6.1.87 ād guṇaḥ
R_6_1_87 = _sandhi_rule("6.1.87", lambda x, y: x in "aA" and is_vowel(y), lambda x, y: guna(y),
                        "a and a following vowel are replaced by {full grade|guṇa}")
# 6.1.88 vṛddhir eci
R_6_1_88 = _sandhi_rule("6.1.88", lambda x, y: x in "aA" and y in EC, lambda x, y: vrddhi(y),
                        "a and a following e/o/ai/au are replaced by {lengthened grade|vṛddhi}", blocks=("6.1.87",))
# 6.1.97 ato guṇe — its domain (short a + a/e/o) lies inside 6.1.101 (a+a) ∪ 6.1.88 (a+e/o)
# ∪ 6.1.87, so it collectively blocks all three (Kiparsky, Architecture §1.4.2, (23) and (32)).
R_6_1_97 = _sandhi_rule("6.1.97", lambda x, y: x == "a" and y in "aeo", lambda x, y: y,
                        "short a and a following {full-grade|guṇa} vowel are replaced by the second",
                        word_internal=True,  # apadāntāt (from 6.1.96): not at the end of a word
                        blocks=("6.1.87", "6.1.88", "6.1.101"))
# 6.1.101 akaḥ savarṇe dīrghaḥ
R_6_1_101 = _sandhi_rule("6.1.101", lambda x, y: x in AK and is_vowel(y) and is_savarna(x, y),
                         lambda x, y: dirgha(x), "a vowel and a like vowel are replaced by the long vowel",
                         blocks=("6.1.87",))

RULES = (R_6_1_78, R_6_1_87, R_6_1_88, R_6_1_97, R_6_1_101)


# 6.1.66 lopo vyor vali — not the initial v/y of a root as taught (vacanasāmarthya): reciting
# vraj, vraṇ with a v that 6.1.66 always deleted would be pointless. Vidyut 0.4 makes the same
# exception (ac_sandhi.rs, try_lopo_vyor_vali: "otherwise roots like vraj would be vyartha").
VAL = pratyahara("val")


def _word(st: State) -> list[tuple[int, int, str]]:
    return [(i, k, s.char) for i, t in enumerate(st.terms) for k, s in enumerate(t.sounds)]


def _root_initial(st: State, i: int, k: int) -> bool:
    """The sound the root begins with as taught (only markers, such as ṭu, before it)."""
    t = st.terms[i]
    return t.kind is TermKind.ROOT and t.sounds[k].upos is not None and all(s.it for s in t.sounds[:k])


def _candidates_6166(st: State) -> list[tuple[int, int]]:
    w = _word(st)
    return [(i, k) for (i, k, c), (_, _, nxt) in zip(w, w[1:]) if c in "yv" and nxt in VAL]


def _find_6166(st: State) -> list[Site]:
    return [Site.at(i, k) for i, k in _candidates_6166(st) if not _root_initial(st, i, k)]


def _near_6166(st: State) -> str | None:
    for i, k in _candidates_6166(st):
        if _root_initial(st, i, k):
            c = slp1_to_iast(st.terms[i].sounds[k].char)
            return (f"6.1.66 (y/v before a consonant other than y is deleted) is not applied to the {c} "
                    f"that begins the root: teaching the root with that {c} would be pointless "
                    "if the rule always deleted it")
    return None


R_6_1_66 = Rule("6.1.66", _find_6166,
                lambda st, site: (DeleteSounds(site.spans[0].term, (site.spans[0].start,)),),
                near_miss=_near_6166,
                note=lambda st, site: f"{slp1_to_iast(st.terms[site.spans[0].term].sounds[site.spans[0].start].char)}"
                " before a consonant other than y is deleted")

RULES = (*RULES, R_6_1_66)


# 6.1.90 āṭaś ca
def _find_6190(st: State) -> list[Site]:
    return [_site(st, l, r) for l, r, x, y in junctions(st)
            if st.terms[l].upadesha == "Aw" and x == "A" and is_vowel(y)]


R_6_1_90 = Rule("6.1.90", _find_6190,
                lambda st, site: (Ekadesha(site.spans[0].term, site.spans[1].term,
                                           _sounds(vrddhi(st.terms[site.spans[1].term].sounds[0].char)), "6.1.90"),),
                merge=lambda x, y: vrddhi(y) if x == "A" and is_vowel(y) else None,
                blocks=("6.1.87", "6.1.88", "6.1.101"),
                note=lambda st, site: f"the augment ā and {slp1_to_iast(st.terms[site.spans[1].term].sounds[0].char)} "
                f"→ {slp1_to_iast(vrddhi(st.terms[site.spans[1].term].sounds[0].char))} ({{lengthened grade|vṛddhi}})")

RULES = (*RULES, R_6_1_90)
