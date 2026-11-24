"""Markers (it): 1.3.1–1.3.9, and root-initial ṣ/ṇ (6.1.64–65)."""

from __future__ import annotations

from panini.edits import AddTags, DeleteSounds, MarkIt, ReplaceSounds
from panini.model import Site, Sound, State, TermKind
from panini.rules.base import Rule, is_pratyaya
from panini.sounds import is_vowel, pratyahara
from panini.translit import slp1_to_iast

HAL = pratyahara("hal")
TU_S_M = frozenset("tTdDnsm")  # 1.3.4: tu (t th d dh n), s, m
CU, TU, KU = pratyahara("cu"), pratyahara("wu"), frozenset("kKgGN")


def _mark(term_i: int, pos: tuple[int, ...], letters: str):
    return (MarkIt(term_i, pos, frozenset({letters})),)


# 1.3.1 bhūvādayo dhātavaḥ
def _find_131(st: State) -> list[Site]:
    return [Site.term(i) for i, t in enumerate(st.terms) if t.kind is TermKind.ROOT and "dhātu" not in t.tags]


R_1_3_1 = Rule("1.3.1", _find_131, lambda st, site: (AddTags(site.spans[0].term, frozenset({"dhātu"})),),
               note=lambda st, site: f"‘{slp1_to_iast(st.terms[site.spans[0].term].upadesha)}’ is a root (dhātu)")


# 1.3.2 upadeśe 'janunāsika it
def _find_132(st: State) -> list[Site]:
    return [Site.at(i, k) for i, t in enumerate(st.terms) for k, s in enumerate(t.sounds)
            if s.nasal and not s.it and is_vowel(s.char)]


R_1_3_2 = Rule("1.3.2", _find_132,
               lambda st, site: _mark(site.spans[0].term, (site.spans[0].start,),
                                      st.terms[site.spans[0].term].sounds[site.spans[0].start].char),
               note=lambda st, site: "the nasal vowel "
               f"{slp1_to_iast(st.terms[site.spans[0].term].sounds[site.spans[0].start].char)}~ is a marker")


# 1.3.3 hal antyam
def _find_133(st: State) -> list[Site]:
    out = []
    for i, t in enumerate(st.terms):
        k = t.upadesha_final()
        if k is not None and t.sounds[k].char in HAL and not t.sounds[k].it:
            out.append(Site.at(i, k))
    return out


def _note_final(st: State, site: Site) -> str:
    sp = site.spans[0]
    return f"final {slp1_to_iast(st.terms[sp.term].sounds[sp.start].char)} is a marker"


R_1_3_3 = Rule("1.3.3", _find_133,
               lambda st, site: _mark(site.spans[0].term, (site.spans[0].start,),
                                      st.terms[site.spans[0].term].sounds[site.spans[0].start].char),
               note=_note_final)


# 1.3.4 na vibhaktau tusmāḥ (a niṣedha: blocks 1.3.3, changes nothing itself)
def _find_134(st: State) -> list[Site]:
    out = []
    for i, t in enumerate(st.terms):
        k = t.upadesha_final()
        if t.kind is TermKind.TIN and k is not None and t.sounds[k].char in TU_S_M and not t.sounds[k].it:
            out.append(Site.at(i, k))
    return out


R_1_3_4 = Rule("1.3.4", _find_134, lambda st, site: (), blocks=("1.3.3",),
               note=lambda st, site: "the final "
               f"{slp1_to_iast(st.terms[site.spans[0].term].sounds[site.spans[0].start].char)}"
               " of a verb ending (vibhakti, 1.4.104) is not a marker")


# 1.3.5 ādir ñiṭuḍavaḥ
def _find_135(st: State) -> list[Site]:
    out = []
    for i, t in enumerate(st.terms):
        if t.kind is TermKind.ROOT and len(t.sounds) > 2 and t.sounds[0].upos == 0 and t.sounds[1].upos == 1:
            first = t.sounds[0].char + t.sounds[1].char
            if first in ("Yi", "wu", "qu") and not t.sounds[0].it:
                out.append(Site.at(i, 0, 2))
    return out


R_1_3_5 = Rule("1.3.5", _find_135,
               lambda st, site: _mark(site.spans[0].term, (0, 1),
                                      st.terms[site.spans[0].term].sounds[0].char
                                      + st.terms[site.spans[0].term].sounds[1].char),
               note=lambda st, site: "initial "
               f"{slp1_to_iast(st.terms[site.spans[0].term].sounds[0].char + st.terms[site.spans[0].term].sounds[1].char)}"
               " of a root is a marker")


