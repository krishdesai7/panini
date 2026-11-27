"""Operations on the base (aṅga): guṇa, lengthening, ch-substitution, tuk, num, jh → ant."""

from __future__ import annotations

import itertools
from dataclasses import replace

from panini.edits import VIKRTA, AddTags, DeleteSounds, ReplaceSounds
from panini.lexicon import citation_name
from panini.meta import (
    absorbed_ekadesha,
    augment_in_term_edit,
    mit_augment_edit,
    mit_position,
    substitution_edit,
)
from panini.model import Site, Sound, Span, State, Term, TermKind
from panini.rules.base import Optionality, Rule, adi, is_pratyaya
from panini.rules.readings import HISTORY, Aside
from panini.sounds import dirgha, guna, is_hrasva, is_vowel, pratyahara
from panini.translit import slp1_to_iast

IK = pratyahara("ik")
YAN_ = pratyahara("yaY")
HAL = pratyahara("hal")


def _sounds(text: str) -> tuple[Sound, ...]:
    return tuple(Sound(c) for c in text)


def _following(st: State, i: int) -> int | None:
    """Index of the next term with sounds after term i."""
    return next((k for k in range(i + 1, len(st.terms)) if st.terms[k].sounds), None)


def _next_term(st: State, i: int) -> int:
    """Like _following, for callers whose site guarantees such a term exists."""
    j = _following(st, i)
    if j is None:
        raise ValueError(f"no term with sounds after term {i}")
    return j


def _before_sarvadhatuka(st: State) -> list[int]:
    """Indices i whose term is an aṅga directly before a sārvadhātuka affix. A term emptied by
    a single substitute (śap's a merged into the stem's a, 6.1.97) is not in the way."""
    out: list[int] = []
    for i in range(len(st.terms) - 1):
        j = _following(st, i)
        if (
            j is not None
            and "aṅga" in st.terms[i].tags
            and is_pratyaya(st.terms[j])
            and "sārvadhātuka" in st.terms[j].tags
            and st.terms[i].sounds
        ):
            out.append(i)
    return out


# 7.3.84 sārvadhātukārdhadhātukayoḥ (guṇa of a final ik)
def _find_7384(st: State) -> list[Site]:
    return [
        Site.at(i, len(st.terms[i].sounds) - 1)
        for i in _before_sarvadhatuka(st)
        if st.terms[i].antya in IK
    ]


def _rewrite_7384(st: State, site: Site) -> tuple[ReplaceSounds]:
    sp = site.spans[0]
    return (
        ReplaceSounds(
            sp.term,
            sp.start,
            sp.end,
            _sounds(guna(st.terms[sp.term].sounds[sp.start].char)),
        ),
    )


def _note_7384(st: State, site: Site) -> str:
    sp = site.spans[0]
    v = st.terms[sp.term].sounds[sp.start].char
    affix = slp1_to_iast(st.terms[_next_term(st, sp.term)].text)
    note = f"final {slp1_to_iast(v)} takes {{full grade|guṇa}} → {slp1_to_iast(guna(v))} before the {{present-system|sārvadhātuka}} affix {affix} (1.1.3)"
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
    out: list[Site] = []
    for i in _before_sarvadhatuka(st):
        k = _light_upadha(st, i)
        if k is not None and st.terms[i].sounds[k].char in IK:
            out.append(Site.at(i, k))
    return out


def _near_7386(st: State) -> str | None:
    for i in _before_sarvadhatuka(st):
        k = _light_upadha(st, i)
        t = st.terms[i]
        if (
            k is not None
            and t.kind is TermKind.ROOT
            and VIKRTA not in t.tags
            and t.sounds[k].char not in IK
        ):
            v = slp1_to_iast(st.terms[i].sounds[k].char)
            return (
                f"7.3.86 ({{full grade|guṇa}} of a light penultimate vowel) does not apply: "
                f"[[{v}]] is outside the {{close syllabics|ik}} (1.1.3)"
            )
    return None


