"""Tense, pada, the person/number ending, śap, and the saṃjñās they need."""

from __future__ import annotations

lazy from collections.abc import Callable

from panini.edits import AddTags, InsertTerm, ReplaceTerm
from panini.lexicon import middle_voice_markers, middle_voice_reason
from panini.meta import substitute_term
from panini.model import Coreference, Number, Site, State, Term, TermKind, Time
from panini.rules.base import Find, Rewrite, Rule, dhatu_index, is_pratyaya
from panini.rules.readings import TUDADI_ASIDE
from panini.translit import slp1_to_iast

PADA_TAGS = ("parasmaipada", "ātmanepada")

# 3.4.78 tiptasjhisipthasthamibvasmastātāṃjhathāsāthāṃdhvamiḍvahimahiṅ
TIN = {
    "parasmaipada": {
        Coreference.NONE: ("tip", "tas", "Ji"),
        Coreference.ADDRESSEE: ("sip", "Tas", "Ta"),
        Coreference.SPEAKER: ("mip", "vas", "mas"),
    },
    "ātmanepada": {
        Coreference.NONE: ("ta", "AtAm", "Ja"),
        Coreference.ADDRESSEE: ("TAs", "ATAm", "Dvam"),
        Coreference.SPEAKER: ("iw", "vahi", "mahiN"),
    },
}
_PERSON_REASON = {
    Coreference.NONE: "neither addressee nor speaker is the agent → {third person|prathama puruṣa} (1.4.108 śeṣe prathamaḥ)",
    Coreference.ADDRESSEE: "the addressee is the agent → {second person|madhyama puruṣa} (1.4.105 yuṣmady upapade … madhyamaḥ)",
    Coreference.SPEAKER: "the speaker is the agent → {first person|uttama puruṣa} (1.4.107 asmady uttamaḥ)",
}
_NUMBER_REASON = {
    Number.ONE: "one agent → {singular|ekavacana} (1.4.22 dvyekayor dvivacanaikavacane)",
    Number.TWO: "two agents → {dual|dvivacana} (1.4.22 dvyekayor dvivacanaikavacane)",
    Number.MANY: "many agents → {plural|bahuvacana} (1.4.21 bahuṣu bahuvacanam)",
}


def _root(st: State) -> Term:
    d = dhatu_index(st)
    if d is None:
        raise ValueError("the derivation has no root")
    return st.terms[d]


def _la_index(st: State) -> int | None:
    return next((i for i, t in enumerate(st.terms) if t.kind is TermKind.LA), None)


# 3.2.123 vartamāne laṭ / 3.2.111 anadyatane laṅ
def _add_la(time: Time) -> Callable[[State], list[Site]]:
    def find(st: State) -> list[Site]:
        d = dhatu_index(st)
        if (
            d is not None
            and d == len(st.terms) - 1
            and "dhātu" in st.terms[d].tags
            and st.intent.time is time
        ):
            return [Site.term(d)]
        return []

    return find


def _insert_la(upadesha: str) -> Rewrite:
    return lambda st, site: (
        InsertTerm(
            site.spans[0].term + 1,
            Term.from_upadesha(TermKind.LA, upadesha, frozenset({"pratyaya"})),
        ),
    )


def _la_note(meaning: str, written: str, recited: str) -> str:
    return (
        f"{meaning} → {written}, an affix (3.1.1) placed after (3.1.2) the root (3.1.91). "
        f"The text writes {written}; by tradition it is taught as {recited}, its vowel nasal (nasality was "
        f"never written down), so that vowel, there only to make the l pronounceable, is a marker (1.3.2), "
        f"as is the final consonant (1.3.3)"
    )


R_3_2_123 = Rule(
    "3.2.123",
    _add_la(Time.PRESENT),
    _insert_la("la~w"),
    note=lambda st, site: _la_note("present time", "laṭ", "lãṭ"),
)
R_3_2_111 = Rule(
    "3.2.111",
    _add_la(Time.PAST_NOT_TODAY),
    _insert_la("la~N"),
    note=lambda st, site: _la_note("past time, not of today", "laṅ", "lãṅ"),
)


# Pada: 1.3.12 anudāttaṅita ātmanepadam, 1.3.72 svaritañitaḥ kartrabhiprāye kriyāphale,
# 1.3.78 śeṣāt kartari parasmaipadam
def _pada_find(condition: Callable[[State, Term], bool]) -> Find:
    def find(st: State) -> list[Site]:
        la, d = _la_index(st), dhatu_index(st)
        if la is None or d is None or any(st.terms[la].has_tag(p) for p in PADA_TAGS):
            return []
        return [Site.term(la)] if condition(st, st.terms[d]) else []

    return find


