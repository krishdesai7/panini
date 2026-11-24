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
