# tests/test_site.py
import json, re, threading
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen
from panini.lexicon import FEATURED, ROOTS
from panini.site.build import build_site, page_html, root_derivations, root_entries, site_data
from panini.site.serve import make_server
from panini.derivation import Status

def test_site_data_covers_everything():
    d = site_data(FEATURED, embed_all_roots=False)
    assert len(d["roots"]) == len(FEATURED) and len(d["derivations"]) == len(FEATURED) * 36
    assert d["derivations"]["01.0002|laṭ|P|3|sg"]["status"] == "unavailable"


def test_static_site_embeds_featured_only():
    d = site_data(FEATURED, embed_all_roots=False)
    assert [r["key"] for r in d["roots"]] == list(FEATURED) and "01.0074|laṭ|P|3|sg" not in d["derivations"]


def test_root_entries_cover_every_root_and_say_why_one_is_unavailable():
    entries = {e["key"]: e for e in root_entries()}
    assert len(entries) == len(ROOTS)
    assert entries["01.1092"]["unavailable"] and entries["01.0001"]["unavailable"] is None
    assert entries["01.0991"]["pada"] == "A"   # śad, by 1.3.60
    assert {"name", "upadesha_iast", "meaning", "meaning_kind", "gana", "class_label"} <= set(entries["01.0001"])


def test_api_root_and_404():
    srv = make_server(port=0, style_dir=Path("/nonexistent"))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    try:
        d = json.load(urlopen(base + "/api/root/01.0074"))["derivations"]
        assert d["01.0074|laṭ|P|3|sg"]["result"] == "krandati"
        assert json.load(urlopen(base + "/api/root/01.1092"))["derivations"]["01.1092|laṭ|P|3|sg"]["status"] == "unavailable"
        with pytest.raises(HTTPError) as e:
            urlopen(base + "/api/root/99.9999")
        assert e.value.code == 404 and "error" in json.load(e.value)
        page = urlopen(base + "/").read().decode()
        data = json.loads(re.search(r'<script type="application/json" id="data">(.*?)</script>', page, re.S).group(1))
        assert data["source"] == "server" and len(data["roots"]) == len(ROOTS) and data["derivations"] == {}
    finally:
        srv.shutdown()
        srv.server_close()


def test_page_html_has_no_external_urls():
    html = page_html({**site_data([], embed_all_roots=True), "source": "server"}, Path("/nonexistent"))
    assert not set(re.findall(r"https?://[^\s\"')]+", html)) - {"http://www.w3.org/2000/svg"}

def test_build_without_fonts(tmp_path, capsys):
    out = build_site(tmp_path / "p.html", style_dir=tmp_path / "nope")
    html = out.read_text()
    assert "warning" in capsys.readouterr().err.lower()
    data = json.loads(re.search(r'<script type="application/json" id="data">(.*?)</script>', html, re.S).group(1))
    assert data["derivations"]["01.0381|laṭ|P|3|sg"]["result"] == "paṭhati"
    urls = set(re.findall(r"https?://[^\s\"')]+", html)) - {"http://www.w3.org/2000/svg"}  # SVG namespace, not a fetch
    assert not urls

def test_one_failing_derivation_does_not_abort(monkeypatch, tmp_path):
    import panini.site.build as b
    real = b.derive
    def flaky(req, **kw):
        if req.key == "01.1137|laṭ|P|3|sg":
            raise RuntimeError("boom")
        return real(req, **kw)
    monkeypatch.setattr(b, "derive", flaky)
    root_derivations.cache_clear()
    try:
        assert root_derivations("01.1137")["01.1137|laṭ|P|3|sg"]["status"] == "error"
    finally:
        root_derivations.cache_clear()


import shutil
import subprocess

import pytest

