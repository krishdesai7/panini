"""Every step can show how its rule is read: interpretive conventions and carried-over words."""

from panini.engine import derive
from panini.request import parse_request
from panini.rules import ALL_RULES, get_rule
from panini.rules.base import sutra_info
from panini.rules.readings import PARIBHASHA, READS
from panini.trace import render_text


def test_readings_only_annotate_real_rules_and_cite_known_sutras() -> None:
    ids = {r.id for r in ALL_RULES}
    assert set(READS) <= ids
    for rid, items in READS.items():
        for src, note in items:
            if src not in PARIBHASHA:
                sutra_info(src)  # every cited sūtra has text and gloss
            assert note
            assert src != rid


def test_most_rules_have_a_reading() -> None:
    annotated = [r.id for r in ALL_RULES if READS.get(r.id)]
    assert len(annotated) >= len(ALL_RULES) - 3


def test_step_carries_its_reading() -> None:
    d = derive(parse_request("bhū", "laṭ", 3, "sg", "active"))
    step = next(s for s in d.steps if "6.1.78" in s.rule_ids)
    assert {src for src, _ in step.reads} >= {"1.1.49", "6.1.77"}
    assert d.to_json()["steps"][0]["reads"] is not None


def test_trace_shows_readings_at_v_only() -> None:
    d = derive(parse_request("bhū", "laṭ", 3, "sg", "active"))
    assert "read via" not in render_text(d)
    assert "read via 1.1.49" in render_text(d, verbosity=1)


def test_tapara_reading_for_short_a_rules() -> None:
    for rid in ("6.1.97", "7.3.101"):
        assert "1.1.70" in {src for src, _ in READS[rid]}, rid


def test_6197_does_not_apply_at_the_end_of_a_word() -> None:
    from panini.model import Coreference, Intent, Number, State, Term, TermKind, Time

    intent = Intent(Time.PRESENT, Coreference.NONE, Number.ONE, False)
    left = Term.from_upadesha(
        TermKind.ROOT, "ca", frozenset({"pada"})
    )  # a whole word ending in a
    right = Term.from_upadesha(TermKind.ROOT, "atra")
    st = State((left, right), intent)
    assert get_rule("6.1.97").find(st) == []
    assert get_rule("6.1.101").find(st) != []