def _initial_unmarked_pratyaya(st: State, letters: frozenset[str]) -> list[tuple[int, str]]:
    return [(i, t.sounds[0].char) for i, t in enumerate(st.terms)
            if is_pratyaya(t) and t.sounds and t.sounds[0].upos == 0 and not t.sounds[0].it
            and t.sounds[0].char in letters]


# 1.3.7 cuṭū — amendment A3: the jh of jhi/jha is not marked (7.1.3 needs it).
def _find_137(st: State) -> list[Site]:
    return [Site.at(i, 0) for i, c in _initial_unmarked_pratyaya(st, CU | TU)
            if not (st.terms[i].kind is TermKind.TIN and c == "J")]


def _near_137(st: State) -> str | None:
    if any(st.terms[i].kind is TermKind.TIN for i, c in _initial_unmarked_pratyaya(st, frozenset("J"))):
        return ("1.3.7 (initial cu/ṭu of an affix is a marker) is not applied to the jh of the ending: "
                "7.1.3 jho 'ntaḥ replaces that jh, which it could not do if jh were a marker")
    return None


R_1_3_7 = Rule("1.3.7", _find_137,
               lambda st, site: _mark(site.spans[0].term, (0,), st.terms[site.spans[0].term].sounds[0].char),
               near_miss=_near_137,
               note=lambda st, site: f"initial {slp1_to_iast(st.terms[site.spans[0].term].sounds[0].char)} "
               "of an affix is a marker")


# 1.3.8 laśakvataddhite — the l of a lakāra is not marked (3.4.77 lasya needs it).
def _find_138(st: State) -> list[Site]:
    return [Site.at(i, 0) for i, c in _initial_unmarked_pratyaya(st, frozenset("lS") | KU)
            if st.terms[i].kind is not TermKind.LA]


def _near_138(st: State) -> str | None:
    if any(st.terms[i].kind is TermKind.LA for i, _ in _initial_unmarked_pratyaya(st, frozenset("l"))):
        return ("1.3.8 (initial l of an affix is a marker) is not applied to the l of laṭ/laṅ: "
                "3.4.77 lasya ‘in place of l’ refers to that l, so it must remain")
    return None


R_1_3_8 = Rule("1.3.8", _find_138,
               lambda st, site: _mark(site.spans[0].term, (0,), st.terms[site.spans[0].term].sounds[0].char),
               near_miss=_near_138,
               note=lambda st, site: f"initial {slp1_to_iast(st.terms[site.spans[0].term].sounds[0].char)} "
               "of an affix is a marker")


# 1.3.9 tasya lopaḥ
def _find_139(st: State) -> list[Site]:
    return [Site.term(i) for i, t in enumerate(st.terms) if any(s.it for s in t.sounds)]


R_1_3_9 = Rule("1.3.9", _find_139,
               lambda st, site: (DeleteSounds(site.spans[0].term, tuple(
                   k for k, s in enumerate(st.terms[site.spans[0].term].sounds) if s.it)),),
               note=lambda st, site: "markers are deleted")


# 6.1.64 dhātvādeḥ ṣaḥ saḥ / 6.1.65 ṇo naḥ
def _root_initial(old: str):
    def find(st: State) -> list[Site]:
        return [Site.at(i, 0) for i, t in enumerate(st.terms)
                if t.kind is TermKind.ROOT and "dhātu" in t.tags and t.adi == old]
    return find


R_6_1_64 = Rule("6.1.64", _root_initial("z"), lambda st, site: (ReplaceSounds(site.spans[0].term, 0, 1, (Sound("s"),)),),
                note=lambda st, site: "root-initial ṣ becomes s")
R_6_1_65 = Rule("6.1.65", _root_initial("R"), lambda st, site: (ReplaceSounds(site.spans[0].term, 0, 1, (Sound("n"),)),),
                note=lambda st, site: "root-initial ṇ becomes n")

RULES = (R_1_3_1, R_1_3_2, R_1_3_3, R_1_3_4, R_1_3_5, R_1_3_7, R_1_3_8, R_1_3_9, R_6_1_64, R_6_1_65)
