"""How each rule is read: the interpretive conventions and carried-over words its wording relies on.

A sūtra is terse; to apply it you read it through general conventions (the case of
a word tells you its role: 1.1.49 genitive = what is replaced, 1.1.66 locative =
right context, 1.1.67 ablative = left context; 1.1.52 only the last sound is
replaced; abbreviations by 1.1.71) and through words carried down from earlier rules
(anuvṛtti) or from section headings (adhikāra). The engine applies these silently
inside each rule's find/rewrite; this table makes them visible in the trace.

Entries are (source sūtra, what it contributes). Notes use {modern|traditional}.
Carried-over words are cited only where the source is well established.
"""

from __future__ import annotations

from dataclasses import dataclass

GEN = "1.1.49"  # ṣaṣṭhī sthāneyogā
LOC = "1.1.66"  # tasminn iti nirdiṣṭe pūrvasya
ABL = "1.1.67"  # tasmād ity uttarasya
FINAL = "1.1.52"  # alo 'ntyasya
WHOLE = "1.1.55"  # anekālśit sarvasya
NEAR = "1.1.50"  # sthāne 'ntaratamaḥ
ABBR = "1.1.71"  # ādir antyena sahetā
CLASS = "1.1.69"  # aṇudit savarṇasya cāpratyayaḥ
BASE = "6.4.1"  # aṅgasya (heading)
CONTACT = "6.1.72"  # saṃhitāyām (heading)
SINGLE = "6.1.84"  # ekaḥ pūrvaparayoḥ (heading)
WORD = "8.1.16"  # padasya (heading)
NIMITTA = "nimittāpāye naimittikasyāpy apāyaḥ"  # paribhāṣā: when the cause goes, its effect goes too
SAMARTHYA = "vacanasāmarthya"  # the force of the wording: a reading that would make a recitation pointless is excluded
PARIBHASHA = frozenset(
    {NIMITTA, SAMARTHYA}
)  # reading sources that are maxims, not sūtras (no sutras.toml entry)
SUBST = "1.1.56"  # sthānivad ādeśo 'nalvidhau
AFFIX = (
    ("3.1.1", "the item introduced is an {affix|pratyaya}"),
    ("3.1.2", "it is placed after what it is added to"),
    ("3.1.91", "it is added to a {root|dhātu}"),
)
SANDHI = ((CONTACT, "applies to sounds in close contact"),)

