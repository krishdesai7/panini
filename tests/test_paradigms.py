# tests/test_paradigms.py
import json, pytest
from pathlib import Path
from panini.engine import derive
from panini.derivation import Status
from panini.request import all_requests, availability

REF = json.loads(Path("tests/data/reference_forms.json").read_text())
XFAIL: dict[str, str] = {}   # key -> explanation (mirrors docs/findings.md)
IN_SCOPE = lambda r: r.lakara.iast == "laṭ" and r.voice.name == "ACTIVE"   # widened in Tasks 8 and 9

CASES = [r for r in all_requests() if availability(r) is None and IN_SCOPE(r)]

@pytest.mark.parametrize("req", CASES, ids=lambda r: r.key)
def test_form_matches_reference(req):
    if req.key in XFAIL:
        pytest.xfail(XFAIL[req.key])
    d = derive(req)
    assert d.status is Status.OK, d.message
    assert [d.result, *d.alternatives] == REF[req.key]
