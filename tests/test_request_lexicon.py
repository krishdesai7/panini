# tests/test_request_lexicon.py
import json, unicodedata, pytest
from pathlib import Path
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
    ref = json.loads(Path("tests/data/reference_forms.json").read_text())
    avail = [r.key for r in all_requests() if availability(r) is None]
    assert sorted(avail) == sorted(ref) and len(ref) == 162
