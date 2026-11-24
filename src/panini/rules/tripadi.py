"""The tripādī (8.2.1–8.4.68): applied once, in sūtra order (8.2.1 pūrvatrāsiddham)."""

from __future__ import annotations

from collections.abc import Iterator

from panini.edits import DeleteSounds, ReplaceSounds
from panini.model import Site, Sound, State
from panini.rules.base import Optionality, Rule
from panini.sounds import pratyahara
from panini.translit import slp1_to_iast

JHAL = pratyahara("Jal")
YAY = frozenset("yvrlYmNRnJBGQDjbgqdKPCWTcwtkp")  # yay: y … the y of Śiva sūtra 12
HAL = pratyahara("hal")
CU = pratyahara("cu")
STU = frozenset("stTdDn")
_JAS = {}   # jhal → jaś (voiced unaspirated stop of the same place), 8.2.39
_CAR = {}   # jhal → car (voiceless unaspirated), 8.4.56
for varga in ("kKgGN", "cCjJY", "wWqQR", "tTdDn", "pPbBm"):
    for c in varga[:4]:
        _JAS[c], _CAR[c] = varga[2], varga[0]
_JAS["s"] = "d"   # the dental jaś; never used in practice, since 8.2.66 blocks 8.2.39 for s
_SCU = {"s": "S", "t": "c", "T": "C", "d": "j", "D": "J", "n": "Y"}


def word_sounds(st: State) -> Iterator[tuple[int, int, str]]:
    """(term, position, char) for every sound of the word, in order."""
    for i, t in enumerate(st.terms):
        for k, s in enumerate(t.sounds):
            yield i, k, s.char


def _final(st: State) -> tuple[int, int, str] | None:
    sounds = list(word_sounds(st))
    return sounds[-1] if sounds else None


def _replace(term: int, k: int, new: str):
    return (ReplaceSounds(term, k, k + 1, tuple(Sound(c) for c in new)),)


def _final_rule(rule_id: str, letters: frozenset[str] | set[str], target: dict[str, str] | str, what: str, **kw) -> Rule:
    def get(c: str) -> str:
        return target if isinstance(target, str) else target[c]

    def find(st: State) -> list[Site]:
        f = _final(st)
        if f and f[2] in letters and get(f[2]) != f[2]:
            return [Site.at(f[0], f[1])]
        return []

    def rewrite(st: State, site: Site):
        sp = site.spans[0]
        return _replace(sp.term, sp.start, get(st.terms[sp.term].sounds[sp.start].char))

    def note(st: State, site: Site) -> str:
        c = st.terms[site.spans[0].term].sounds[site.spans[0].start].char
        return f"word-final {slp1_to_iast(c)} → {slp1_to_iast(get(c))} ({what})"

    return Rule(rule_id, find, rewrite, note=note, **kw)


# 8.2.23 saṃyogāntasya lopaḥ
def _find_8223(st: State) -> list[Site]:
    sounds = list(word_sounds(st))
    if len(sounds) >= 2 and sounds[-1][2] in HAL and sounds[-2][2] in HAL:
        return [Site.at(sounds[-1][0], sounds[-1][1])]
    return []


R_8_2_23 = Rule("8.2.23", _find_8223,
                lambda st, site: (DeleteSounds(site.spans[0].term, (site.spans[0].start,)),),
                note=lambda st, site: "a word cannot end in a consonant cluster: final "
                f"{slp1_to_iast(st.terms[site.spans[0].term].sounds[site.spans[0].start].char)} is dropped")

R_8_2_39 = _final_rule("8.2.39", JHAL & _JAS.keys(), _JAS, "an obstruent at the end of a word becomes voiced")


# 8.2.66 sasajuṣo ruḥ — a later, more specific rule that blocks 8.2.39 for s.
def _find_8266(st: State) -> list[Site]:
    f = _final(st)
    return [Site.at(f[0], f[1])] if f and f[2] == "s" else []


R_8_2_66 = Rule("8.2.66", _find_8266,
                lambda st, site: (ReplaceSounds(site.spans[0].term, site.spans[0].start, site.spans[0].start + 1,
                                                (Sound("r"), Sound("u", nasal=True))),),
                blocks=("8.2.39",), reintroduces_upadesha=True,
                note=lambda st, site: "s at the end of a word is replaced by ru~ (its nasal u is a marker)")
R_8_3_15 = _final_rule("8.3.15", {"r"}, "H", "r at a pause becomes visarga")


# 8.3.24 naś cāpadāntasya jhali
def _find_8324(st: State) -> list[Site]:
    sounds = list(word_sounds(st))
    return [Site.at(i, k) for (i, k, c), (_, _, nxt) in zip(sounds, sounds[1:]) if c in "nm" and nxt in JHAL]


R_8_3_24 = Rule("8.3.24", _find_8324, lambda st, site: _replace(site.spans[0].term, site.spans[0].start, "M"),
                note=lambda st, site: "n inside a word before an obstruent becomes anusvāra ṃ")


# 8.4.40 stoḥ ścunā ścuḥ
def _find_8440(st: State) -> list[Site]:
    sounds = list(word_sounds(st))
    out = []
    for n, (i, k, c) in enumerate(sounds):
        neighbours = [sounds[m][2] for m in (n - 1, n + 1) if 0 <= m < len(sounds)]
        if c in STU and any(x in CU or x == "S" for x in neighbours):
            out.append(Site.at(i, k))
    return out


R_8_4_40 = Rule("8.4.40", _find_8440,
                lambda st, site: _replace(site.spans[0].term, site.spans[0].start,
                                          _SCU[st.terms[site.spans[0].term].sounds[site.spans[0].start].char]),
                note=lambda st, site: f"{slp1_to_iast(st.terms[site.spans[0].term].sounds[site.spans[0].start].char)} "
                "next to a palatal becomes palatal: "
                f"{slp1_to_iast(_SCU[st.terms[site.spans[0].term].sounds[site.spans[0].start].char])}")

R_8_4_56 = _final_rule("8.4.56", JHAL & _CAR.keys(), _CAR, "at a pause an obstruent may become voiceless", optional=Optionality.VA)


# 8.4.58 anusvārasya yayi parasavarṇaḥ
def _nasal_of(c: str) -> str | None:
    return next((v[4] for v in ("kKgGN", "cCjJY", "wWqQR", "tTdDn", "pPbBm") if c in v), None)


def _find_8458(st: State) -> list[Site]:
    sounds = list(word_sounds(st))
    return [Site.at(i, k) for (i, k, c), (_, _, nxt) in zip(sounds, sounds[1:])
            if c == "M" and nxt in YAY and _nasal_of(nxt)]


def _rewrite_8458(st: State, site: Site):
    sounds = list(word_sounds(st))
    n = next(m for m, (i, k, _) in enumerate(sounds) if (i, k) == (site.spans[0].term, site.spans[0].start))
    return _replace(site.spans[0].term, site.spans[0].start, _nasal_of(sounds[n + 1][2]) or "M")


R_8_4_58 = Rule("8.4.58", _find_8458, _rewrite_8458,
                note=lambda st, site: "anusvāra before a stop becomes the nasal of that stop's class")

RULES = (R_8_2_23, R_8_2_39, R_8_2_66, R_8_3_15, R_8_3_24, R_8_4_40, R_8_4_56, R_8_4_58)
