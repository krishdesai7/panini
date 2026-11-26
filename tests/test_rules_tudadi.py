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


# -- 7.1.59 śe mucādīnām, vārttika 7.1.59.1, 6.4.24 ----------------------------


@pytest.mark.parametrize(
    ("code", "voice", "expected"),
    [
        ("06.0166", "active", "muñcati"),
        ("06.0166", "middle", "muñcate"),
        ("06.0167", "active", "lumpati"),
        ("06.0168", "active", "vindati"),
        ("06.0171", "active", "kṛntati"),
        ("06.0172", "active", "khindati"),
        ("06.0173", "active", "piṃśati"),
    ],
)
def test_mucadi_nasal_infix(code, voice, expected) -> None:
    d = form(code, voice=voice)
    assert d.result == expected
    step = next(s for s in d.steps if "7.1.59" in s.rule_ids)
    assert "1.1.47" in step.note


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("06.0031", "tṛmphati"),
        ("06.0043", "gumphati"),
        ("06.0045", "umbhati"),
        ("06.0077", "tṛṃhati"),
    ],
)
def test_trmphadi_lose_and_regain_the_nasal(code, expected) -> None:
    d = form(code)
    ids = _rule_ids(d)
    assert d.result == expected
    assert ids.index("6.4.24") < ids.index("7.1.59.1")


def test_strh_loses_its_nasal() -> None:  # 06.0037 stfnhU~: 6.4.24 only
    d = form("06.0037")
    assert d.result == "stṛhati"
    assert "7.1.59.1" not in _rule_ids(d)


def test_nasal_infix_aside() -> None:
    step = next(s for s in form("06.0166").steps if "7.1.59" in s.rule_ids)
    assert step.history is not None
    assert "nasal-infix" in step.history
    assert "rumpit" in step.history_italic


def test_bhvadi_nasal_kept_before_shap() -> None:
    d = form("01.0435", voice="middle")
    assert d.result == "kampate"
    assert "6.4.24" not in _rule_ids(d)


# -- 6.4.77 iyaṅ/uvaṅ, 7.4.28 riṅ -------------------------------------------


@pytest.mark.parametrize(
    ("code", "person", "voice", "expected"),
    [
        ("06.0133", 3, "active", "dhuvati"),
        ("06.0132", 3, "active", "nuvati"),
        ("06.0143", 3, "active", "kṣiyati"),
        ("06.0143", 1, "active", "kṣiyāmi"),
        ("06.0137", 3, "middle", "kuvate"),
    ],
)
def test_iyan_uvan(code, person, voice, expected) -> None:
    d = form(code, person=person, voice=voice)
    assert d.result == expected
    assert "6.4.77" in _rule_ids(d)


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("06.0139", "mriyate"),
        ("06.0147", "driyate"),
        ("06.0148", "dhriyate"),
        ("06.0138", "priyate"),
    ],
)
def test_rin_then_iyan(code, expected) -> None:
    d = form(code, voice="middle")
    ids = _rule_ids(d)
    assert d.result == expected
    assert ids.index("7.4.28") < ids.index("6.4.77")


def test_mr_has_no_active() -> None:
    assert availability(parse_request("06.0139", "laṭ", 3, "sg", "active")) is not None


def test_bhvadi_u_root_unaffected() -> None:
    assert "6.4.77" not in _rule_ids(form("01.0001"))


# -- 6.1.16 samprasāraṇa, 6.1.108 samprasāraṇāc ca -----------------------------


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("06.0149", "pṛcchati"),
        ("06.0012", "vṛścati"),
        ("06.0013", "vicati"),
        ("06.0004", "bhṛjjati"),
    ],
)
def test_samprasarana(code, expected) -> None:
    d = form(code)
    ids = _rule_ids(d)
    assert d.result == expected
    assert ids.index("6.1.16") < ids.index("6.1.108")


def test_prach_also_shows_6173() -> None:
    assert "6.1.73" in _rule_ids(form("06.0149"))