READS: dict[str, tuple[tuple[str, str], ...]] = {
    # -- markers --
    "1.3.2": (
        (ABBR, "the {sound-class abbreviation|pratyāhāra} names {all syllabics|ac}"),
    ),
    "1.3.3": (
        (
            "1.3.2",
            "upadeśe ‘in a {form as taught|upadeśa}’ and it ‘{marker|it}’ carry over",
        ),
        (ABBR, "the {sound-class abbreviation|pratyāhāra} names {all consonants|hal}"),
    ),
    "1.3.4": (
        ("1.3.3", "antyam ‘final’ carries over"),
        (
            CLASS,
            "the marker [[u]] makes the abbreviation name the whole class of {dental stops|tu} ([[t th d dh n]])",
        ),
    ),
    "1.3.5": (("1.3.2", "upadeśe and it carry over"),),
    "1.3.7": (
        ("1.3.5", "ādiḥ ‘initial’ carries over"),
        ("1.3.6", "pratyayasya ‘of an {affix|pratyaya}’ carries over"),
        (
            CLASS,
            "the marker [[u]] makes the two abbreviations name the {palatal stops|cu} and {retroflex stops|ṭu}",
        ),
    ),
    "1.3.8": (
        ("1.3.5", "ādiḥ ‘initial’ carries over"),
        ("1.3.6", "pratyayasya ‘of an {affix|pratyaya}’ carries over"),
        (CLASS, "the marker [[u]] makes the abbreviation name the {velar stops|ku}"),
    ),
    "1.3.9": (
        ("1.3.2", "tasya ‘of it’ refers back to the {marker|it}"),
        ("1.1.60", "lopa = disappearance"),
    ),
    "6.1.64": (
        (GEN, "ṣaḥ (genitive): ṣ is what is replaced"),
        (
            NIMITTA,
            "the ṭ, ṭh or ṇ that the ṣ had caused (8.4.41) goes back to t, th or n once the ṣ is gone",
        ),
    ),
    "6.1.64.1": (
        (
            "6.1.64",
            "dhātvādeḥ ‘at the start of a root’ and the replacement of ṣ by s carry over",
        ),
    ),
    "6.1.65": (
        ("6.1.64", "dhātvādeḥ ‘at the start of a root’ carries over"),
        (GEN, "ṇaḥ (genitive): ṇ is what is replaced"),
    ),
    # -- tense, voice, ending, stem suffix --
    "3.2.123": AFFIX,
    "3.2.111": AFFIX,
    "1.3.12": (
        (ABL, "anudāttaṅitaḥ (ablative): the endings follow such a root"),
        ("1.4.100", "ātmanepadam names the {middle|ātmanepada} endings"),
    ),
    "1.3.72": (
        (ABL, "svaritañitaḥ (ablative): the endings follow such a root"),
        ("1.3.12", "ātmanepadam carries over"),
    ),
    "1.3.78": (
        (ABL, "śeṣāt (ablative): after all remaining roots"),
        ("1.4.99", "parasmaipadam names the {active|parasmaipada} endings"),
    ),
    "3.4.78": (
        ("3.4.77", "lasya ‘in place of l’ (heading)"),
        (GEN, "lasya (genitive): l is what is replaced"),
        (SUBST, "each ending inherits the properties of the l it replaces"),
    ),
    "3.4.113": (
        (
            ABBR,
            "the abbreviation names the eighteen {personal endings|tiṅ}, [[tip]] through [[mahiṅ]]",
        ),
    ),
    "3.1.68": (
        *AFFIX,
        (
            "3.1.67",
            "sārvadhātuke ‘before a {present-system affix|sārvadhātuka}’ carries over",
        ),
    ),
    "3.1.77": (
        *AFFIX,
        (
            "3.1.67",
            "sārvadhātuke ‘before a {present-system affix|sārvadhātuka}’ carries over",
        ),
        ("3.1.68", "kartari ‘denoting the agent’ carries over; śa replaces its śap"),
    ),
    "1.2.4": (("1.2.1", "ṅit ‘counts as marked ṅ’ carries over"),),
    "1.4.13": (),
    "1.4.14": (
        (
            ABBR,
            "the abbreviations name the {case endings|sup} and the {personal endings|tiṅ}",
        ),
    ),
    # -- the base --
    "7.3.84": (
        (BASE, "an operation on the {base|aṅga} (heading)"),
        ("7.3.82", "[[guṇaḥ]] ‘{full grade|guṇa}’ carries over"),
        ("1.1.3", "{full grade|guṇa} replaces a {close syllabic|ik}"),
        (FINAL, "only the final sound of the {base|aṅga} is replaced"),
        (LOC, "[[sārvadhātukārdhadhātukayoḥ]] (locative): before such an affix"),
    ),
    "7.3.86": (
        (BASE, "an operation on the {base|aṅga} (heading)"),
        ("7.3.82", "guṇaḥ carries over"),
        ("1.1.65", "upadhā = the penultimate sound"),
        ("1.4.10", "laghu ‘light’ = a short vowel not before a consonant cluster"),
    ),
    "6.4.25": (
        (BASE, "an operation on the {base|aṅga} (heading)"),
        ("6.4.23", "na lopaḥ ‘n is dropped’ carries over"),
        ("6.4.24", "upadhāyāḥ ‘in the {penultimate position|upadhā}’ carries over"),
        (LOC, "śapi (locative): before śap"),
    ),
    "6.4.26": (
        (BASE, "an operation on the {base|aṅga} (heading)"),
        ("6.4.25", "śapi ‘before śap’ carries over, with na lopaḥ and upadhāyāḥ"),
    ),
    "6.4.77": (
        (BASE, "an operation on the {base|aṅga} (heading)"),
        (LOC, "aci (locative): before a vowel"),
        ("1.1.53", "iyaṅ and uvaṅ are marked ṅ, so they replace only the last sound"),
    ),
    "7.4.28": (
        (BASE, "an operation on the {base|aṅga} (heading)"),
        ("7.4.27", "ṛtaḥ ‘of ṛ’ and akṛtsārvadhātukayoḥ carry over"),
        (LOC, "śa…ṣu (locative): before śa, yak or liṅ"),
        ("1.1.53", "riṅ is marked ṅ, so it replaces only the last sound"),
    ),
    "6.1.16": (
        (
            "6.1.15",
            "kiti ‘before an affix marked k’ carries over; ṅiti ca adds marked ṅ",
        ),
        ("1.1.45", "samprasāraṇa = a semivowel replaced by its vowel"),
    ),
    "6.1.108": (
        ("6.1.84", "ekaḥ pūrvaparayoḥ ‘one sound for both’ (heading)"),
        ("1.1.45", "samprasāraṇa = the vowel that replaced a semivowel"),
    ),
    "7.1.100": (
        (BASE, "an operation on the {base|aṅga} (heading)"),
        (GEN, "ṝtaḥ (genitive): ṝ is what is replaced"),
        ("1.1.51", "a vowel replacing ṛ/ṝ is followed by r"),
    ),
    "8.2.21": (
        ("8.2.20", "graḥ ‘of gṝ’ and the r → l change (from 8.2.18) carry over"),
        (LOC, "aci (locative): before a vowel"),
    ),
    "6.4.89": (
        (BASE, "an operation on the {base|aṅga} (heading)"),
        ("6.4.77", "the condition ‘before a {syllabic|ac}’ carries over"),
        ("1.1.65", "upadhā = the penultimate sound"),
        (GEN, "gohaḥ (genitive): in goh, guh in its {full grade|guṇa}"),
    ),
    "7.1.5": (
        (BASE, "an operation on the {base|aṅga} and its affixes (heading)"),
        ("7.1.3", "jhaḥ ‘of jh’ carries over"),
        ("1.1.70", "at, marked by a following t, means short a only"),
        (ABL, "anataḥ (ablative): after what is not short a"),
    ),
    "7.3.101": (
        (BASE, "an operation on the {base|aṅga} (heading)"),
        (GEN, "ataḥ (genitive): a is what is replaced"),
        ("1.1.70", "at, marked by a following t, means short a only"),
        (
            LOC,
            "the locative means the rule applies before a {resonant, [[jh]], or [[bh]]|yañ}",
        ),
    ),
    "7.1.3": (
        (BASE, "an operation on the {base|aṅga} and its affixes (heading)"),
        ("7.1.2", "pratyayādīnām ‘at the start of an {affix|pratyaya}’ carries over"),
        (GEN, "jhaḥ (genitive): jh is what is replaced"),
    ),
    "7.1.58": (
        (BASE, "an operation on the {base|aṅga} (heading)"),
        ("1.1.47", "num, marked m, goes right after the last vowel"),
    ),
    "7.1.59": (
        (BASE, "an operation on the {base|aṅga} (heading)"),
        ("7.1.58", "num carries over"),
        (LOC, "śe (locative): before śa"),
        ("1.1.47", "num, marked m, goes right after the last vowel"),
    ),
    "7.1.59.1": (
        ("7.1.59", "śe ‘before śa’ and num carry over"),
        ("1.1.47", "num, marked m, goes right after the last vowel"),
    ),
    "6.4.24": (
        (BASE, "an operation on the {base|aṅga} (heading)"),
        ("6.4.23", "na lopaḥ ‘n is dropped’ carries over"),
        ("1.1.65", "upadhā = the penultimate sound"),
        (LOC, "kṅiti (locative): before an affix marked k or ṅ"),
    ),
    "7.1.61": (
        (BASE, "an operation on the {base|aṅga} (heading)"),
        ("7.1.58", "num carries over"),
        (GEN, "radhijabhoḥ (genitive dual): radh and jabh get it"),
        (LOC, "aci (locative): before a vowel"),
        ("1.1.47", "num, marked m, goes right after the last vowel"),
    ),
    "1.3.60": (
        (ABL, "śitaḥ: the endings follow a root before an affix marked ś"),
        ("1.3.12", "ātmanepadam carries over"),
    ),
    "7.3.78": (
        (BASE, "an operation on the {base|aṅga} (heading)"),
        ("7.3.75", "śiti ‘before an affix marked ś’ carries over"),
        (
            GEN,
            "the genitive list: each root is what is replaced by its stem, in order (1.3.10)",
        ),
        (WHOLE, "a replacement of several sounds takes the place of the whole root"),
    ),
    "7.3.77": (
        (BASE, "an operation on the {base|aṅga} (heading)"),
        ("7.3.75", "śiti ‘before an affix marked ś’ carries over"),
        (FINAL, "only the final sound is replaced: the m of gam"),
    ),
    "6.1.73": (
        *SANDHI,
        ("6.1.71", "hrasvasya ‘to a short vowel’ and tuk carry over"),
        (LOC, "che (locative): before ch"),
        (
            "1.1.46",
            "tuk, marked k, goes at the end of what it is added to: the short vowel, right before the ch",
        ),
    ),
    "6.1.75": (
        *SANDHI,
        ("6.1.71", "tuk carries over"),
        (
            ABL,
            "dīrghāt (ablative): the long vowel comes before the sound operated on, the ch",
        ),
        ("6.1.73", "che ‘before ch’ carries over"),
        (
            "1.1.46",
            "tuk, marked k, goes at the end of what it is added to: the long vowel, right before the ch",
        ),
    ),
    "7.3.75": (
        (BASE, "an operation on the {base|aṅga} (heading)"),
        ("7.3.74", "dīrghaḥ ‘a long vowel’ carries over"),
        (LOC, "śiti (locative): before an affix marked ś"),
    ),
    "7.2.81": (
        (BASE, "an operation on the {base|aṅga} (heading)"),
        ("7.2.80", "ataḥ ‘after a’ and iy carry over"),
        (GEN, "ātaḥ (genitive): ā is what is replaced"),
    ),
    "1.1.5": (
        (
            "1.1.3",
            "the target {close syllabics|ik} and the operations {full grade|guṇa} and {lengthened grade|vṛddhi} carry over",
        ),
        (LOC, "kṅiti (locative): before an affix marked k or ṅ"),
    ),
    # -- vowel sandhi --
    "6.1.78": (
        *SANDHI,
        (
            GEN,
            "the genitive marks the {diphthongs|ec} ([[e o ai au]]) as the sounds being replaced",
        ),
        ("6.1.77", "the condition ‘before a {syllabic|ac}’ carries over"),
        (NEAR, "each takes its closest substitute: e → ay, o → av"),
    ),
    "6.1.87": (
        *SANDHI,
        (SINGLE, "one sound replaces both (heading)"),
        (ABL, "āt (ablative): after a or ā"),
        ("6.1.77", "the condition ‘before a {syllabic|ac}’ carries over"),
        (NEAR, "the {full-grade|guṇa} vowel closest to the second sound"),
    ),
    "6.1.88": (
        *SANDHI,
        (SINGLE, "one sound replaces both (heading)"),
        ("6.1.87", "āt ‘after a or ā’ carries over"),
        (NEAR, "the {lengthened-grade|vṛddhi} vowel closest to the second sound"),
    ),
    "6.1.97": (
        *SANDHI,
        (SINGLE, "one sound replaces both (heading)"),
        ("1.1.70", "at, marked by a following t, means short a only"),
        ("6.1.96", "apadāntāt ‘not at the end of a word’ carries over"),
        ("6.1.94", "pararūpam ‘the form of the second’ carries over"),
        (LOC, "guṇe (locative): before a {full-grade|guṇa} vowel"),
    ),
    "6.1.101": (
        *SANDHI,
        (SINGLE, "one sound replaces both (heading)"),
        (LOC, "savarṇe (locative): before a vowel of the same kind"),
        (NEAR, "the long vowel of that kind"),
    ),
    "6.1.90": (
        *SANDHI,
        (SINGLE, "one sound replaces both (heading)"),
        ("6.1.88", "[[vṛddhiḥ]] ‘{lengthened grade|vṛddhi}’ carries over"),
        (ABL, "[[āṭaḥ]] (ablative): after the augment [[āṭ]]"),
    ),
    "6.1.66": (
        (
            LOC,
            "the locative means the rule applies before {any consonant other than [[y]]|val}",
        ),
        ("1.1.60", "lopa = disappearance"),
        (
            SAMARTHYA,
            (
                "not the y/v a root begins with as taught: reciting vraj, vraṇ with a v "
                "the rule always deleted would be pointless"
            ),
        ),
    ),
    # -- endings and augments --
    "3.4.79": (
        ("3.4.77", "lasya ‘in place of l’ (heading)"),
        (GEN, "ṭeḥ (genitive): the ṭi is what is replaced"),
        ("1.1.64", "ṭi = the last vowel and what follows"),
        (SUBST, "ṭitaḥ refers to the lakāra, whose ṭ the ending inherits"),
    ),
    "3.4.80": (
        ("3.4.79", "ṭitaḥ ‘of a ṭ-marked lakāra’ carries over"),
        (GEN, "thāsaḥ (genitive): thās is what is replaced"),
    ),
    "6.4.71": (
        (BASE, "the augment is added to the {base|aṅga} (heading)"),
        (LOC, "luṅlaṅlṛṅkṣu (locative): when these lakāras follow"),
        ("1.1.46", "aṭ, marked ṭ, goes at the beginning"),
    ),
    "6.4.72": (
        ("6.4.71", "luṅlaṅlṛṅkṣu ‘when these lakāras follow’ carries over"),
        ("1.1.46", "āṭ, marked ṭ, goes at the beginning"),
    ),
    "3.4.99": (
        ("3.4.77", "lasya ‘in place of l’ (heading)"),
        (SUBST, "the ending inherits the ṅ of laṅ"),
        (FINAL, "only the final sound (s) is dropped"),
    ),
    "3.4.100": (
        ("3.4.99", "ṅitaḥ ‘of a ṅ-marked lakāra’ carries over"),
        (FINAL, "only the final sound (i) is dropped"),
    ),
    "3.4.101": (
        ("3.4.99", "ṅitaḥ ‘of a ṅ-marked lakāra’ carries over"),
        (WHOLE, "a substitute of several sounds replaces the whole ending"),
    ),
    # -- tripādī --
    "8.2.18": (
        ("8.2.1", "applies after, and invisibly to, all earlier rules (heading)"),
        (GEN, "kṛpaḥ, raḥ (genitive): in kṛp, r is what is replaced"),
    ),
    "8.2.23": (
        (WORD, "padasya ‘at the end of a {word|pada}’ (heading)"),
        ("8.2.1", "applies after, and invisibly to, all earlier rules (heading)"),
    ),
    "8.2.39": (
        (WORD, "padasya ‘at the end of a {word|pada}’ (heading)"),
        (NEAR, "the {modal voiced oral stop|jaś} closest to the original"),
    ),
    "8.2.66": (
        (WORD, "padasya ‘at the end of a {word|pada}’ (heading)"),
        (GEN, "sasajuṣaḥ (genitive): s is what is replaced"),
    ),
    "8.2.78": (
        (
            "8.2.76",
            "the heading supplies lengthening of a {close syllabic|ik} in the environment with [[r]] or [[v]]",
        ),
        ("8.2.77", "the condition ‘before a {consonant|hal}’ carries over"),
        (
            LOC,
            "upadhāyām (locative): when the r or v is in the {penultimate position|upadhā}",
        ),
    ),
    "8.3.15": (
        (WORD, "padasya ‘at the end of a {word|pada}’ (heading)"),
        (
            LOC,
            "the locative means the rule applies before a {voiceless obstruent|khar} or at a pause",
        ),
    ),
    "8.3.24": (
        (LOC, "the locative means the rule applies before an {obstruent|jhal}"),
    ),
    "8.4.1": (
        ("8.2.1", "applies after, and invisibly to, all earlier rules (heading)"),
        (GEN, "no (genitive): n is what is replaced"),
        (ABL, "raṣābhyām (ablative): after r or ṣ"),
    ),
    "8.4.37": ((WORD, "padasya ‘at the end of a {word|pada}’ (heading)"),),
    "8.4.1.1": (
        (
            "8.4.1",
            "raṣābhyāṃ no ṇaḥ samānapade carries over, with ṛ/ṝ added to r and ṣ",
        ),
    ),
    "8.4.2": (("8.4.1", "raṣābhyāṃ no ṇaḥ samānapade carries over"),),
    "8.4.40": (
        ("1.3.10", "the substitutes match the originals in order: s → ś, t → c, …"),
    ),
    "8.4.41": (
        (
            "8.4.40",
            "the {retroflex substitutes|ṣṭu} match [[s]] and the {dental stops|tu} in order: [[s → ṣ]], [[t → ṭ]], …",
        ),
        ("1.3.10", "the substitutes match the originals in order"),
    ),
    "8.4.53": (
        (LOC, "the locative means the rule applies before a {voiced oral stop|jhaś}"),
        (NEAR, "the {modal voiced oral stop|jaś} closest to the original"),
    ),
    "8.4.56": (
        (
            "8.4.55",
            "the change from an {obstruent|jhal} to the corresponding {voiceless unaspirated obstruent|car} carries over",
        ),
    ),
    "8.4.58": (
        (LOC, "the locative means the rule applies before a {stop or approximant|yay}"),
        (NEAR, "the nasal of the following sound's class"),
    ),
}


