# tests/test_rules_anga_sandhi.py
import pytest
from panini.engine import derive
from panini.request import parse_request

@pytest.mark.parametrize("root,person,number,expected", [
    ("bhū", 3, "sg", "bhavati"), ("bhū", 3, "pl", "bhavanti"), ("bhū", 1, "sg", "bhavāmi"),
    ("smṛ", 3, "sg", "smarati"), ("nī", 3, "sg", "nayati"), ("pac", 3, "sg", "pacati"),
])
def test_lat_active_vowel_final_forms(root, person, number, expected):
    assert derive(parse_request(root, "laṭ", person, number, "active")).result == expected

def test_gam_before_tripadi():
    d = derive(parse_request("gam", "laṭ", 3, "sg", "active"), disabled=frozenset({"8.4.40"}))
    assert d.result == "gatchati"

def test_bhavanti_shows_collective_blocking():
    d = derive(parse_request("bhū", "laṭ", 3, "pl", "active"))
    step = next(s for s in d.steps if "6.1.97" in s.rule_ids)
    assert {l.rule_id for l in step.losers} >= {"6.1.101", "6.1.87"}

def test_pathati_near_miss():
    d = derive(parse_request("paṭh", "laṭ", 3, "sg", "active"))
    assert any("7.3.86" in n and "not an ik vowel" in n for s in d.steps for n in s.near_misses)

def test_smarati_cites_rapara():
    d = derive(parse_request("smṛ", "laṭ", 3, "sg", "active"))
    assert "1.1.51" in next(s.note for s in d.steps if "7.3.84" in s.rule_ids)


def test_7386_near_miss_only_for_the_root_as_recited():
    d = derive(parse_request("nī", "laṭ", 3, "sg", "active"))   # nay (after guṇa) is not a light-a root
    assert not any("7.3.86" in n for s in d.steps for n in s.near_misses)


def test_7377_note_names_the_replaced_sound():
    d = derive(parse_request("gam", "laṭ", 3, "sg", "active"))
    assert "final m of gam" in next(s.note for s in d.steps if "7.3.77" in s.rule_ids)