def _tag_pada(pada: str, rule_id: str) -> Rewrite:
    return lambda st, site: (
        AddTags(site.spans[0].term, frozenset({pada, f"pada-by:{rule_id}"})),
    )


R_1_3_12 = Rule(
    "1.3.12",
    _pada_find(lambda st, root: bool(middle_voice_markers(root))),
    _tag_pada("ātmanepada", "1.3.12"),
    blocks=("1.3.78",),
    note=lambda st, site: (
        f"{middle_voice_reason(_root(st))}, so l is classed as "
        "taking {middle|ātmanepada} endings; 3.4.78 will choose from that set"
    ),
)
R_1_3_72 = Rule(
    "1.3.72",
    _pada_find(
        lambda st, root: (
            ("svaritet" in root.tags or root.has_marker("Y"))
            and st.intent.fruit_to_agent
        )
    ),
    _tag_pada("ātmanepada", "1.3.72"),
    blocks=("1.3.78",),
    note=lambda st, site: (
        "the root's marker vowel is {falling-pitched|svarita} (or it is marked ñ) and the fruit of the action goes "
        "to the agent, so l is classed as taking {middle|ātmanepada} endings; 3.4.78 will choose from that set"
    ),
)
R_1_3_78 = Rule(
    "1.3.78",
    _pada_find(lambda st, root: True),
    _tag_pada("parasmaipada", "1.3.78"),
    note=lambda st, site: (
        "no rule assigns the {middle|ātmanepada} voice, so l is classed as taking {active|parasmaipada} "
        "endings; 3.4.78 will choose from that set"
    ),
)


# 1.3.60 śadeḥ śitaḥ: śad takes ātmanepada before an affix marked ś. Both lakāras here take śap
# (or śa, in tudādi), so the la is known to be followed by a ś-affix before 3.1.68/3.1.77 add it.
SHIT_LAKARAS = ("la~w", "la~N")


def _find_1360(st: State) -> list[Site]:
    la, d = _la_index(st), dhatu_index(st)
    if la is None or d is None or any(st.terms[la].has_tag(p) for p in PADA_TAGS):
        return []
    return (
        [Site.term(la)]
        if st.terms[d].upadesha == "Sadx~" and st.terms[la].upadesha in SHIT_LAKARAS
        else []
    )


R_1_3_60 = Rule(
    "1.3.60",
    _find_1360,
    _tag_pada("ātmanepada", "1.3.60"),
    blocks=("1.3.78",),
    note=lambda st, site: (
        "śad takes {middle|ātmanepada} endings before an affix marked ś "
        f"({'śa' if st.terms[dhatu_index(st) or 0].has_tag('tudādi') else 'śap'} follows), "
        "so l is classed as taking them; 3.4.78 will choose from that set"
    ),
)


# 3.4.78: l is replaced by the ending the intent selects.
def _find_3478(st: State) -> list[Site]:
    la = _la_index(st)
    if la is None or not any(st.terms[la].has_tag(p) for p in PADA_TAGS):
        return []
    return [Site.term(la)]


def _chosen(st: State, la: Term) -> tuple[str, str]:
    pada = "ātmanepada" if la.has_tag("ātmanepada") else "parasmaipada"
    return pada, TIN[pada][st.intent.coreference][st.intent.number.value - 1]


def _rewrite_3478(st: State, site: Site) -> tuple[ReplaceTerm, AddTags]:
    i = site.spans[0].term
    la = st.terms[i]
    _pada, ending = _chosen(st, la)
    new = substitute_term(la, TermKind.TIN, ending)
    return (ReplaceTerm(i, new), AddTags(i, frozenset({"tiṅ", "vibhakti", "pratyaya"})))


def _note_3478(st: State, site: Site) -> str:
    la = st.terms[site.spans[0].term]
    pada, ending = _chosen(st, la)
    by = next((t.split(":", 1)[1] for t in la.tags if t.startswith("pada-by:")), "?")
    pada_rule = (
        "1.4.99 laḥ parasmaipadam"
        if pada == "parasmaipada"
        else "1.4.100 taṅānāv ātmanepadam"
    )
    voice = "{active|parasmaipada}" if pada == "parasmaipada" else "{middle|ātmanepada}"
    return "\n".join(
        [
            f"l is replaced by {slp1_to_iast(ending)}, chosen by:",
            f"· voice: {voice}, assigned by {by} ({pada_rule})",
            f"· person: {_PERSON_REASON[st.intent.coreference]}; the persons are named by 1.4.101",
            f"· number: {_NUMBER_REASON[st.intent.number]}; the numbers are named by 1.4.102",
        ]
    )


R_3_4_78 = Rule("3.4.78", _find_3478, _rewrite_3478, note=_note_3478)