APP_JS = Path(__file__).parent.parent / "src/panini/site/app.js"


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
@pytest.mark.parametrize("hash_, expected", [
    ("#paṭh/laṭ/P/3/sg", {"root": "paṭh", "key": "paṭh|laṭ|P|3|sg"}),
    ("#pa%E1%B9%ADh/la%E1%B9%AD/P/3/sg", {"root": "paṭh", "key": "paṭh|laṭ|P|3|sg"}),
    ("#edh", {"root": "edh", "key": None}),
    ("#xyz/laṭ/P/9/sg", {"root": "bhū", "key": None}),
    ("#bhū/laṭ/P/9/sg", {"root": "bhū", "key": None}),
    ("", {"root": "bhū", "key": None}),
    ("#%E0%A4", {"root": "bhū", "key": None}),
])
def test_parse_hash_falls_back_safely(hash_, expected):
    data = {"roots": [{"key": "bhū"}, {"key": "paṭh"}, {"key": "edh"}],
            "derivations": {"paṭh|laṭ|P|3|sg": {}, "bhū|laṭ|P|3|sg": {}}}
    script = (f"const {{parseHash}} = require({json.dumps(str(APP_JS.resolve()))});"
              f"console.log(JSON.stringify(parseHash({json.dumps(hash_)}, {json.dumps(data)})))")
    out = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True).stdout
    assert json.loads(out) == expected


def test_site_data_carries_sutra_texts_and_plain_class_labels():
    d = site_data(FEATURED, embed_all_roots=False)
    assert d["sutras"]["1.3.78"]["text"] == "śeṣāt kartari parasmaipadam"
    assert "9.9.1" not in d["sutras"]   # toy rules stay out
    bhu = next(r for r in d["roots"] if r["key"] == "01.0001")
    assert bhu["class_label"] == "class 1 · thematic, full grade"
    assert bhu["upadesha_iast"] == "bhū" and next(r for r in d["roots"] if r["key"] == "01.0381")["upadesha_iast"] == "paṭhã"


def _node(expr: str):
    script = f"const app = require({json.dumps(str(APP_JS.resolve()))}); console.log(JSON.stringify({expr}))"
    return json.loads(subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True).stdout)


SUTRAS = {"1.3.78": {"text": "śeṣāt kartari parasmaipadam", "gloss": "After all other roots, the parasmaipada endings are used."}}


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_split_citations_marks_known_sutra_numbers():
    parts = _node(f"app.splitCitations('active only (1.3.78; see 9.9.9)', {json.dumps(SUTRAS)})")
    assert parts == [["active only (", None], ["1.3.78", "1.3.78"], ["; see 9.9.9)", None]]


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_sutra_title_is_text_then_gloss():
    assert _node(f"app.sutraTitle('1.3.78', {json.dumps(SUTRAS)})") == (
        "1.3.78 śeṣāt kartari parasmaipadam\nAfter all other roots, the parasmaipada endings are used.")


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_tooltip_sits_below_the_word_and_stays_on_screen():
    pos = _node("app.tipPosition({left: 100, bottom: 50, top: 30}, {width: 200, height: 40}, {width: 1000, height: 800})")
    assert pos == {"left": 100, "top": 56}
    right_edge = _node("app.tipPosition({left: 950, bottom: 50, top: 30}, {width: 200, height: 40}, {width: 1000, height: 800})")
    assert right_edge["left"] == 1000 - 200 - 8
    bottom_edge = _node("app.tipPosition({left: 100, bottom: 790, top: 770}, {width: 200, height: 40}, {width: 1000, height: 800})")
    assert bottom_edge["top"] == 770 - 40 - 6


def test_page_uses_instant_tooltips_not_title_attributes(tmp_path):
    html = build_site(tmp_path / "p.html", style_dir=tmp_path / "nope").read_text()
    assert "data-tip" in html and 'title: title' not in html


def test_heading_monogram_draws_the_dot_and_keeps_the_real_name_for_screen_readers(tmp_path):
    html = build_site(tmp_path / "p.html", style_dir=tmp_path / "nope").read_text()
    assert 'aria-label="Pāṇini"' in html and 'class="dot-below"' in html


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_split_terms_parses_modern_and_traditional_markup():
    assert _node("app.splitTerms('the {middle|ātmanepada} voice (1.3.78)')") == [
        ["the ", None], ["middle", "ātmanepada"], [" voice (1.3.78)", None]]


def test_site_data_explains_what_markers_do():
    notes = site_data(FEATURED, embed_all_roots=False)["markers"]
    assert "primary endings" in notes["lãṭ|ṭ"] and "3.4.79" in notes["lãṭ|ṭ"]
    assert "secondary endings" in notes["lãṅ|ṅ"]
    assert "1.3.12" in notes["edhã|ã"]


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_marker_tip_prefers_a_specific_note():
    notes = {"lãṭ|ṭ": "primary endings"}
    assert _node(f"app.markerTip('lãṭ', 'ṭ', {json.dumps(notes)})") == "marker (it) · primary endings"
    assert _node(f"app.markerTip('tip', 'x', {json.dumps(notes)})") == "marker (it): deleted by 1.3.9"