R_7_3_86 = Rule(
    "7.3.86",
    _find_7386,
    _rewrite_7384,
    near_miss=_near_7386,
    note=lambda st, site: (
        "the light penultimate "
        f"{slp1_to_iast(st.terms[site.spans[0].term].sounds[site.spans[0].start].char)} takes {{full grade|guṇa}}"
    ),
)


# 7.3.101 ato dīrgho yañi
def _find_73101(st: State) -> list[Site]:
    return [
        Site.at(i, len(st.terms[i].sounds) - 1)
        for i in _before_sarvadhatuka(st)
        if st.terms[i].antya == "a" and adi(st, _next_term(st, i)) in YAN_
    ]


R_7_3_101 = Rule(
    "7.3.101",
    _find_73101,
    lambda st, site: (
        ReplaceSounds(
            site.spans[0].term, site.spans[0].start, site.spans[0].end, (Sound("A"),)
        ),
    ),
    note=lambda st, site: (
        f"a is lengthened before {slp1_to_iast(st.terms[_next_term(st, site.spans[0].term)].adi or '')},"
        " a {resonant, [[jh]], or [[bh]]|yañ}, beginning a {present-system|sārvadhātuka} affix"
    ),
)


# 7.1.3 jho 'ntaḥ
def _find_713(st: State) -> list[Site]:
    return [
        Site.at(i, 0)
        for i, t in enumerate(st.terms)
        if t.kind is TermKind.TIN
        and t.sounds
        and t.sounds[0].char == "J"
        and not t.sounds[0].it
    ]


R_7_1_3 = Rule(
    "7.1.3",
    _find_713,
    lambda st, site: (ReplaceSounds(site.spans[0].term, 0, 1, _sounds("ant")),),
    note=lambda st, site: "jh of the ending is replaced by ant",
)


def _preceding(st: State, j: int) -> int:
    """Index of the last term with sounds before term j."""
    return next(i for i in range(j - 1, -1, -1) if st.terms[i].sounds)


# 7.1.5 ātmanepadeṣv anataḥ: in a middle ending, jh becomes at after a base that does not end in
# short a. In this class, once śap is there, the base ends in its a, except where that a has merged
# into a root's ā (gā + a → gā, 6.1.101).
def _find_715(st: State) -> list[Site]:
    return [
        site
        for site in _find_713(st)
        if (j := site.spans[0].term) > 0
        and st.terms[j].has_tag("ātmanepada")
        and st.terms[_preceding(st, j)].antya != "a"
    ]


# Apavāda of 7.1.3: wherever 7.1.5 applies (the jh of a middle ending), 7.1.3 applies too.
R_7_1_5 = Rule(
    "7.1.5",
    _find_715,
    lambda st, site: (ReplaceSounds(site.spans[0].term, 0, 1, _sounds("at")),),
    blocks=("7.1.3",),
    note=lambda st, site: (
        "in a {middle|ātmanepada} ending, jh is replaced by at, because the {base|aṅga} "
        f"before it ends in {slp1_to_iast(st.terms[_preceding(st, site.spans[0].term)].antya or '')}, not short a"
    ),
)


# 7.3.77 iṣugamiyamāṃ chaḥ. The roots are named by their upadeśa: yam is the one marked with an
# accent on its vowel (ya\ma~, 'to stop'); yama~ ('to serve food') is not meant.
def _takes_ch(t: Term) -> bool:
    return t.upadesha in ("izu~", "gamx~") or (
        t.upadesha == "yama~" and t.has_tag("anudatta-vowel")
    )


def _find_7377(st: State) -> list[Site]:
    out: list[Site] = []
    for i in range(len(st.terms) - 1):
        t, nxt = st.terms[i], st.terms[i + 1]
        if t.kind is TermKind.ROOT and _takes_ch(t) and nxt.has_marker("S"):
            out.append(Site.at(i, len(t.sounds) - 1))
    return out


