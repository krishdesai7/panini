# tests/test_rules_core.py
from panini.engine import derive
from panini.derivation import Status
from panini.request import parse_request

def ids(d): return [i for s in d.steps for i in s.rule_ids]

def test_pathati():
    d = derive(parse_request("paṭh", "laṭ", 3, "sg", "active"))
    assert d.status is Status.OK and d.result == "paṭhati"
    assert set(ids(d)) >= {"1.3.1","1.3.2","1.3.9","3.2.123","1.3.3","1.3.78","3.4.78","3.4.113","3.1.68","1.3.8","1.4.13","1.4.14"}
    order = ids(d)
    for a, b in [("3.2.123","3.4.78"), ("3.4.78","3.1.68"), ("3.4.113","3.1.68")]:
        assert order.index(a) < order.index(b)

def test_markers_capitalized_once_marked():
    d = derive(parse_request("paṭh", "laṭ", 3, "sg", "active"))
    rendered = [" + ".join(tv.iast() for tv in s.after) for s in d.steps]
    assert "paṭhÃ" in rendered[1]            # after 1.3.2
    assert any("tiP" in r for r in rendered)

def test_tin_selection_note_cites_category_rules():
    d = derive(parse_request("paṭh", "laṭ", 3, "sg", "active"))
    note = next(s.note for s in d.steps if "3.4.78" in s.rule_ids)
    assert "1.4.108" in note and "1.4.22" in note and "1.3.78" in note

def test_unavailable():
    d = derive(parse_request("edh", "laṭ", 3, "sg", "active"))
    assert d.status is Status.UNAVAILABLE and "1.3.12" in d.message


def test_nisedha_applies_once_and_losers_not_repeated():
    d = derive(parse_request("pac", "laṭ", 1, "pl", "active"))
    assert ids(d).count("1.3.4") == 1
    blocked = [l for s in d.steps for l in s.losers if l.rule_id == "1.3.3" and "1.3.4" in l.reason]
    assert len(blocked) == 1
    assert not any("commutes" in l.reason for s in d.steps for l in s.losers)


def test_lakara_note_explains_the_unwritten_nasal_and_the_placement():
    d = derive(parse_request("paṭh", "laṭ", 3, "sg", "active"))
    note = next(s.note for s in d.steps if "3.2.123" in s.rule_ids)
    assert "lãṭ" in note and "3.1.2" in note


def test_affix_glosses_name_their_headings():
    from panini.rules.base import sutra_info
    for rid in ("3.2.123", "3.2.111", "3.1.68"):
        assert "3.1.91" in sutra_info(rid)[1] and "3.1.2" in sutra_info(rid)[1]
    assert sutra_info("3.1.2")[0] == "paraś ca"
