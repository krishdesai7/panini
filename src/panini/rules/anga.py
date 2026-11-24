"""Operations on the base (aṅga): guṇa, lengthening, ch-substitution, tuk, jh → ant."""

from __future__ import annotations

from panini.edits import ReplaceSounds
from panini.meta import augment_in_term_edit
from panini.model import Site, Sound, State, TermKind
from panini.rules.base import Rule, adi, is_pratyaya
from panini.sounds import guna, is_hrasva, is_vowel, pratyahara
from panini.translit import slp1_to_iast

IK = pratyahara("ik")
YAN_ = pratyahara("yaY")
HAL = pratyahara("hal")


def _sounds(text: str) -> tuple[Sound, ...]:
    return tuple(Sound(c) for c in text)


def _before_sarvadhatuka(st: State) -> list[int]:
    """Indices i whose term is an aṅga directly before a sārvadhātuka affix."""
    out = []
    for i in range(len(st.terms) - 1):
        j = i + 1
        if "aṅga" in st.terms[i].tags and is_pratyaya(st.terms[j]) and "sārvadhātuka" in st.terms[j].tags \
                and st.terms[i].sounds:
            out.append(i)
    return out


# 7.3.84 sārvadhātukārdhadhātukayoḥ (guṇa of a final ik)
def _find_7384(st: State) -> list[Site]:
    return [Site.at(i, len(st.terms[i].sounds) - 1) for i in _before_sarvadhatuka(st)
            if st.terms[i].antya in IK]


def _rewrite_7384(st: State, site: Site):
    sp = site.spans[0]
    return (ReplaceSounds(sp.term, sp.start, sp.end, _sounds(guna(st.terms[sp.term].sounds[sp.start].char))),)


def _note_7384(st: State, site: Site) -> str:
    sp = site.spans[0]
    v = st.terms[sp.term].sounds[sp.start].char
    affix = slp1_to_iast(st.terms[sp.term + 1].text)
    note = f"final {slp1_to_iast(v)} takes guṇa → {slp1_to_iast(guna(v))} before the sārvadhātuka {affix} (1.1.3)"
    if v in "fFxX":
        note += "; the r/l comes from 1.1.51 uraṇ raparaḥ"
    return note


R_7_3_84 = Rule("7.3.84", _find_7384, _rewrite_7384, note=_note_7384)


# 7.3.86 pugantalaghūpadhasya ca (guṇa of a light penultimate ik)
def _light_upadha(st: State, i: int) -> int | None:
    t = st.terms[i]
    if len(t.sounds) >= 2 and t.sounds[-1].char in HAL and is_hrasva(t.sounds[-2].char):
        return len(t.sounds) - 2
    return None


def _find_7386(st: State) -> list[Site]:
    out = []
    for i in _before_sarvadhatuka(st):
        k = _light_upadha(st, i)
        if k is not None and st.terms[i].sounds[k].char in IK:
            out.append(Site.at(i, k))
    return out


def _near_7386(st: State) -> str | None:
    for i in _before_sarvadhatuka(st):
        k = _light_upadha(st, i)
        if k is not None and st.terms[i].kind is TermKind.ROOT and st.terms[i].sounds[k].char not in IK:
            v = slp1_to_iast(st.terms[i].sounds[k].char)
            return (f"7.3.86 (guṇa of a light penultimate vowel) does not apply: "
                    f"{v} is not an ik vowel (1.1.3)")
    return None


R_7_3_86 = Rule("7.3.86", _find_7386, _rewrite_7384, near_miss=_near_7386,
                note=lambda st, site: "the light penultimate "
                f"{slp1_to_iast(st.terms[site.spans[0].term].sounds[site.spans[0].start].char)} takes guṇa")


# 7.3.101 ato dīrgho yañi
def _find_73101(st: State) -> list[Site]:
    return [Site.at(i, len(st.terms[i].sounds) - 1) for i in _before_sarvadhatuka(st)
            if st.terms[i].antya == "a" and adi(st, i + 1) in YAN_]


