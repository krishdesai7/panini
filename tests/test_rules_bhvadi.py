# tests/test_rules_bhvadi.py — rules added for the whole bhvādi class (slice 1.5)
import pytest
from panini.derivation import Derivation
from panini.engine import derive
from panini.request import parse_request


def form(code: str, tense: str = "laṭ", person: int = 3, number: str = "sg", voice: str = "active") -> Derivation:
    return derive(parse_request(code, tense, person, number, voice))


def _rule_ids(d: Derivation) -> list[str]:
    return [i for s in d.steps for i in s.rule_ids]


# -- 7.1.58 idito num dhātoḥ ---------------------------------------------

@pytest.mark.parametrize("code, tense, voice, expected", [
    ("01.0074", "laṭ", "active", "krandati"), ("01.0074", "laṅ", "active", "akrandat"),
    ("01.0100", "laṭ", "middle", "vaṅkate"), ("01.0435", "laṭ", "middle", "kampate")])
def test_idit_nasal(code, tense, voice, expected):
    d = form(code, tense, voice=voice)
    assert d.result == expected and "7.1.58" in [i for s in d.steps for i in s.rule_ids]


def test_idit_nasal_applies_once_and_cites_1147():
    d = form("01.0074")
    steps = [s for s in d.steps if "7.1.58" in s.rule_ids]
    assert len(steps) == 1 and "1.1.47" in steps[0].note
    assert any(src == "1.1.47" for src, _ in steps[0].reads)


def test_irit_root_gets_no_nasal():
    d = form("01.1143")   # dṛś, df\Si~r: i~r is the marker ir, not i
    assert "7.1.58" not in _rule_ids(d)


def test_idit_nasal_after_a_merged_initial_vowel():
    # laṅ of adi~ (and): ā + a merge (6.1.90); the merged vowel still counts as the root's (6.1.85)
    assert form("01.0064", "laṅ").result == "āndat"


def test_idit_note_uses_house_markup():
    note = next(s.note for s in form("01.0074").steps if "7.1.58" in s.rule_ids)
    assert "{i|idit}" in note and "{augment|āgama}" in note and "markers u, m" not in note


# -- 6.1.64-65 root-initial ṣ and ṇ ----------------------------------------

@pytest.mark.parametrize("code, expected", [
    ("01.0532", "stanati"),   # ṣṭana~: ṭ goes back to t
    ("01.1136", "namati"),    # ṇama~
    ("01.0970", "sthalati"),  # ṣṭhala~: ṭh goes back to th
    ("01.1072", "snāyati"),   # ṣṇai: ṇ goes back to n
    ("01.0535", "sanati"),    # ṣaṇa~: the ṇ the ṣ caused, not at the start, goes back to n
    ("01.0451", "stambhate")])
def test_root_initial_s_and_n(code, expected):
    assert form(code, voice="middle" if code == "01.0451" else "active").result == expected


def test_retroflex_undone_in_the_same_step_and_cites_the_paribhasha():
    d = form("01.0532")
    steps = [s for s in d.steps if "6.1.64" in s.rule_ids]
    assert len(steps) == 1
    assert "ṭ goes back to t" in steps[0].note
    assert "{ṣ-taught|ṣopadeśa}" in steps[0].note and "{marker|it}" not in steps[0].note
    assert any(src == "nimittāpāye naimittikasyāpy apāyaḥ" for src, _ in steps[0].reads)


def test_root_initial_n_note_names_the_taught_form():
    note = next(s.note for s in form("01.1136").steps if "6.1.65" in s.rule_ids)
    assert "{ṇ-taught|ṇopadeśa}" in note and "{marker|it}" not in note


# -- 8.2.78 upadhāyāṃ ca ---------------------------------------------------

@pytest.mark.parametrize("code, voice, expected", [
    ("01.0021", "middle", "kūrdate"), ("01.0239", "active", "hūrchati"), ("01.0650", "active", "ūrvati")])
def test_vowel_lengthened_before_upadha_r_or_v_and_consonant(code, voice, expected):
    d = form(code, voice=voice)
    assert d.result == expected and "8.2.78" in _rule_ids(d)


# -- 6.1.75 dīrghāt: tuk after a long vowel before ch ---------------------

@pytest.mark.parametrize("code, tense, expected", [
    ("01.0233", "laṭ", "mlecchati"), ("01.0238", "laṭ", "hrīcchati"),   # long e, long ī
    ("01.0541", "laṅ", "acchamat")])                                     # the augment a before ch (6.1.73)
def test_tuk_before_ch(code, tense, expected):
    d = form(code, tense)
    assert d.result == expected


def test_tuk_after_long_vowel_is_6175_not_6173():
    ids = _rule_ids(form("01.0233"))
    assert "6.1.75" in ids and "6.1.73" not in ids
    note = next(s.note for s in form("01.0233").steps if "6.1.75" in s.rule_ids)
    assert "long vowel" in note and "tuk" in note


# -- 8.4.40 + 8.4.53: ṣasj ------------------------------------------------

def test_sasj_palatal_then_voiced():
    d = form("01.0229")
    ids = _rule_ids(d)
    assert d.result == "sajjati"
    assert ids.index("8.4.40") < ids.index("8.4.53")


# -- 8.4.41 ṣṭunā ṣṭuḥ: the nasal of ghiṇ, ghuṇ, ghṛṇ ----------------------

@pytest.mark.parametrize("code, expected", [
    ("01.0502", "ghiṇṇate"), ("01.0503", "ghuṇṇate"), ("01.0504", "ghṛṇṇate")])
def test_nasal_becomes_retroflex_before_retroflex_nasal(code, expected):
    d = form(code, voice="middle")
    assert d.result == expected and "8.4.41" in _rule_ids(d)


# -- 8.4.1-2 raṣābhyāṃ no ṇaḥ samānapade ----------------------------------

def test_n_after_r_with_vowel_between_is_8_4_2():
    d = form("01.0679")   # riṇv: r i n v
    assert d.result == "riṇvati" and "8.4.2" in _rule_ids(d)
    assert form("01.0680").result == "raṇvati"


def test_n_before_a_stop_stays_dental():
    # bhṛ: the n of the ending follows r + a but precedes t, so no ṇ (Vidyut agrees)
    d = form("01.1045", number="pl")
    assert d.result == "bharanti" and "8.4.1" not in _rule_ids(d) and "8.4.2" not in _rule_ids(d)


# -- vārttika on 6.1.64: ṣṭhiv and ṣvaṣk keep their ṣ; 7.3.75 -------------

def test_svask_keeps_its_s():
    d = form("01.0105", voice="middle")
    ids = _rule_ids(d)
    assert d.result == "ṣvaṣkate" and "6.1.64.1" in ids and "6.1.64" not in ids


def test_sthiv_keeps_its_s_and_lengthens_i():
    d = form("01.0641")
    ids = _rule_ids(d)
    assert d.result == "ṣṭhīvati" and "6.1.64.1" in ids and "7.3.75" in ids
    assert "6.1.64" not in ids and "7.3.86" not in ids
    step = next(s for s in d.steps if "6.1.64.1" in s.rule_ids)
    assert step.kind == "prohibition" and "ṣṭhiv" in step.note


def test_root_initial_s_and_n_only_when_the_root_still_begins_with_it():
    # laṅ of iṣ and aṇ: the vowel merged into the augment, so the ṣ / ṇ left over is not the root's start
    assert form("01.0780", "laṅ").result == "aiṣat"
    assert form("01.0512", "laṅ").result == "āṇat"
