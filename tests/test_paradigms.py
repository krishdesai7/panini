# tests/test_paradigms.py
import json, pytest
from pathlib import Path
from panini.engine import derive
from panini.derivation import Status
from panini.request import all_requests, availability

REF = json.loads(Path("tests/data/reference_forms.json").read_text())
XFAIL: dict[str, str] = {}   # key -> explanation (mirrors docs/findings.md)
IN_SCOPE = lambda r: True

CASES = [r for r in all_requests() if availability(r) is None and IN_SCOPE(r)]

@pytest.mark.parametrize("req", CASES, ids=lambda r: r.key)
def test_form_matches_reference(req):
    if req.key in XFAIL:
        pytest.xfail(XFAIL[req.key])
    d = derive(req)
    assert d.status is Status.OK, d.message
    assert [d.result, *d.alternatives] == REF[req.key]


def test_edhete_order():
    from panini.request import parse_request
    o = [i for s in derive(parse_request("edh", "laṭ", 3, "du", "middle")).steps for i in s.rule_ids]
    for a, b in [("3.4.79", "7.2.81"), ("7.2.81", "6.1.66"), ("6.1.66", "6.1.87")]:
        assert o.index(a) < o.index(b)
