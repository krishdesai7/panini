"""Every step can show how its rule is read: interpretive conventions and carried-over words."""

import pytest

from panini.derivation import Status
from panini.engine import derive
from panini.request import parse_request
from panini.rules import ALL_RULES, get_rule
from panini.rules.base import sutra_info
from panini.rules.readings import READS
from panini.trace import render_text


def test_readings_only_annotate_real_rules_and_cite_known_sutras():
    ids = {r.id for r in ALL_RULES}
    assert set(READS) <= ids
    for rid, items in READS.items():
        for src, note in items:
            sutra_info(src)            # every cited sūtra has text and gloss
            assert note and src != rid


def test_most_rules_have_a_reading():
    annotated = [r.id for r in ALL_RULES if READS.get(r.id)]
    assert len(annotated) >= len(ALL_RULES) - 3


def test_step_carries_its_reading():
    d = derive(parse_request("bhū", "laṭ", 3, "sg", "active"))
    step = next(s for s in d.steps if "6.1.78" in s.rule_ids)
    assert {src for src, _ in step.reads} >= {"1.1.49", "6.1.77"}
    assert d.to_json()["steps"][0]["reads"] is not None


def test_trace_shows_readings_at_v_only():
    d = derive(parse_request("bhū", "laṭ", 3, "sg", "active"))
    assert "read via" not in render_text(d)
    assert "read via 1.1.49" in render_text(d, verbosity=1)
