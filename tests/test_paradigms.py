# tests/test_paradigms.py
import json, pytest
from panini.request import REFERENCE_PATH
from panini.engine import derive
from panini.derivation import Status
from panini.lexicon import FEATURED
from panini.request import all_requests, availability

REF = json.loads(REFERENCE_PATH.read_text())

_SLOT = lambda code: [r.key for r in all_requests([code]) if availability(r) is None]

# key -> explanation (mirrors docs/findings.md)
XFAIL: dict[str, str] = {
    **{k: "7.3.78 not yet implemented (Task 7)" for c in FEATURED[7:] if c not in ("01.0991", "01.1077") for k in _SLOT(c)},
    # sthā (zWA\) also shows the ṣṭ-initial problem (sṭhāti), a separate bug the sweep tracks.
    **{k: "7.3.78 not yet implemented (Task 7); also the ṣṭ-initial bug (sṭhāti)" for k in _SLOT("01.1077")},
    # Vidyut gives no form: its śad takes ātmanepada via 1.3.60 (Task 7), so active is unavailable once that lands.
    **{k: "no active form once 1.3.60 lands (Task 7)" for k in _SLOT("01.0991")},
}


def _check(req, request):
    if req.key in XFAIL:
        request.applymarker(pytest.mark.xfail(reason=XFAIL[req.key], strict=True))
    d = derive(req)
    assert d.status is Status.OK, d.message
    assert [d.result, *d.alternatives] == REF[req.key]


FAST = [r for r in all_requests(FEATURED) if availability(r) is None]
ALL = [r for r in all_requests() if availability(r) is None]


@pytest.mark.parametrize("req", FAST, ids=lambda r: r.key)
def test_form_matches_reference(req, request):
    _check(req, request)


@pytest.mark.slow
@pytest.mark.parametrize("req", ALL, ids=lambda r: r.key)
def test_form_matches_reference_whole_class(req, request):
    _check(req, request)


def test_edhete_order():
    from panini.request import parse_request
    o = [i for s in derive(parse_request("edh", "laṭ", 3, "du", "middle")).steps for i in s.rule_ids]
    for a, b in [("3.4.79", "7.2.81"), ("7.2.81", "6.1.66"), ("6.1.66", "6.1.87")]:
        assert o.index(a) < o.index(b)
