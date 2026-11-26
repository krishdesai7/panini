# tests/test_request_lexicon.py
import json
import unicodedata

import pytest
from panini.lexicon import ROOTS, AmbiguousRoot, UnknownRoot, citation_name, lookup_root
from panini.request import REFERENCE_PATH, all_requests, availability, parse_request


def test_lexicon_loads_whole_section() -> None:
    assert len(ROOTS) == 1156 and "01.0933" not in ROOTS  # 1166 rows, 10 placeholders
    assert ROOTS["01.0001"].upadesha == "BU"
    assert ROOTS["01.0001"].meaning == "to be, become"
    assert ROOTS["01.0074"].meaning == "āhvāne rodane ca"
    assert ROOTS["01.0074"].meaning_kind == "traditional"
    assert (
        citation_name(ROOTS["01.0925"].upadesha) == "chad"
    )  # CadiH, read as Cada~ by the vendor script


@pytest.mark.parametrize(
    "up, name",
    [
        ("BU", "bhū"),
        ("paWa~", "paṭh"),
        ("ga\\mx~", "gam"),
        ("smf\\", "smṛ"),
        ("eDa~\\", "edh"),
        ("RI\\Y", "nī"),
        ("qupa\\ca~^z", "pac"),
        ("kradi~", "krand"),
        ("zwana~", "stan"),
        ("zWA\\", "sthā"),
        ("Divi~", "dhinv"),
        ("da\\nSa~", "daṃś"),
        ("df\\Si~r", "dṛś"),
        # a nasal is quoted at the place of the consonant after it: palatal, labial, velar, retroflex
        ("za\\nja~", "sañj"),
        ("zva\\nja~\\", "svañj"),
        ("ra\\nja~^", "rañj"),
        ("ancu~", "añc"),
        ("tunpa~", "tump"),
        ("SranBu~\\", "śrambh"),
        ("vaki~\\", "vaṅk"),
        ("GiRi~\\", "ghiṇṇ"),
        ("kanka~", "kaṅk"),
        ("kanwa~", "kaṇṭ"),
    ],
)  # no bhvādi root is taught with n before a velar or retroflex
def test_citation_name(up, name) -> None:
    assert citation_name(up) == name


def test_lookup_names_codes_and_ambiguity() -> None:
    assert lookup_root("paṭh").code == "01.0381"
    assert lookup_root("01.0074").name == "krand"
    assert lookup_root("smṛ").code == "01.0919"  # featured wins
    with pytest.raises(AmbiguousRoot) as e:
        lookup_root("yam")
    assert "01.0930" in str(e.value)
    assert "01.1031" in str(e.value)
    with pytest.raises(UnknownRoot):
        lookup_root("kṛkṛkṛ")


def test_pada_from_markers() -> None:
    assert [ROOTS[c].pada for c in ("01.0001", "01.0002", "01.1049")] == ["P", "A", "U"]


def test_lookup_variants() -> None:
    assert lookup_root("paṭh").key == "01.0381"
    assert lookup_root(unicodedata.normalize("NFD", "paṭh-")).key == "01.0381"
    assert lookup_root("paṭha~").key == "01.0381"
    with pytest.raises(UnknownRoot) as e:
        lookup_root("zzz")
    assert "bhū" in e.value.available


def test_parse_both_vocabularies() -> None:
    a = parse_request("paṭh", "present imperfective", 3, "sg", "active")
    b = parse_request("paṭh", "laṭ", "prathama", "ekavacana", "parasmaipada")
    assert a == b
    assert a.key == "01.0381|laṭ|P|3|sg"
    assert a.describe()[1] == "3sg present imperfective active"


def test_availability() -> None:
    assert availability(parse_request("paṭh", "laṭ", 3, "sg", "middle"))[1] == "1.3.78"
    assert availability(parse_request("edh", "laṭ", 3, "sg", "active"))[1] == "1.3.12"
    assert availability(parse_request("nī", "laṭ", 3, "sg", "middle")) is None


def test_middle_only_reason_names_the_marker_1312_reads() -> None:
    # 1.3.12 anudāttaṅitaḥ: an unaccented marker vowel (edh) or the marker ṅ (smi, zmi\N)
    edh = availability(parse_request("edh", "laṭ", 3, "sg", "active"))[0]
    smi = availability(parse_request("01.1099", "laṭ", 3, "sg", "active"))
    assert "anudātta" in edh
    assert "ṅ" not in edh
    assert smi[1] == "1.3.12"
    assert "marked ṅ" in smi[0]
    assert "anudātta" not in smi[0]


def test_reference_fixture_matches_available_requests() -> None:
    ref = json.loads(REFERENCE_PATH.read_text())
    avail = [r.key for r in all_requests() if availability(r) is None]
    assert sorted(avail) == sorted(ref)


def test_reference_loads_from_any_working_directory(tmp_path, monkeypatch) -> None:
    from panini.request import load_reference

    monkeypatch.chdir(tmp_path)
    assert len(load_reference()) > 1000


def test_missing_reference_warns(tmp_path, capsys) -> None:
    from panini.request import load_reference

    assert load_reference(tmp_path / "nope.json") == {}
    assert "warning" in capsys.readouterr().err.lower()


@pytest.mark.parametrize(
    "text,key",
    [
        ("gamḷ", "01.1137"),
        ("paṭha", "01.0381"),
        ("ḍupacaṣ", "01.1151"),
        ("Bhū", "01.0001"),
        ("PAṬH", "01.0381"),
    ],
)
def test_lookup_ignores_nasal_sign_and_case(text, key) -> None:
    assert lookup_root(text).key == key


def test_lookup_accepts_tilde_over_vowel() -> None:
    assert lookup_root("paṭhã").key == "01.0381"


def test_out_of_scope_roots_say_why() -> None:
    r = parse_request("01.1092", "laṭ", 3, "sg")  # śru
    assert availability(r) == (
        "śru forms a nu-present (śṛṇoti), deferred to the athematic classes",
        "3.1.74",
    )
    assert (
        availability(parse_request("01.0461", "laṭ", 3, "sg"))[1] == "3.1.28"
    )  # gup → gopāyati


def test_lookup_accepts_plain_ascii_spellings() -> None:
    # every diacritic folds away, as in the explorer's search: ñ → n, ṃ → m, ā → a, dot-below dropped
    assert lookup_root("sanj").code == "01.1142"
    assert lookup_root("stha").code == lookup_root("01.1077").code == "01.1077"
    assert lookup_root("dams").name == "daṃś"
    # an exact spelling still wins over a folded one: pat is pat, not paṭ or pāt
    assert lookup_root("pat").name == "pat"
    with pytest.raises(AmbiguousRoot):
        lookup_root("yam")
