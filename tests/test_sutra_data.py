import pytest

from panini.rules import ALL_RULES
from panini.rules.base import sutra_info

CITED = ["1.4.99", "1.4.100", "1.4.101", "1.4.102", "1.4.104", "1.4.105", "1.4.107", "1.4.108",
         "1.4.21", "1.4.22", "1.1.56", "1.1.46", "1.1.3", "1.1.51", "1.4.2", "3.4.77", "6.1.84", "6.1.85", "1.1.50", "1.1.64"]


@pytest.mark.parametrize("rule_id", [r.id for r in ALL_RULES] + CITED)
def test_every_rule_and_cited_sutra_has_text_and_gloss(rule_id):
    text, gloss = sutra_info(rule_id)
    assert text and gloss and text != "toy"


def test_marker_rule_glosses_avoid_jargon():
    t7, g7 = sutra_info("1.3.7")
    t8, g8 = sutra_info("1.3.8")
    assert "row" not in g7 and "row" not in g8
    assert "{secondary nominal suffix|taddhita}" in g8


def test_no_bare_jargon_left_in_these_glosses():
    import re
    for rid in ("7.3.101", "8.3.24", "8.4.58"):
        bare = re.sub(r"\{[^}]*\}", "", sutra_info(rid)[1])
        assert "anusvāra" not in bare and "y v r l ñ m" not in bare, rid
