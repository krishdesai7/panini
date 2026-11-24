# tests/test_model_edits.py
import pytest
from panini.model import Sound, Term, TermKind, State, Intent, Time, Coreference, Number, Site, Span
from panini.edits import MarkIt, DeleteSounds, ReplaceSounds, Ekadesha, apply_edit, apply_simultaneous, EditConflict
from panini.meta import substitute_term, sthanivat_note

INTENT = Intent(Time.PRESENT, Coreference.NONE, Number.ONE, False)

def test_from_upadesha_nasal_and_accent_tags():
    t = Term.from_upadesha(TermKind.ROOT, "eDa~\\")
    assert t.text == "eDa" and t.sounds[-1].nasal and "anudattet" in t.tags

def test_mark_then_delete_keeps_marker_memory():
    s = State((Term.from_upadesha(TermKind.TIN, "tip"),), INTENT)
    s = apply_edit(s, (MarkIt(0, (2,), frozenset("p")),))
    assert s.terms[0].sounds[2].it
    s = apply_edit(s, (DeleteSounds(0, (2,)),))
    assert s.terms[0].text == "ti" and s.terms[0].has_marker("p")

def test_sthanivat_inherits_markers():
    la = Term(TermKind.LA, "laN", (), markers=frozenset("N"))
    ti = substitute_term(la, TermKind.TIN, "tip")
    assert ti.has_marker("N") and "1.1.56" in sthanivat_note(ti)

def test_ekadesha_and_simultaneous_conflict():
    s = State((Term.from_upadesha(TermKind.ROOT, "Bava"), Term.from_upadesha(TermKind.TIN, "anti")), INTENT)
    out = apply_edit(s, (Ekadesha(0, 1, (Sound("a"),)),))
    assert out.terms[0].text == "Bava" and out.terms[1].text == "nti"
    e1 = (ReplaceSounds(0, 3, 4, ()),); e2 = (ReplaceSounds(0, 3, 4, ()),)
    with pytest.raises(EditConflict):
        apply_simultaneous(s, [e1, e2])

def test_site_overlap():
    assert Site((Span(0, 1, 2),)).overlaps(Site((Span(0, 0, -1),)))
    assert not Site((Span(0, 0, 1),)).overlaps(Site((Span(1, 0, 1),)))
