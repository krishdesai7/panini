"""Meta-rule behaviour of the engine, tested with toy rules (ids 9.9.x)."""

import json

import pytest

from panini.derivation import Derivation, Status, StepRecord
from panini.edits import DeleteSounds, InsertSounds, ReplaceSounds
from panini.engine import StepLimitExceeded, final_text, run
from panini.model import (
    Coreference,
    Intent,
    Number,
    Site,
    Sound,
    State,
    Term,
    TermKind,
    Time,
)
from panini.resolver import Loser, UnresolvedConflict
from panini.rules.base import Optionality, Rule

INTENT = Intent(Time.PRESENT, Coreference.NONE, Number.ONE, False)


def S(text: str) -> State:  # ruff: ignore[invalid-function-name] -- reads like a constructor
    return State((Term.from_upadesha(TermKind.ROOT, text),), INTENT)


def replace_rule(
    rule_id: str, old: str, new: str, *, only_at: int | None = None, **kw
) -> Rule:
    def find(st: State) -> list[Site]:
        return [
            Site.at(0, k)
            for k, s in enumerate(st.terms[0].sounds)
            if s.char == old and (only_at is None or k == only_at)
        ]

    def rewrite(_st: State, site: Site) -> tuple[ReplaceSounds]:
        k = site.spans[0].start
        return (ReplaceSounds(0, k, k + 1, (Sound(new),)),)

    return Rule(rule_id, find, rewrite, **kw)


def ids(steps: tuple[StepRecord, ...]) -> list[str]:
    return [i for s in steps for i in s.rule_ids]


def test_blocking_special_beats_general() -> None:
    general = replace_rule("9.9.2", "a", "i")
    special = replace_rule("9.9.3", "a", "u", only_at=0, blocks=("9.9.2",))
    state, steps, _ = run(S("aba"), [general, special])
    assert final_text(state) == "ubi"
    assert Loser("9.9.2", "blocked by 9.9.3") in steps[0].losers


def test_collective_blocking() -> None:
    a = replace_rule("9.9.2", "a", "i")
    b = replace_rule("9.9.5", "a", "e", only_at=0)
    c = replace_rule("9.9.4", "a", "o", only_at=0, blocks=("9.9.2", "9.9.5"))
    state, steps, _ = run(S("aba"), [a, b, c])
    assert final_text(state) == "obi"
    losers = {loser for s in steps for loser in s.losers}
    assert Loser("9.9.2", "blocked by 9.9.4") in losers
    assert Loser("9.9.5", "blocked by 9.9.4") in losers


def test_nisedha_keeps_blocking() -> None:
    general = replace_rule("9.9.2", "a", "i")
    nisedha = Rule(
        "9.9.6",
        lambda st: [Site.at(0, 0)] if st.terms[0].adi == "a" else [],
        lambda st, site: (),
        blocks=("9.9.2",),
    )
    state, steps, _ = run(S("ab"), [general, nisedha])
    assert final_text(state) == "ab"
    assert ids(steps) == ["9.9.6"]


def test_nitya_preference() -> None:
    # X deletes a final "su"; Y turns d into a before s. X applies whether or not
    # Y has applied; after X, Y has nothing to apply to. So X is nitya and goes first.
    def find_x(st) -> list[Site]:
        t = st.terms[0].text
        return [Site.at(0, len(t) - 2, len(t))] if t.endswith("su") else []

    def rewrite_x(_st, site) -> tuple[DeleteSounds]:
        sp = site.spans[0]
        return (DeleteSounds(0, tuple(range(sp.start, sp.end))),)

    x = Rule("9.9.7", find_x, rewrite_x)

    def find_y(st) -> list[Site]:
        t = st.terms[0].text
        return [
            Site.at(0, k) for k in range(len(t) - 1) if t[k] == "d" and t[k + 1] == "s"
        ]

    y = Rule(
        "9.9.8",
        find_y,
        lambda st, site: (
            ReplaceSounds(
                0, site.spans[0].start, site.spans[0].start + 1, (Sound("a"),)
            ),
        ),
    )
    state, steps, _ = run(S("tadsu"), [x, y])
    assert final_text(state) == "tad"
    assert ids(steps) == ["9.9.7"]
    assert (
        Loser("9.9.8", "deferred: 9.9.7 {applies either way|nitya}") in steps[0].losers
    )