R_7_3_77 = Rule(
    "7.3.77",
    _find_7377,
    lambda st, site: (
        ReplaceSounds(
            site.spans[0].term, site.spans[0].start, site.spans[0].end, (Sound("C"),)
        ),
    ),
    note=lambda st, site: (
        f"the final {slp1_to_iast(st.terms[site.spans[0].term].antya or '')} of "
        f"{slp1_to_iast(st.terms[site.spans[0].term].text)} is replaced by ch before an affix marked ś (śap)"
    ),
    history=lambda st, site: HISTORY.get(st.terms[site.spans[0].term].upadesha),
)


# 6.1.73 che ca (tuk after a short vowel before ch) and 6.1.75 dīrghāt (after a long vowel)
def _tuk_before_ch(st: State, short: bool) -> list[Site]:
    """Sites of a vowel right before ch, short or long: the vowel's span, then the ch's span.
    The ch may belong to the next term: 6.1.72 saṃhitāyām makes this a rule about sounds in contact
    (the augment a of laṅ + ch)."""
    flat = [
        (i, k, s.char) for i, t in enumerate(st.terms) for k, s in enumerate(t.sounds)
    ]
    return [
        Site((Span(i, k, k + 1), Span(j, m, m + 1)))
        for (i, k, c), (j, m, nxt) in itertools.pairwise(flat)
        if is_vowel(c) and is_hrasva(c) == short and nxt == "C"
    ]


def _tuk_rule(rule_id: str, short: bool, which: str) -> Rule:
    # tuk is added to the vowel (6.1.71 hrasvasya, genitive) and, being kit, goes at its end (1.1.46):
    # it is written right after the vowel, in the vowel's term. When that vowel is the augment a/ā
    # (laṅ), the t ends the augment's term; meta.mit_position skips it when it looks for a merged vowel.
    return Rule(
        rule_id,
        lambda st: _tuk_before_ch(st, short),
        lambda st, site: augment_in_term_edit(
            site.spans[0].term, site.spans[0].start, (Sound("t"),)
        ),
        tuk_or_satva=True,
        note=lambda st, site: (
            f"the augment tuk (t; markers u, k) is added to a {which} vowel before ch; "
            "being kit, it goes at the end of that vowel (1.1.46)"
        ),
    )


R_6_1_73 = _tuk_rule("6.1.73", True, "short")
R_6_1_75 = _tuk_rule("6.1.75", False, "long")


# 7.3.75 ṣṭhivuklamyācamāṃ śiti: ṣṭhiv, klam and ācam take a long vowel before an affix marked ś.
# ācam is cam after the preverb ā, outside this scope (no preverbs). klam (klamu~) is a divādi root:
# it belongs to a later slice, where the note must say what 7.3.75 displaces there instead of guṇa.
# Only ṣṭhiv is in the bhvādi list.
LENGTHENED_BEFORE_SHIT = ("zWiv",)


def _find_7375(st: State) -> list[Site]:
    out: list[Site] = []
    for i in range(len(st.terms) - 1):
        t, nxt = st.terms[i], st.terms[i + 1]
        if (
            t.kind is TermKind.ROOT
            and t.text in LENGTHENED_BEFORE_SHIT
            and nxt.has_marker("S")
        ):
            out.append(Site.at(i, len(t.sounds) - 2))
    return out


R_7_3_75 = Rule(
    "7.3.75",
    _find_7375,
    lambda st, site: (
        ReplaceSounds(
            site.spans[0].term,
            site.spans[0].start,
            site.spans[0].end,
            (
                Sound(
                    dirgha(
                        st.terms[site.spans[0].term].sounds[site.spans[0].start].char
                    )
                ),
            ),
        ),
    ),
    blocks=("7.3.86",),
    note=lambda st, site: (
        f"{slp1_to_iast(st.terms[site.spans[0].term].text)} gets a long vowel "
        "before an affix marked ś (śap); this takes the place of the {full grade|guṇa} of 7.3.86"
    ),
)


