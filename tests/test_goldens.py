"""Golden derivations: which rules apply, and the order of the pairs whose order matters.

The reference order is the traditional derivation; Vidyut's step order stands in for it.
"""

from panini.derivation import Derivation
from panini.engine import derive
from panini.request import parse_request


def steps_of(root: str, tense: str, person: int, number: str, voice: str="active") -> tuple[Derivation, list[str]]:
    d = derive(parse_request(root, tense, person, number, voice))
    assert d.status.value == "ok", d.message
    return d, [i for s in d.steps for i in s.rule_ids]


def before(order: list[str], a: str, b: str) -> None:
    assert a in order and b in order, (a, b, order)
    assert order.index(a) < order.index(b), (a, b, order)


def test_bhavanti() -> None:
    d, o = steps_of("bhū", "laṭ", 3, "pl")
    assert d.result == "bhavanti"
    assert set(o) >= {"7.1.3", "7.3.84", "6.1.78", "6.1.97", "8.3.24", "8.4.58"}
    before(o, "7.3.84", "6.1.78"); before(o, "7.1.3", "6.1.97"); before(o, "8.3.24", "8.4.58")


def test_gacchati() -> None:
    d, o = steps_of("gam", "laṭ", 3, "sg")
    assert d.result == "gacchati"
    before(o, "7.3.77", "6.1.73"); before(o, "6.1.73", "8.4.40")


def test_aidhata() -> None:
    d, o = steps_of("edh", "laṅ", 3, "sg", "middle")
    assert d.result == "aidhata"
    assert set(o) >= {"3.2.111", "6.4.72", "6.1.90"} and "3.4.79" not in o
    before(o, "6.4.72", "6.1.90")


def test_abhavam() -> None:
    d, o = steps_of("bhū", "laṅ", 1, "sg")
    assert d.result == "abhavam"
    before(o, "3.4.101", "6.1.97")
    assert "6.4.71" in o
    assert "1.1.56" in next(s.note for s in d.steps if "3.4.101" in s.rule_ids)


def test_abhavat_optional_devoicing() -> None:
    d, o = steps_of("bhū", "laṅ", 3, "sg")
    assert d.result == "abhavat" and d.alternatives == ("abhavad",)
    assert next(s for s in d.steps if "8.4.56" in s.rule_ids).alternatives == ("abhavad",)


def test_abhavan() -> None:
    d, o = steps_of("bhū", "laṅ", 3, "pl")
    assert d.result == "abhavan"
    before(o, "3.4.100", "7.1.3")
    assert "8.2.23" in o


def test_bhavamah_ru_markers_read_inside_tripadi() -> None:
    d, o = steps_of("bhū", "laṭ", 1, "pl")
    assert d.result == "bhavāmaḥ"
    k = o.index("8.2.66")
    assert o[k + 1] == "1.3.2"
    before(o[k:], "1.3.2", "8.3.15")


def test_endings_own_markers_do_not_make_lat_behave_like_lan() -> None:
    d, o = steps_of("edh", "laṭ", 1, "pl", "middle")   # mahiṅ is itself ṅit
    assert d.result == "edhāmahe" and "6.4.72" not in o


def test_guna_before_a_nit_ending_is_prohibited_by_1_1_5_not_merely_deferred() -> None:
    d, o = steps_of("nī", "laṭ", 3, "du")   # tas is ṅit-vat (1.2.4) until śap intervenes
    assert d.result == "nayataḥ"
    reasons = {l.reason for s in d.steps for l in s.losers if l.rule_id == "7.3.84"}
    assert "blocked by 1.1.5" in reasons
    assert not any("nitya" in r for r in reasons)


def test_optional_rule_note_just_says_preferably() -> None:
    d, o = steps_of("bhū", "laṅ", 3, "sg")
    note = next(s for s in d.steps if "8.4.56" in s.rule_ids).note
    assert note.endswith("{preferably|vā}; also correct: abhavad") and "Kiparsky" not in note
    from panini.rules.base import sutra_info
    assert "Kiparsky" not in sutra_info("8.4.56")[1] and "{preferably|vā}" in sutra_info("8.4.56")[1]