@dataclass(frozen=True)
class Aside:
    """A historical remark about a step: outside Pāṇini's account, shown beside it.
    ``italic`` lists the words (Latin, Greek) the page sets in italics. An asterisk marks a
    reconstructed form and is shown as it stands."""

    text: str
    italic: tuple[str, ...] = ()


REDUPLICATED = "a reduplicated present"
SK_PRESENT = "a present in *-sḱe-"

# The tud class as a whole (3.1.77).
TUDADI_ASIDE = Aside(
    "the Indo-European *tudé- type, accented on the thematic vowel "
    "(accent is not shown yet)"
)

# Historical asides for the substituted present stems (7.3.77, 7.3.78), keyed by upadeśa.
HISTORY: dict[str, Aside] = {
    "pA": Aside(f"{REDUPLICATED}, cf. Latin bibit", ("bibit",)),
    "GrA": Aside(REDUPLICATED),
    "zWA": Aside(
        f"{REDUPLICATED}, cf. Latin sistit, Greek hístēmi", ("sistit", "hístēmi")
    ),
    "zadx~": Aside("a reduplicated present (*si-sd-), cf. Latin sīdit", ("sīdit",)),
    "dfSi~r": Aside("a different root, spaś ‘see’, cf. Latin speciō", ("speciō",)),
    "dAR": Aside("a different root, yam ‘hold out’"),
    "f": Aside(SK_PRESENT),
    "gamx~": Aside(f"{SK_PRESENT}, cf. Greek báskō", ("báskō",)),
}