# 7.2.81 āto ṅitaḥ
def _find_7281(st: State) -> list[Site]:
    out: list[Site] = []
    nonempty = [i for i, t in enumerate(st.terms) if t.sounds]
    for a, j in itertools.pairwise(nonempty):
        t = st.terms[j]
        if (
            t.kind is TermKind.TIN
            and t.sounds[0].char == "A"
            and st.terms[a].antya == "a"
            and (t.has_tag("ṅit-vat") or t.has_marker("N"))
        ):
            out.append(Site.at(j, 0))
    return out


# Apavāda of 6.1.101 and 6.1.87: wherever 7.2.81 applies (a + ā of a ṅit ending), both of
# them apply too, so its domain is properly included in theirs (yena nāprāpte; Kiparsky's (19)).
R_7_2_81 = Rule(
    "7.2.81",
    _find_7281,
    lambda st, site: (ReplaceSounds(site.spans[0].term, 0, 1, _sounds("iy")),),
    blocks=("6.1.101", "6.1.87"),
    note=lambda st, site: (
        "after a {base|aṅga} in a, the ā of an ending that counts as marked ṅ becomes iy"
    ),
)


# 1.1.5 kṅiti ca — a niṣedha: no guṇa/vṛddhi of an ik vowel before an affix marked k or ṅ
# (or treated as ṅit, 1.2.4). Like 1.3.4 it changes nothing itself and blocks the rules.
def _is_knit(t: Term) -> bool:
    return t.has_marker("k") or t.has_marker("N") or t.has_tag("ṅit-vat")


def _find_115(st: State) -> list[Site]:
    out: list[Site] = []
    for i in _before_sarvadhatuka(st):
        if not _is_knit(st.terms[_next_term(st, i)]):
            continue
        t = st.terms[i]
        if t.antya in IK:
            out.append(Site.at(i, len(t.sounds) - 1))
        k = _light_upadha(st, i)
        if k is not None and t.sounds[k].char in IK:
            out.append(Site.at(i, k))
    return out


R_1_1_5 = Rule(
    "1.1.5",
    _find_115,
    lambda st, site: (),
    blocks=("7.3.84", "7.3.86"),
    note=lambda st, site: (
        f"no {{full grade|guṇa}} before {slp1_to_iast(st.terms[_next_term(st, site.spans[0].term)].text)}, "
        "which is marked ṅ (or counts as such)"
    ),
)


# 7.1.58 idito num dhātoḥ
def _is_idit(t: Term) -> bool:
    r"""A root whose marker is a final i. The it-rules must have marked it (1.3.2); the upadeśa
    tells i from ir: in i~r (dṛś, df\Si~r) the nasal i belongs to the marker ir and adds no nasal."""
    return t.kind is TermKind.ROOT and t.has_marker("i") and t.upadesha.endswith("i~")


def _find_7158(st: State) -> list[Site]:
    out: list[Site] = []
    for i, t in enumerate(st.terms):
        if (
            _is_idit(t)
            and not any(s.agama and s.char == "n" for s in t.sounds)
            and (pos := mit_position(st, i)) is not None
        ):
            out.append(Site.at(i, pos, pos))
    return out


R_7_1_58 = Rule(
    "7.1.58",
    _find_7158,
    lambda st, site: mit_augment_edit(st, site.spans[0].term, (Sound("n"),)),
    note=lambda st, site: (
        "a root marked with {i|idit} gets a nasal in every form: "
        "the {augment|āgama} n (num) goes right after its last vowel (1.1.47)"
    ),
)


# 7.1.61 radhijabhor aci: radh and jabh get num before a vowel-initial affix. The sūtra names the
# roots by shape, so every root whose bare form is raD or jaB is meant: in bhvādi that is jabhī
# (jaBI~\, 01.0453; jambhate, as the Siddhānta Kaumudī and the Mādhavīya Dhātuvṛtti give it).
# Vidyut restricts the rule to jaBI~ by upadeśa, citing nothing. The other bhvādi jabh, jaBa~
# (01.0150), is Kṣīrasvāmin's reading of the same root and is out of scope (docs/findings.md).
# 7.1.62 neṭy aliṭi radheḥ (radh, before iṭ) is not reached in laṭ and laṅ.
RADH_JABH = frozenset({"raD", "jaB"})


