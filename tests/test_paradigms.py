# tests/test_paradigms.py
import json

import pytest

from panini.derivation import Status
from panini.engine import derive
from panini.lexicon import FEATURED
from panini.request import REFERENCE_PATH, all_requests, availability

REF = json.loads(REFERENCE_PATH.read_text())


def _slots(code: str) -> list[str]:
    return [r.key for r in all_requests([code]) if availability(r) is None]


# key -> explanation (mirrors docs/findings.md)
XFAIL: dict[str, str] = {
    # Vidyut also gives ārchat: 8.4.65 jharo jhari savarṇe optionally drops one c of rcch (docs/findings.md).
    **{
        k: "8.4.65 optional cluster simplification not modelled (ārchat)"
        for k in _slots("01.1086")
        if "|laṅ|" in k
    },
}


def _check(req, request) -> None:
    if req.key in XFAIL:
        request.applymarker(pytest.mark.xfail(reason=XFAIL[req.key], strict=True))
    d = derive(req)
    assert d.status is Status.OK, d.message
    assert [d.result, *d.alternatives] == REF[req.key]


FAST = [r for r in all_requests(FEATURED) if availability(r) is None]
ALL = [r for r in all_requests() if availability(r) is None]


@pytest.mark.parametrize("req", FAST, ids=lambda r: r.key)
def test_form_matches_reference(req, request) -> None:
    _check(req, request)


@pytest.mark.slow
@pytest.mark.parametrize("req", ALL, ids=lambda r: r.key)
def test_form_matches_reference_whole_class(req, request) -> None:
    _check(req, request)


def test_edhete_order() -> None:
    from panini.request import parse_request

    o = [
        i
        for s in derive(parse_request("edh", "laṭ", 3, "du", "middle")).steps
        for i in s.rule_ids
    ]
    for a, b in [("3.4.79", "7.2.81"), ("7.2.81", "6.1.66"), ("6.1.66", "6.1.87")]:
        assert o.index(a) < o.index(b)
