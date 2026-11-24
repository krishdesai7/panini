# tests/test_request_lexicon.py
import json, unicodedata, pytest
from pathlib import Path
from panini.request import REFERENCE_PATH
from panini.lexicon import lookup_root, UnknownRoot, ROOTS
from panini.request import parse_request, availability, all_requests, Purusha

def test_lookup_variants():
    assert lookup_root("paṭh").key == "paṭh"
    assert lookup_root(unicodedata.normalize("NFD", "paṭh-")).key == "paṭh"
    assert lookup_root("paṭha~").key == "paṭh"
    with pytest.raises(UnknownRoot) as e:
        lookup_root("kṛ")
    assert "bhū" in e.value.available

def test_parse_both_vocabularies():
    a = parse_request("paṭh", "present imperfective", 3, "sg", "active")
    b = parse_request("paṭh", "laṭ", "prathama", "ekavacana", "parasmaipada")
    assert a == b and a.key == "paṭh|laṭ|P|3|sg"
    assert a.describe()[1] == "3sg present imperfective active"

def test_availability():
    assert availability(parse_request("paṭh", "laṭ", 3, "sg", "middle"))[1] == "1.3.78"
    assert availability(parse_request("edh", "laṭ", 3, "sg", "active"))[1] == "1.3.12"
    assert availability(parse_request("nī", "laṭ", 3, "sg", "middle")) is None

def test_reference_fixture_matches_available_requests():
    ref = json.loads(REFERENCE_PATH.read_text())
    avail = [r.key for r in all_requests() if availability(r) is None]
    assert sorted(avail) == sorted(ref) and len(ref) == 162


def test_reference_loads_from_any_working_directory(tmp_path, monkeypatch):
    from panini.request import load_reference
    monkeypatch.chdir(tmp_path)
    assert len(load_reference()) == 162


def test_missing_reference_warns(tmp_path, capsys):
    from panini.request import load_reference
    assert load_reference(tmp_path / "nope.json") == {}
    assert "warning" in capsys.readouterr().err.lower()


@pytest.mark.parametrize("text,key", [("gamḷ", "gam"), ("paṭha", "paṭh"), ("ḍupacaṣ", "pac"), ("Bhū", "bhū"), ("PAṬH", "paṭh")])
def test_lookup_ignores_nasal_sign_and_case(text, key):
    assert lookup_root(text).key == key


def test_lexicon_pada_class_agrees_with_root_markers():
    # availability() reads Root.pada; the engine reads the markers (1.3.12, 1.3.72, 1.3.78).
    from panini.model import Term, TermKind
    for root in ROOTS.values():
        t = Term.from_upadesha(TermKind.ROOT, root.upadesha)
        derived = "A" if "anudattet" in t.tags else "U" if ("svaritet" in t.tags or root.upadesha.endswith("Y")) else "P"
        assert root.pada == derived, root.key