def _bare(t: Term) -> str:
    return "".join(s.char for s in t.sounds if not s.it and not s.agama)


def _find_7161(st: State) -> list[Site]:
    out: list[Site] = []
    for i, t in enumerate(st.terms):
        j = _following(st, i)
        if (
            t.kind is TermKind.ROOT
            and _bare(t) in RADH_JABH
            and j is not None
            and not any(s.agama and s.char == "n" for s in t.sounds)
            and is_pratyaya(st.terms[j])
            and is_vowel(adi(st, j) or "")
            and (pos := mit_position(st, i)) is not None
        ):
            out.append(Site.at(i, pos, pos))
    return out


R_7_1_61 = Rule(
    "7.1.61",
    _find_7161,
    lambda st, site: mit_augment_edit(st, site.spans[0].term, (Sound("n"),)),
    note=lambda st, site: (
        f"{slp1_to_iast(_bare(st.terms[site.spans[0].term]))} gets the "
        "{augment|āgama} n (num) before an affix beginning with a vowel; it goes right after "
        "the last vowel (1.1.47)"
    ),
)


# 7.3.78 pāghrādhmāsthāmnādāṇdṛśyartisartiśadasadāṃ pibajighradhamatiṣṭhamanayacchapaśyarcchadhauśīyasīdāḥ:
# before an affix marked ś the whole root is replaced by a present stem, listed by upadeśa.
STEMS_7378 = {
    "pA": "piba",
    "GrA": "jiGra",
    "DmA": "Dama",
    "zWA": "tizWa",
    "mnA": "mana",
    "dAR": "yacCa",
    "dfSi~r": "paSya",
    "f": "fcCa",
    "sf": "DO",
    "Sadx~": "SIya",
    "zadx~": "sIda",
}
SUBSTITUTED = "stem-substituted"  # tag: the whole root has been replaced (7.3.78)
# sṛ becomes dhau only in the sense of running (Kāśikā: vegitāyāṃ gatau); the engine can't know
# the sense, so this one is optional and the ordinary stem sarati comes first.
OPTIONAL_7378 = frozenset({"sf"})


def _site_7378(st: State, only_optional: bool) -> list[Site]:
    out: list[Site] = []
    for i in range(len(st.terms) - 1):
        t, nxt = st.terms[i], st.terms[i + 1]
        if (
            t.kind is TermKind.ROOT
            and t.upadesha in STEMS_7378
            and SUBSTITUTED not in t.tags
            and (t.upadesha in OPTIONAL_7378) is only_optional
            and nxt.has_marker("S")
        ):
            out.append(Site.at(i, 0, len(t.sounds)))
    return out


def _rewrite_7378(st: State, site: Site):
    sp = site.spans[0]
    # If the root's first sound has merged into an ekādeśa (ā + ṛ → ār, 6.1.90), the stem takes the
    # root's place in it and that rule is applied again (meta.substitution_edit).
    return (
        *substitution_edit(st, sp.term, STEMS_7378[st.terms[sp.term].upadesha]),
        AddTags(sp.term, frozenset({SUBSTITUTED})),
    )


def _note_7378(st: State, site: Site) -> str:
    t = st.terms[site.spans[0].term]
    new = STEMS_7378[t.upadesha]
    root = citation_name(t.upadesha)
    note = f"{root} is replaced by the stem {slp1_to_iast(new)} before an affix marked ś (śap)"
    for rule_id, x, y in absorbed_ekadesha(st, site.spans[0].term):
        note += (
            f"; its sound had merged with its neighbour ({slp1_to_iast(x)} + {slp1_to_iast(y)}, {rule_id}), "
            "which counts as part of both (6.1.85), so the stem takes its place (1.1.56) and "
            f"{rule_id} is applied again to the stem's sound"
        )
    return note