def test_nitya_counts_one_operation_across_sibling_rules() -> None:
    # bU: G1 (final U -> o) and Y (final U -> uv) bleed each other as rules, but after Y the
    # sibling G2 (penultimate u -> o, the same operation) makes the same change on the same
    # term. So the operation survives Y and Y does not survive it: G1 is nitya (bhū: guṇa
    # 7.3.84/7.3.86 over uvaṅ 6.4.77).
    g1 = replace_rule("9.9.10", "U", "o", operation="g")
    y = Rule(
        "9.9.11",
        lambda st: [Site.at(0, 1)] if st.terms[0].text == "bU" else [],
        lambda st, site: (ReplaceSounds(0, 1, 2, (Sound("u"), Sound("v"))),),
    )
    g2 = replace_rule("9.9.12", "u", "o", only_at=1, operation="g")
    state, steps, _ = run(S("bU"), [g1, y, g2])
    assert final_text(state) == "bo"
    assert ids(steps) == ["9.9.10"]
    assert (
        Loser(
            "9.9.11",
            "deferred: 9.9.10 {applies either way|nitya}: after 9.9.11, "
            "9.9.12 still applies to the same sound",
        )
        in steps[0].losers
    )


def test_nitya_operation_survives_on_the_same_vowel_whatever_its_result() -> None:
    # tF: G1 (final F -> ar) and Y (final F -> ir) bleed each other; after Y the sibling G2 still
    # applies to the same vowel (i -> e), with a different result. The operation survives Y, so
    # G1 is nitya (tṝ: guṇa over 7.1.100, tarati; the user's ruling, slice 1.6).
    def g1_rewrite(_st, site):
        return (ReplaceSounds(0, 1, 2, (Sound("a"), Sound("r"))),)

    g1 = Rule(
        "9.9.10",
        lambda st: [Site.at(0, 1)] if st.terms[0].text == "tF" else [],
        g1_rewrite,
        operation="g",
    )
    y = Rule(
        "9.9.11",
        lambda st: [Site.at(0, 1)] if st.terms[0].text == "tF" else [],
        lambda st, site: (ReplaceSounds(0, 1, 2, (Sound("i"), Sound("r"))),),
    )
    g2 = replace_rule("9.9.12", "i", "e", only_at=1, operation="g")
    state, steps, _ = run(S("tF"), [g1, y, g2])
    assert final_text(state) == "tar"
    assert ids(steps) == ["9.9.10"]


def test_sibling_rules_without_a_shared_operation_still_conflict() -> None:
    g1 = replace_rule("9.9.10", "U", "o")
    y = Rule(
        "9.9.11",
        lambda st: [Site.at(0, 1)] if st.terms[0].text == "bU" else [],
        lambda st, site: (ReplaceSounds(0, 1, 2, (Sound("u"), Sound("v"))),),
    )
    g2 = replace_rule("9.9.12", "u", "o", only_at=1)
    with pytest.raises(UnresolvedConflict):
        run(S("bU"), [g1, y, g2])


def test_commuting_tie_lowest_id() -> None:
    a = replace_rule("9.9.2", "a", "i")
    b = replace_rule("9.9.9", "b", "p")
    state, steps, _ = run(S("ab"), [b, a])
    assert final_text(state) == "ip"
    assert ids(steps) == ["9.9.2", "9.9.9"]


def test_noncommuting_tie_raises() -> None:
    a = replace_rule("9.9.2", "a", "i")
    b = replace_rule("9.9.5", "a", "e", only_at=0)
    with pytest.raises(UnresolvedConflict) as e:
        run(S("ab"), [a, b])
    assert set(e.value.rule_ids) == {"9.9.2", "9.9.5"}


def test_tripadi_one_pass() -> None:
    earlier = replace_rule("9.9.1", "c", "k", section_override="tripadi")
    later = replace_rule("9.9.2", "a", "c", section_override="tripadi")
    state, steps, _ = run(S("a"), [earlier, later])
    assert final_text(state) == "c"
    assert ids(steps) == ["9.9.2"]


