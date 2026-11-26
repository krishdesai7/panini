# tests/test_rules_core.py
from panini.derivation import Derivation
from panini.engine import derive
from panini.derivation import Status
from panini.request import parse_request

def ids(d: Derivation) -> list[str]: return [i for s in d.steps for i in s.rule_ids]

def test_pathati() -> None:
    d = derive(parse_request("paṭh", "laṭ", 3, "sg", "active"))
    assert d.status is Status.OK and d.result == "paṭhati"
    assert set(ids(d)) >= {"1.3.1","1.3.2","1.3.9","3.2.123","1.3.3","1.3.78","3.4.78","3.4.113","3.1.68","1.3.8","1.4.13","1.4.14"}
    order = ids(d)
    for a, b in [("3.2.123","3.4.78"), ("3.4.78","3.1.68"), ("3.4.113","3.1.68")]:
        assert order.index(a) < order.index(b)

def test_markers_capitalized_once_marked() -> None:
    d = derive(parse_request("paṭh", "laṭ", 3, "sg", "active"))
    rendered = [" + ".join(tv.iast() for tv in s.after) for s in d.steps]
    assert "paṭhÃ" in rendered[1]            # after 1.3.2
    assert any("tiP" in r for r in rendered)

def test_tin_selection_note_cites_category_rules() -> None:
    d = derive(parse_request("paṭh", "laṭ", 3, "sg", "active"))
    note = next(s.note for s in d.steps if "3.4.78" in s.rule_ids)
    assert "1.4.108" in note and "1.4.22" in note and "1.3.78" in note

def test_unavailable() -> None:
    d = derive(parse_request("edh", "laṭ", 3, "sg", "active"))
    assert d.status is Status.UNAVAILABLE and "1.3.12" in d.message


def test_nisedha_applies_once_and_losers_not_repeated() -> None:
    d = derive(parse_request("pac", "laṭ", 1, "pl", "active"))
    assert ids(d).count("1.3.4") == 1
    blocked = [l for s in d.steps for l in s.losers if l.rule_id == "1.3.3" and "1.3.4" in l.reason]
    assert len(blocked) == 1
    assert not any("commutes" in l.reason for s in d.steps for l in s.losers)


def test_lakara_note_explains_the_unwritten_nasal_and_the_placement() -> None:
    d = derive(parse_request("paṭh", "laṭ", 3, "sg", "active"))
    note = next(s.note for s in d.steps if "3.2.123" in s.rule_ids)
    assert "lãṭ" in note and "3.1.2" in note


def test_affix_glosses_name_their_headings() -> None:
    from panini.rules.base import sutra_info
    for rid in ("3.2.123", "3.2.111", "3.1.68"):
        assert "3.1.91" in sutra_info(rid)[1] and "3.1.2" in sutra_info(rid)[1]
    assert sutra_info("3.1.2")[0] == "paraś ca"


def test_lakara_note_cites_each_heading_at_its_word() -> None:
    d = derive(parse_request("bhū", "laṭ", 3, "sg", "active"))
    note = next(s.note for s in d.steps if "3.2.123" in s.rule_ids)
    assert "an affix (3.1.1) placed after (3.1.2) the root (3.1.91)" in note
    assert "by tradition" in note


def test_steps_say_what_kind_of_step_they_are() -> None:
    d = derive(parse_request("pac", "laṭ", 1, "pl", "active"))
    kind = {s.rule_ids[0]: s.kind for s in d.steps}
    assert kind["3.2.123"] == "change" and kind["1.3.78"] == "category" and kind["1.3.4"] == "prohibition"
    assert d.to_json()["steps"][0]["kind"] in ("change", "category", "prohibition")


def test_pada_note_names_the_rule_that_uses_it() -> None:
    d = derive(parse_request("bhū", "laṭ", 3, "sg", "active"))
    assert "3.4.78" in next(s.note for s in d.steps if "1.3.78" in s.rule_ids)


def test_notes_lead_with_modern_terms_and_keep_panini_s_in_markup() -> None:
    d = derive(parse_request("bhū", "laṭ", 3, "sg", "active"))
    note = next(s.note for s in d.steps if "1.3.78" in s.rule_ids)
    assert "no rule assigns the {middle|ātmanepada} voice" in note
    assert "{active|parasmaipada}" in note


def test_glosses_use_markup_for_technical_terms() -> None:
    from panini.rules.base import sutra_info
    assert "{active|parasmaipada}" in sutra_info("1.3.78")[1]
    assert "{present-system affix|sārvadhātuka}" in sutra_info("3.4.113")[1]


def test_ending_choice_note_uses_modern_voice_name() -> None:
    d = derive(parse_request("bhū", "laṭ", 3, "sg", "active"))
    assert "{active|parasmaipada}, assigned by 1.3.78" in next(s.note for s in d.steps if "3.4.78" in s.rule_ids)


def test_ending_choice_note_is_one_line_per_category() -> None:
    d = derive(parse_request("bhū", "laṭ", 3, "sg", "active"))
    lines = next(s.note for s in d.steps if "3.4.78" in s.rule_ids).split("\n")
    assert lines[0] == "l is replaced by tip, chosen by:"
    assert [l.split(":")[0] for l in lines[1:]] == ["· voice", "· person", "· number"]