R_7_3_101 = Rule("7.3.101", _find_73101,
                 lambda st, site: (ReplaceSounds(site.spans[0].term, site.spans[0].start, site.spans[0].end,
                                                 (Sound("A"),)),),
                 note=lambda st, site: f"a is lengthened before {slp1_to_iast(st.terms[site.spans[0].term + 1].adi)},"
                 " a yañ consonant beginning a sārvadhātuka affix")


# 7.1.3 jho 'ntaḥ
def _find_713(st: State) -> list[Site]:
    return [Site.at(i, 0) for i, t in enumerate(st.terms)
            if t.kind is TermKind.TIN and t.sounds and t.sounds[0].char == "J" and not t.sounds[0].it]


R_7_1_3 = Rule("7.1.3", _find_713, lambda st, site: (ReplaceSounds(site.spans[0].term, 0, 1, _sounds("ant")),),
               note=lambda st, site: "jh of the ending is replaced by ant")


# 7.3.77 iṣugamiyamāṃ chaḥ
def _find_7377(st: State) -> list[Site]:
    out = []
    for i in range(len(st.terms) - 1):
        t, nxt = st.terms[i], st.terms[i + 1]
        if t.kind is TermKind.ROOT and t.text in ("iz", "gam", "yam") and nxt.has_marker("S"):
            out.append(Site.at(i, len(t.sounds) - 1))
    return out


R_7_3_77 = Rule("7.3.77", _find_7377,
                lambda st, site: (ReplaceSounds(site.spans[0].term, site.spans[0].start, site.spans[0].end,
                                                (Sound("C"),)),),
                note=lambda st, site: "the final of gam is replaced by ch before an affix marked ś (śap)")


# 6.1.73 che ca (tuk after a short vowel before ch)
def _find_6173(st: State) -> list[Site]:
    out = []
    for i, t in enumerate(st.terms):
        for k in range(len(t.sounds) - 1):
            if is_vowel(t.sounds[k].char) and is_hrasva(t.sounds[k].char) and t.sounds[k + 1].char == "C":
                out.append(Site.at(i, k))
    return out


R_6_1_73 = Rule("6.1.73", _find_6173,
                lambda st, site: augment_in_term_edit(st, site.spans[0].term, site.spans[0].start, (Sound("t"),)),
                tuk_or_satva=True,
                note=lambda st, site: "the augment tuk (t; markers u, k) follows a short vowel before ch; "
                "being kit, it goes at the end of what it is added to (1.1.46)")

RULES = (R_7_3_84, R_7_3_86, R_7_3_101, R_7_1_3, R_7_3_77, R_6_1_73)


# 7.2.81 āto ṅitaḥ
def _find_7281(st: State) -> list[Site]:
    out = []
    nonempty = [i for i, t in enumerate(st.terms) if t.sounds]
    for a, j in zip(nonempty, nonempty[1:]):
        t = st.terms[j]
        if (t.kind is TermKind.TIN and t.sounds[0].char == "A" and st.terms[a].antya == "a"
                and (t.has_tag("ṅit-vat") or t.has_marker("N"))):
            out.append(Site.at(j, 0))
    return out


# Apavāda of 6.1.101 and 6.1.87: wherever 7.2.81 applies (a + ā of a ṅit ending), both of
# them apply too, so its domain is properly included in theirs (yena nāprāpte; Kiparsky's (19)).
R_7_2_81 = Rule("7.2.81", _find_7281, lambda st, site: (ReplaceSounds(site.spans[0].term, 0, 1, _sounds("iy")),),
                blocks=("6.1.101", "6.1.87"),
                note=lambda st, site: "after a base in a, the ā of an ending that counts as ṅit becomes iy")

RULES = (*RULES, R_7_2_81)
