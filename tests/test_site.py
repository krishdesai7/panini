# tests/test_site.py
import json, re
from pathlib import Path
from panini.site.build import build_site, site_data
from panini.derivation import Status

def test_site_data_covers_everything():
    d = site_data()
    assert len(d["roots"]) == 7 and len(d["derivations"]) == 252
    assert d["derivations"]["edh|laṭ|P|3|sg"]["status"] == "unavailable"

def test_build_without_fonts(tmp_path, capsys):
    out = build_site(tmp_path / "p.html", style_dir=tmp_path / "nope")
    html = out.read_text()
    assert "warning" in capsys.readouterr().err.lower()
    data = json.loads(re.search(r'<script type="application/json" id="data">(.*?)</script>', html, re.S).group(1))
    assert data["derivations"]["paṭh|laṭ|P|3|sg"]["result"] == "paṭhati"
    urls = set(re.findall(r"https?://[^\s\"')]+", html)) - {"http://www.w3.org/2000/svg"}  # SVG namespace, not a fetch
    assert not urls

def test_one_failing_derivation_does_not_abort(monkeypatch, tmp_path):
    import panini.site.build as b
    real = b.derive
    def flaky(req, **kw):
        if req.key == "gam|laṭ|P|3|sg":
            raise RuntimeError("boom")
        return real(req, **kw)
    monkeypatch.setattr(b, "derive", flaky)
    assert site_data()["derivations"]["gam|laṭ|P|3|sg"]["status"] == "error"


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
    d = site_data()
    assert d["sutras"]["1.3.78"]["text"] == "śeṣāt kartari parasmaipadam"
    assert "9.9.1" not in d["sutras"]   # toy rules stay out
    bhu = next(r for r in d["roots"] if r["key"] == "bhū")
    assert bhu["class_label"] == "class 1 · thematic, full grade"
    assert bhu["upadesha_iast"] == "bhū" and next(r for r in d["roots"] if r["key"] == "paṭh")["upadesha_iast"] == "paṭhã"


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
