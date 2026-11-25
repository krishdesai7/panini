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