def _history_7378(st: State, site: Site) -> Aside | None:
    return HISTORY.get(st.terms[site.spans[0].term].upadesha)


# It replaces the whole root, so it overrides the guṇa of 7.3.84/86 (apavāda).
R_7_3_78 = Rule(
    "7.3.78",
    lambda st: _site_7378(st, False),
    _rewrite_7378,
    blocks=("7.3.84", "7.3.86"),
    note=_note_7378,
    history=_history_7378,
)
R_7_3_78_OPT = replace(
    R_7_3_78,
    find=lambda st: _site_7378(st, True),
    optional=Optionality.SENSE,
    optional_phrase="{only in the sense of running|Kāśikā: vegitāyāṃ gatau}, so not applied here",
)


# 6.4.25 daṃśasañjasvañjāṃ śapi, 6.4.26 rañjeś ca: these roots lose their penultimate nasal before
# śap (na lopaḥ from 6.4.23, upadhāyāḥ from 6.4.24), extending 6.4.24's loss before a kit/ṅit affix.
# The roots are named by their upadeśa, accents removed: da\nSa~, za\nja~, zva\nja~\, ra\nja~^.
NASAL_LOSS_BEFORE_SHAP = {
    "6.4.25": ("danSa~", "zanja~", "zvanja~"),
    "6.4.26": ("ranja~",),
}


def _nasal_loss(rule_id: str) -> Rule:
    def find(st: State) -> list[Site]:
        out: list[Site] = []
        for i in range(len(st.terms) - 1):
            t, nxt = st.terms[i], st.terms[i + 1]
            if (
                t.kind is TermKind.ROOT
                and t.upadesha in NASAL_LOSS_BEFORE_SHAP[rule_id]
                and nxt.upadesha == "Sap"
                and t.upadha == "n"
            ):
                out.append(Site.at(i, len(t.sounds) - 2))
        return out

    return Rule(
        rule_id,
        find,
        lambda st, site: (DeleteSounds(site.spans[0].term, (site.spans[0].start,)),),
        note=lambda st, site: (
            f"the penultimate nasal of {citation_name(st.terms[site.spans[0].term].upadesha)} "
            "is dropped before śap"
        ),
    )


R_6_4_25 = _nasal_loss("6.4.25")
R_6_4_26 = _nasal_loss("6.4.26")


# 6.4.89 ūd upadhāyā gohaḥ: the penultimate vowel of goha becomes ū before a vowel-initial affix
# (aci, carried over from 6.4.77). goha is guh in its full grade, so the rule follows guṇa (7.3.86)
# and reaches only forms where guṇa applied.
def _find_6489(st: State) -> list[Site]:
    out: list[Site] = []
    for i, t in enumerate(st.terms):
        j = _following(st, i)
        if (
            t.kind is TermKind.ROOT
            and t.upadesha == "guhU~"
            and t.upadha == "o"
            and j is not None
            and is_pratyaya(st.terms[j])
            and is_vowel(adi(st, j) or "")
        ):
            out.append(Site.at(i, len(t.sounds) - 2))
    return out


R_6_4_89 = Rule(
    "6.4.89",
    _find_6489,
    lambda st, site: (
        ReplaceSounds(
            site.spans[0].term, site.spans[0].start, site.spans[0].end, (Sound("U"),)
        ),
    ),
    note=lambda st, site: (
        "guh in its {full grade|guṇa} form goh has its {penultimate|upadhā} o "
        "replaced by ū before an affix beginning with a vowel"
    ),
)


RULES = (
    R_7_3_84,
    R_7_3_86,
    R_7_3_101,
    R_7_1_3,
    R_7_1_5,
    R_7_3_77,
    R_6_1_73,
    R_6_1_75,
    R_7_3_75,
    R_7_2_81,
    R_1_1_5,
    R_7_1_58,
    R_7_1_61,
    R_7_3_78,
    R_7_3_78_OPT,
    R_6_4_25,
    R_6_4_26,
    R_6_4_89,
)
