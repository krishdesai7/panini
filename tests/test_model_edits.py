# tests/test_model_edits.py
from typing import ClassVar

import pytest

from panini.edits import (
    DeleteSounds,
    EditConflict,
    Ekadesha,
    MarkIt,
    ReplaceSounds,
    apply_edit,
    apply_simultaneous,
)
from panini.meta import sthanivat_note, substitute_term
from panini.model import (
    Coreference,
    Intent,
    Number,
    Site,
    Sound,
    Span,
    State,
    Term,
    TermKind,
    Time,
)

INTENT = Intent(Time.PRESENT, Coreference.NONE, Number.ONE, False)


def test_from_upadesha_nasal_and_accent_tags() -> None:
    t = Term.from_upadesha(TermKind.ROOT, "eDa~\\")
    assert t.text == "eDa"
    assert t.sounds[-1].nasal
    assert "anudattet" in t.tags


def test_mark_then_delete_keeps_marker_memory() -> None:
    s = State((Term.from_upadesha(TermKind.TIN, "tip"),), INTENT)
    s = apply_edit(s, (MarkIt(0, (2,), frozenset("p")),))
    assert s.terms[0].sounds[2].it
    s = apply_edit(s, (DeleteSounds(0, (2,)),))
    assert s.terms[0].text == "ti"
    assert s.terms[0].has_marker("p")


def test_sthanivat_inherits_markers() -> None:
    la = Term(TermKind.LA, "laN", (), markers=frozenset("N"))
    ti = substitute_term(la, TermKind.TIN, "tip")
    assert ti.has_marker("N")
    assert "1.1.56" in sthanivat_note(ti)


def test_ekadesha_and_simultaneous_conflict() -> None:
    s = State(
        (
            Term.from_upadesha(TermKind.ROOT, "Bava"),
            Term.from_upadesha(TermKind.TIN, "anti"),
        ),
        INTENT,
    )
    out = apply_edit(s, (Ekadesha(0, 1, (Sound("a"),)),))
    assert out.terms[0].text == "Bava"
    assert out.terms[1].text == "nti"
    e1 = (ReplaceSounds(0, 3, 4, ()),)
    e2 = (ReplaceSounds(0, 3, 4, ()),)
    with pytest.raises(EditConflict):
        apply_simultaneous(s, [e1, e2])


def test_site_overlap() -> None:
    assert Site((Span(0, 1, 2),)).overlaps(Site((Span(0, 0, -1),)))
    assert not Site((Span(0, 0, 1),)).overlaps(Site((Span(1, 0, 1),)))


def test_substantive_change_marks_term_vikrta_but_marker_deletion_does_not() -> None:
    s = State((Term.from_upadesha(TermKind.TIN, "tip"),), INTENT)
    s = apply_edit(s, (MarkIt(0, (2,), frozenset("p")),))
    s = apply_edit(s, (DeleteSounds(0, (2,)),))
    assert "vikrta" not in s.terms[0].tags
    s = apply_edit(s, (ReplaceSounds(0, 0, 1, (Sound("d"),)),))
    assert "vikrta" in s.terms[0].tags


# -- substitution inside an ekādeśa (meta.substitution_edit) -----------------


class _ToyMerge:
    """A toy ekādeśa rule: a+i → e, a+u → o, i+a → y, u+a → v."""

    TABLE: ClassVar[dict[str, str]] = {"ai": "e", "au": "o", "ia": "y", "ua": "v"}
    merge = staticmethod(lambda x, y: _ToyMerge.TABLE.get(x + y))


def _terms(*texts) -> State:
    from panini.model import Coreference, Intent, Number, State, Term, TermKind, Time

    ts = tuple(Term.from_upadesha(TermKind.ROOT, t) for t in texts)
    return State(ts, Intent(Time.PRESENT, Coreference.NONE, Number.ONE, False))


def _chars(state: State) -> list[str]:
    return ["".join(s.char for s in t.sounds) for t in state.terms]


def test_substitute_takes_the_place_of_the_root_in_an_ekadesha_at_its_start() -> None:
    from panini.edits import Ekadesha
    from panini.meta import substitution_edit

    st = apply_edit(_terms("a", "i"), (Ekadesha(0, 1, (Sound("e"),), "9.9.8"),))
    assert _chars(st) == ["e", ""]
    out = apply_edit(st, substitution_edit(st, 1, "ut", lambda rid: _ToyMerge))
    # the stem does not begin with the sound the ekādeśa absorbed (i): a + u → o, then t
    assert _chars(out) == ["o", "t"]
    assert out.terms[0].sounds[-1].ekadesha_inputs == ("a", "u")


def test_substitution_without_ekadesha_is_a_plain_replacement() -> None:
    from panini.meta import substitution_edit

    st = _terms("pi")
    assert _chars(apply_edit(st, substitution_edit(st, 0, "xyz"))) == ["xyz"]


def test_substitute_that_cannot_combine_is_refused() -> None:
    from panini.edits import Ekadesha
    from panini.meta import substitution_edit

    st = apply_edit(_terms("a", "i"), (Ekadesha(0, 1, (Sound("e"),), "9.9.8"),))
    with pytest.raises(ValueError, match="does not apply"):
        substitution_edit(st, 1, "ta", lambda rid: _ToyMerge)
