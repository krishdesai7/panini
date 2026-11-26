# tests/test_rules_tudadi.py — rules added for the tudādi class (slice 1.6)
import pytest

from panini.derivation import Derivation
from panini.engine import derive
from panini.request import availability, parse_request


def form(
    code: str,
    tense: str = "laṭ",
    person: int = 3,
    number: str = "sg",
    voice: str = "active",
) -> Derivation:
    return derive(parse_request(code, tense, person, number, voice))


def _rule_ids(d: Derivation) -> list[str]:
    return [i for s in d.steps for i in s.rule_ids]


# -- 3.1.77 tudādibhyaḥ śaḥ -------------------------------------------------


@pytest.mark.parametrize(
    ("code", "tense", "person", "number", "voice", "expected"),
    [
        ("06.0001", "laṭ", 3, "sg", "active", "tudati"),
        ("06.0001", "laṅ", 3, "sg", "active", "atudat"),
        ("06.0001", "laṭ", 3, "pl", "active", "tudanti"),
        ("06.0001", "laṭ", 3, "pl", "middle", "tudante"),
        ("06.0003", "laṭ", 3, "sg", "active", "diśati"),
    ],
)
def test_sha_forms(code, tense, person, number, voice, expected) -> None:
    d = form(code, tense, person, number, voice)
    assert d.result == expected
    ids = _rule_ids(d)
    assert "3.1.77" in ids
    assert "3.1.68" not in ids


def test_sha_counts_as_marked_n_and_blocks_full_grade() -> None:
    ids = _rule_ids(form("06.0001"))
    assert "1.2.4" in ids
    assert "1.1.5" in ids
    assert "7.3.86" not in ids
    assert "7.3.84" not in ids


def test_3177_note_and_aside() -> None:
    step = next(s for s in form("06.0001").steps if "3.1.77" in s.rule_ids)
    assert "śa" in step.note
    assert "{stem suffix|vikaraṇa}" in step.note
    assert step.history is not None
    assert "tudé" in step.history


@pytest.mark.parametrize(
    ("code", "tense", "expected"),
    [
        ("06.0015", "laṭ", "ucchati"),
        ("06.0015", "laṅ", "aucchat"),
        ("06.0016", "laṭ", "ṛcchati"),
    ],
)
def test_ch_roots_show_6173(code, tense, expected) -> None:
    d = form(code, tense)
    assert d.result == expected
    assert "6.1.73" in _rule_ids(d)


def test_bhvadi_still_takes_shap() -> None:
    ids = _rule_ids(form("01.0001"))
    assert "3.1.68" in ids
    assert "3.1.77" not in ids