# 3.4.113 tiṅśit sārvadhātukam
def _find_34113(st: State) -> list[Site]:
    return [
        Site.term(i)
        for i, t in enumerate(st.terms)
        if (
            t.kind is TermKind.TIN
            or (t.kind is TermKind.VIKARANA and t.has_marker("S"))
        )
        and "sārvadhātuka" not in t.tags
    ]


R_3_4_113 = Rule(
    "3.4.113",
    _find_34113,
    lambda st, site: (AddTags(site.spans[0].term, frozenset({"sārvadhātuka"})),),
    note=lambda st, site: (
        f"{slp1_to_iast(st.terms[site.spans[0].term].text)} is a {{present-system affix|sārvadhātuka}}"
    ),
)


# 3.1.68 kartari śap
def _find_3168(st: State) -> list[Site]:
    d = dhatu_index(st)
    if d is None or d + 1 >= len(st.terms):
        return []
    nxt = st.terms[d + 1]
    if nxt.kind is TermKind.TIN and "sārvadhātuka" in nxt.tags:
        return [Site((Site.term(d).spans[0], Site.term(d + 1).spans[0]))]
    return []


R_3_1_68 = Rule(
    "3.1.68",
    _find_3168,
    lambda st, site: (
        InsertTerm(
            site.spans[1].term,
            Term.from_upadesha(TermKind.VIKARANA, "Sap", frozenset({"pratyaya"})),
        ),
    ),
    note=lambda st, site: (
        "the {stem suffix|vikaraṇa} śap is added before a {present-system|sārvadhātuka} ending denoting the agent"
    ),
)


# 3.1.77 tudādibhyaḥ śaḥ: after a root of the tud class the stem suffix is śa instead of śap
# (an apavāda of 3.1.68, at the same site). Śa has no marker p, so 1.2.4 makes it count as
# marked ṅ and 1.1.5 then blocks full grade: tudati, not *todati.
def _find_3177(st: State) -> list[Site]:
    d = dhatu_index(st)
    if d is None or not st.terms[d].has_tag("tudādi"):
        return []
    return _find_3168(st)


R_3_1_77 = Rule(
    "3.1.77",
    _find_3177,
    lambda st, site: (
        InsertTerm(
            site.spans[1].term,
            Term.from_upadesha(TermKind.VIKARANA, "Sa", frozenset({"pratyaya"})),
        ),
    ),
    blocks=("3.1.68",),
    note=lambda st, site: (
        "after a root of the tud class the {stem suffix|vikaraṇa} is śa instead of śap"
    ),
    history=lambda st, site: TUDADI_ASIDE,
)


# 1.2.4 sārvadhātukam apit
def _find_124(st: State) -> list[Site]:
    return [
        Site.term(i)
        for i, t in enumerate(st.terms)
        if "sārvadhātuka" in t.tags
        and not t.has_marker("p")
        and "ṅit-vat" not in t.tags
    ]


R_1_2_4 = Rule(
    "1.2.4",
    _find_124,
    lambda st, site: (AddTags(site.spans[0].term, frozenset({"ṅit-vat"})),),
    note=lambda st, site: (
        f"{slp1_to_iast(st.terms[site.spans[0].term].text)} is a "
        "{present-system affix|sārvadhātuka} without the marker p, so it counts as marked ṅ"
    ),
)


# 1.4.13 yasmāt pratyayavidhis tadādi pratyaye 'ṅgam
def _find_1413(st: State) -> list[Site]:
    return [
        Site.term(i)
        for i in range(len(st.terms) - 1)
        if is_pratyaya(st.terms[i + 1])
        and st.terms[i + 1].kind is not TermKind.LA
        and "aṅga" not in st.terms[i].tags
    ]


R_1_4_13 = Rule(
    "1.4.13",
    _find_1413,
    lambda st, site: (AddTags(site.spans[0].term, frozenset({"aṅga"})),),
    assigns="aṅga",
    note=lambda st, site: "what precedes an affix is its {base|aṅga}",
)


# 1.4.14 suptiṅantaṃ padam
def _find_1414(st: State) -> list[Site]:
    if (
        st.terms
        and st.terms[-1].kind is TermKind.TIN
        and "pada" not in st.terms[-1].tags
    ):
        return [Site.term(len(st.terms) - 1)]
    return []


R_1_4_14 = Rule(
    "1.4.14",
    _find_1414,
    lambda st, site: (AddTags(site.spans[0].term, frozenset({"pada"})),),
    assigns="pada",
    note=lambda st, site: "what ends in a {personal ending|tiṅ} is a {word|pada}",
)

RULES = (
    R_3_2_123,
    R_3_2_111,
    R_1_3_12,
    R_1_3_60,
    R_1_3_72,
    R_1_3_78,
    R_3_4_78,
    R_3_4_113,
    R_3_1_68,
    R_3_1_77,
    R_1_2_4,
    R_1_4_13,
    R_1_4_14,
)