def test_step_views_carry_the_term_upadesha(tmp_path):
    d = site_data(FEATURED, embed_all_roots=False)["derivations"]["01.0001|laṭ|P|3|sg"]
    assert any(v.get("upadesha") == "lãṭ" for s in d["steps"] for v in s["after"])


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_marker_tip_falls_back_to_a_note_for_the_sound_alone():
    notes = {"*|ũ": "carrier vowel of rũ"}
    assert _node(f"app.markerTip('mas', 'ũ', {json.dumps(notes)})") == "marker (it) · carrier vowel of rũ"


def test_lakara_marker_notes_name_lakaras_not_tenses():
    notes = site_data(FEATURED, embed_all_roots=False)["markers"]
    assert "liṭ (perfect)" in notes["lãṭ|ṭ"] and "tenses" not in notes["lãṭ|ṭ"]
    assert "laṅ (imperfect)" in notes["lãṅ|ṅ"] and "tenses" not in notes["lãṅ|ṅ"]


def test_site_data_has_a_glossary_for_lakara_names():
    g = site_data(FEATURED, embed_all_roots=False)["glossary"]
    assert g["laṭ"] == "present imperfective" and g["laṅ"] == "past imperfective"


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_glossary_words_get_tooltips_only_as_whole_words():
    g = {"laṅ": "past imperfective"}
    assert _node(f"app.splitGlossary('in laṅ (marked ṅ), not lãṅ or laṅa', {json.dumps(g)})") == [
        ["in ", None], ["laṅ", "past imperfective"], [" (marked ṅ), not lãṅ or laṅa", None]]


def test_root_marker_vowel_note_explains_why_it_is_there():
    note = site_data(FEATURED, embed_all_roots=False)["markers"]["paṭhã|ã"]
    assert "1.3.3" in note and "pitch" in note


@pytest.fixture(scope="module")
def all_roots_data():
    d = site_data([], embed_all_roots=True)
    return {"roots": d["roots"], "featured": d["featured"], "derivations": {}, "source": "server"}


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
@pytest.mark.parametrize("q, first", [("krand", "01.0074"), ("KRAND-", "01.0074"), ("01.0074", "01.0074"),
                                      ("stha", "01.1077"), ("sthā", "01.1077"), ("smṛ", "01.0919"), ("āhvāne", "01.0073")])
def test_search_roots(q, first, all_roots_data):
    d = all_roots_data
    hits = _node(f"app.searchRoots({json.dumps(q)}, {json.dumps(d['roots'])}, {json.dumps(d['featured'])})")
    assert hits and hits[0]["key"] == first
    if q == "āhvāne":   # the meaning is shared by kand, krand, kruś...: list order, none featured
        assert "01.0074" in [h["key"] for h in hits]


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_fold_strips_every_combining_mark():
    assert _node("app.fold('Daṃś-')") == "dams"
    assert _node("app.fold('sthā')") == "stha"
    assert _node("app.fold('gamḷ̃')") == "gaml"


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
@pytest.mark.parametrize("hash_, expected", [
    ("#paṭh/laṭ/P/3/sg", {"root": "01.0381", "key": "01.0381|laṭ|P|3|sg"}),
    ("#01.0074", {"root": "01.0074", "key": None}),
    ("#99.9999", {"root": "01.0001", "key": None}),
])
def test_parse_hash_codes_and_old_names(hash_, expected, all_roots_data):
    d = {**all_roots_data, "source": "static",
         "derivations": {"01.0381|laṭ|P|3|sg": {}, "01.0001|laṭ|P|3|sg": {}}}
    assert _node(f"app.parseHash({json.dumps(hash_)}, {json.dumps(d)})") == expected


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_parse_hash_keeps_a_wellformed_key_on_a_server_page_before_the_forms_arrive(all_roots_data):
    got = _node(f"app.parseHash('#01.0074/laṭ/P/3/sg', {json.dumps(all_roots_data)})")
    assert got == {"root": "01.0074", "key": "01.0074|laṭ|P|3|sg"}
