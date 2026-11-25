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