def test_step_limit() -> None:
    grow = Rule(
        "9.9.2",
        lambda st: [Site.at(0, len(st.terms[0].sounds), len(st.terms[0].sounds))],
        lambda st, site: (InsertSounds(0, site.spans[0].start, (Sound("a"),)),),
    )
    with pytest.raises(StepLimitExceeded):
        run(S("a"), [grow], max_steps=20)


def test_optional_va_alternative() -> None:
    va = replace_rule(
        "9.9.4", "a", "o", section_override="tripadi", optional=Optionality.VA
    )
    state, steps, alternatives = run(S("ba"), [va])
    assert final_text(state) == "bo"
    assert alternatives == ("ba",)
    assert steps[-1].alternatives == ("ba",)
    assert "also correct: ba" in steps[-1].note


def test_derivation_to_json_roundtrips_types() -> None:
    general = replace_rule("9.9.2", "a", "i")
    special = replace_rule("9.9.3", "a", "u", only_at=0, blocks=("9.9.2",))
    state, steps, alts = run(S("aba"), [general, special])
    d = Derivation(
        {"key": "toy"}, Status.OK, final_text(state), alts, None, steps, None
    )
    data = json.loads(json.dumps(d.to_json()))
    assert data["status"] == "ok"
    assert data["steps"][0]["after"][0]["iast"] == "abi"


def test_commuting_candidate_applies_before_an_open_conflict() -> None:
    # 9.9.2 and 9.9.5 conflict on "a"; 9.9.8 (a higher id) commutes with both and, once applied,
    # enables 9.9.6, a no-op niṣedha that blocks 9.9.5 — so the conflict dissolves.
    a = replace_rule("9.9.2", "a", "i")
    b = replace_rule("9.9.5", "a", "e", only_at=0)
    c = replace_rule("9.9.8", "b", "p")
    d = Rule(
        "9.9.6",
        lambda st: [Site.at(0, 0)] if "p" in st.terms[0].text else [],
        lambda st, site: (),
        blocks=("9.9.5",),
    )
    state, _steps, _ = run(S("ab"), [a, b, c, d])
    assert final_text(state) == "ip"


def test_orders_converging_on_the_same_final_form_are_not_a_conflict() -> None:
    # 9.9.2 a→i then 9.9.3 i→e, versus 9.9.5 a→e directly (which leaves a tag behind):
    # different intermediate states, same final form, so no UnresolvedConflict.
    from panini.edits import AddTags

    a = replace_rule("9.9.2", "a", "i")
    b = replace_rule("9.9.3", "i", "e")
    c = Rule(
        "9.9.5",
        lambda st: [Site.at(0, 0)] if st.terms[0].adi == "a" else [],
        lambda st, site: (
            ReplaceSounds(0, 0, 1, (Sound("e"),)),
            AddTags(0, frozenset({"x"})),
        ),
    )
    state, steps, _ = run(S("a"), [a, b, c])
    assert final_text(state) == "e"
    assert any(
        "both orders give e" in loser.reason for s in steps for loser in s.losers
    )


def test_declined_optional_rule_stops_blocking_in_later_alternative_branches() -> None:
    # 9.9.1 (vibhāṣā) declines b → u; it must then stop blocking 9.9.3 (b → y) everywhere,
    # including in the branch spawned afterwards by the optional 9.9.2 (a → o).
    opt = replace_rule(
        "9.9.1", "b", "u", blocks=("9.9.3",), optional=Optionality.VIBHASHA
    )
    va = replace_rule("9.9.2", "a", "o", optional=Optionality.VA)
    general = replace_rule("9.9.3", "b", "y")
    state, steps, alts = run(S("ab"), [general, opt, va])
    assert final_text(state) == "oy"
    assert "ay" in alts  # the branch without 9.9.2 still reaches the general rule
    assert ids(steps).count("9.9.1") == 1  # declined once, never offered again


def test_optional_rule_supplies_its_own_phrase() -> None:
    opt = replace_rule(
        "9.9.5",
        "b",
        "u",
        optional=Optionality.VIBHASHA,
        optional_phrase="only in sense Z, so not applied here",
    )
    _, steps, _ = run(S("ab"), [opt])
    assert "only in sense Z, so not applied here; also correct: au" in steps[0].note
    assert "vibhāṣā" not in steps[0].note
