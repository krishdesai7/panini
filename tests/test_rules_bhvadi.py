# tests/test_rules_bhvadi.py — rules added for the whole bhvādi class (slice 1.5)
import pytest
from panini.derivation import Derivation, Status
from panini.engine import derive
from panini.lexicon import lookup_root
from panini.request import OUT_OF_SCOPE, availability, parse_request


def form(code: str, tense: str = "laṭ", person: int = 3, number: str = "sg", voice: str = "active") -> Derivation:
    return derive(parse_request(code, tense, person, number, voice))


def _rule_ids(d: Derivation) -> list[str]:
    return [i for s in d.steps for i in s.rule_ids]


# -- 7.1.58 idito num dhātoḥ ---------------------------------------------

@pytest.mark.parametrize("code, tense, voice, expected", [
    ("01.0074", "laṭ", "active", "krandati"), ("01.0074", "laṅ", "active", "akrandat"),
    ("01.0100", "laṭ", "middle", "vaṅkate"), ("01.0435", "laṭ", "middle", "kampate")])
def test_idit_nasal(code, tense, voice, expected):
    d = form(code, tense, voice=voice)
    assert d.result == expected and "7.1.58" in [i for s in d.steps for i in s.rule_ids]


def test_idit_nasal_applies_once_and_cites_1147():
    d = form("01.0074")
    steps = [s for s in d.steps if "7.1.58" in s.rule_ids]
    assert len(steps) == 1 and "1.1.47" in steps[0].note
    assert any(src == "1.1.47" for src, _ in steps[0].reads)


def test_irit_root_gets_no_nasal():
    d = form("01.1143")   # dṛś, df\Si~r: i~r is the marker ir, not i
    assert "7.1.58" not in _rule_ids(d)


def test_idit_nasal_after_a_merged_initial_vowel():
    # laṅ of adi~ (and): ā + a merge (6.1.90); the merged vowel still counts as the root's (6.1.85)
    assert form("01.0064", "laṅ").result == "āndat"


def test_idit_note_uses_house_markup():
    note = next(s.note for s in form("01.0074").steps if "7.1.58" in s.rule_ids)
    assert "{i|idit}" in note and "{augment|āgama}" in note and "markers u, m" not in note


# -- 6.1.64-65 root-initial ṣ and ṇ ----------------------------------------

@pytest.mark.parametrize("code, expected", [
    ("01.0532", "stanati"),   # ṣṭana~: ṭ goes back to t
    ("01.1136", "namati"),    # ṇama~
    ("01.0970", "sthalati"),  # ṣṭhala~: ṭh goes back to th
    ("01.1072", "snāyati"),   # ṣṇai: ṇ goes back to n
    ("01.0535", "sanati"),    # ṣaṇa~: the ṇ the ṣ caused, not at the start, goes back to n
    ("01.0451", "stambhate")])
def test_root_initial_s_and_n(code, expected):
    assert form(code, voice="middle" if code == "01.0451" else "active").result == expected


def test_retroflex_undone_in_the_same_step_and_cites_the_paribhasha():
    d = form("01.0532")
    steps = [s for s in d.steps if "6.1.64" in s.rule_ids]
    assert len(steps) == 1
    assert "ṭ goes back to t" in steps[0].note
    assert "{ṣ-taught|ṣopadeśa}" in steps[0].note and "{marker|it}" not in steps[0].note
    assert any(src == "nimittāpāye naimittikasyāpy apāyaḥ" for src, _ in steps[0].reads)


def test_root_initial_n_note_names_the_taught_form():
    note = next(s.note for s in form("01.1136").steps if "6.1.65" in s.rule_ids)
    assert "{ṇ-taught|ṇopadeśa}" in note and "{marker|it}" not in note


# -- 8.2.78 upadhāyāṃ ca ---------------------------------------------------

@pytest.mark.parametrize("code, voice, expected", [
    ("01.0021", "middle", "kūrdate"), ("01.0239", "active", "hūrchati"), ("01.0650", "active", "ūrvati")])
def test_vowel_lengthened_before_upadha_r_or_v_and_consonant(code, voice, expected):
    d = form(code, voice=voice)
    assert d.result == expected and "8.2.78" in _rule_ids(d)


# -- 6.1.75 dīrghāt: tuk after a long vowel before ch ---------------------

@pytest.mark.parametrize("code, tense, expected", [
    ("01.0233", "laṭ", "mlecchati"), ("01.0238", "laṭ", "hrīcchati"),   # long e, long ī
    ("01.0541", "laṅ", "acchamat")])                                     # the augment a before ch (6.1.73)
def test_tuk_before_ch(code, tense, expected):
    d = form(code, tense)
    assert d.result == expected


def test_tuk_is_written_with_the_vowel_it_follows():
    # 6.1.71 hrasvasya tuk / 1.1.46: tuk goes at the end of the vowel, so in laṅ of cham it ends the
    # augment a's term (a t + cham), not the start of the root's
    step = next(s for s in form("01.0541", "laṅ").steps if "6.1.73" in s.rule_ids)
    assert [v.iast() for v in step.after][:2] == ["at", "cham"]


@pytest.mark.parametrize("code, expected", [("01.0237", "āñchat"), ("01.0243", "auñchat")])
def test_num_still_goes_after_a_merged_vowel_when_tuk_could_follow_it(code, expected):
    # 7.1.58 vs 6.1.75 on ā + ch: mit_position skips an augment sound, so num stays nitya and wins
    assert form(code, "laṅ").result == expected


def test_tuk_after_long_vowel_is_6175_not_6173():
    ids = _rule_ids(form("01.0233"))
    assert "6.1.75" in ids and "6.1.73" not in ids
    note = next(s.note for s in form("01.0233").steps if "6.1.75" in s.rule_ids)
    assert "long vowel" in note and "tuk" in note


# -- 8.4.40 + 8.4.53: ṣasj ------------------------------------------------

def test_sasj_palatal_then_voiced():
    d = form("01.0229")
    ids = _rule_ids(d)
    assert d.result == "sajjati"
    assert ids.index("8.4.40") < ids.index("8.4.53")


# -- 8.4.41 ṣṭunā ṣṭuḥ: the nasal of ghiṇ, ghuṇ, ghṛṇ ----------------------

@pytest.mark.parametrize("code, expected", [
    ("01.0502", "ghiṇṇate"), ("01.0503", "ghuṇṇate")])
def test_nasal_becomes_retroflex_before_retroflex_nasal(code, expected):
    d = form(code, voice="middle")
    assert d.result == expected and "8.4.41" in _rule_ids(d)


def test_rvarna_triggers_natva_by_the_varttika():
    d = form("01.0504", voice="middle")   # ghṛṇ: the num n after ṛ becomes ṇ by 8.4.1.1, so 8.4.41 has nothing left to do
    ids = _rule_ids(d)
    assert d.result == "ghṛṇṇate" and "8.4.1.1" in ids and "8.4.1" not in ids and "8.4.41" not in ids


# -- 8.4.1-2 raṣābhyāṃ no ṇaḥ samānapade ----------------------------------

def test_n_after_r_with_vowel_between_is_8_4_2():
    d = form("01.0679")   # riṇv: r i n v
    assert d.result == "riṇvati" and "8.4.2" in _rule_ids(d)
    assert form("01.0680").result == "raṇvati"


def test_n_before_a_stop_stays_dental_via_anusvara():
    # bhṛ: 8.3.24 turns the n of the ending into ṃ before the stop, so 8.4.1-2 never see an n; 8.4.58 restores it
    d = form("01.1045", number="pl")
    ids = _rule_ids(d)
    assert d.result == "bharanti" and "8.4.1" not in ids and "8.4.2" not in ids
    assert "8.3.24" in ids and "8.4.58" in ids


def test_word_final_n_is_exempt_by_8_4_37():
    d = form("01.1045", "laṅ", number="pl")
    assert d.result == "abharan"
    step = next(s for s in d.steps if "8.4.37" in s.rule_ids)
    assert step.kind == "prohibition" and "8.4.1" not in _rule_ids(d)


# -- vārttika on 6.1.64: ṣṭhiv and ṣvaṣk keep their ṣ; 7.3.75 -------------

def test_svask_keeps_its_s():
    d = form("01.0105", voice="middle")
    ids = _rule_ids(d)
    assert d.result == "ṣvaṣkate" and "6.1.64.1" in ids and "6.1.64" not in ids


def test_sthiv_keeps_its_s_and_lengthens_i():
    d = form("01.0641")
    ids = _rule_ids(d)
    assert d.result == "ṣṭhīvati" and "6.1.64.1" in ids and "7.3.75" in ids
    assert "6.1.64" not in ids and "7.3.86" not in ids
    step = next(s for s in d.steps if "6.1.64.1" in s.rule_ids)
    assert step.kind == "prohibition" and "ṣṭhiv" in step.note


def test_root_initial_s_and_n_only_when_the_root_still_begins_with_it():
    # laṅ of iṣ and aṇ: the vowel merged into the augment, so the ṣ / ṇ left over is not the root's start
    assert form("01.0780", "laṅ").result == "aiṣat"
    assert form("01.0512", "laṅ").result == "āṇat"


# -- 7.3.78 substituted present stems, 1.3.60, 7.3.77 by upadeśa -------------

@pytest.mark.parametrize("code, voice, expected", [
    ("01.1074", "active", "pibati"), ("01.1075", "active", "jighrati"), ("01.1076", "active", "dhamati"),
    ("01.1077", "active", "tiṣṭhati"), ("01.1078", "active", "manati"), ("01.1079", "active", "yacchati"),
    ("01.0990", "active", "sīdati"), ("01.0991", "middle", "śīyate"), ("01.1086", "active", "ṛcchati"),
    ("01.1143", "active", "paśyati")])
def test_7_3_78_stems(code, voice, expected):
    d = form(code, voice=voice)
    assert d.result == expected and "7.3.78" in _rule_ids(d)


def test_7_3_78_after_the_augment_merged_the_initial_r():
    # laṅ of ṛ: 6.1.90 (nitya) merges ā + ṛ first; by 6.1.85/1.1.56 the stem takes the root's place in
    # that ekādeśa, so meta.substitution_edit applies 6.1.90 again to ā + ṛ, then writes ccha. Nothing is "blocked".
    d = form("01.1086", "laṅ")
    assert d.result == "ārcchat"
    ids = _rule_ids(d)
    assert ids.index("6.1.90") < ids.index("7.3.78")
    losers = [(l.rule_id, l.reason) for s in d.steps for l in s.losers if "6.1.90" in l.reason or l.rule_id in ("6.1.90", "7.3.78")]
    assert not any("blocked by 7.3.78" in r for _, r in losers) and not any(i == "6.1.90" for i, _ in losers)
    step = next(s for s in d.steps if "7.3.78" in s.rule_ids)
    assert step.note.startswith("ṛ is replaced by the stem ṛccha")   # the root is named, not blank
    assert "6.1.90 is applied again" in step.note


def test_7_3_78_replaces_guna_of_r_roots():
    d = form("01.1086")
    assert "7.3.84" not in _rule_ids(d)
    assert any(l.rule_id == "7.3.84" for s in d.steps for l in s.losers)


def test_7_3_77_only_for_yam_uparame():
    assert form("01.1031").result == "yacchati" and form("01.0930").result == "yamati"
    assert form("01.1139").result == "yacchati" and form("01.1137").result == "gacchati"
    assert "7.3.77" not in _rule_ids(form("01.0930"))


def test_sri_dhau_only_as_a_running_option():
    d = form("01.1085")
    assert d.result == "sarati" and d.alternatives == ("dhāvati",)
    step = next(s for s in d.steps if "7.3.78" in s.rule_ids)
    assert "{only in the sense of running|Kāśikā: vegitāyāṃ gatau}, so not applied here; also correct: dhāvati" in step.note
    assert "vibhāṣā" not in step.note and "preferably" not in step.note
    assert "7.3.84" in _rule_ids(d)   # the ordinary stem still gets its guṇa, once
    assert _rule_ids(d).count("7.3.78") == 1


def test_sri_laṅ_alternative_order():
    d = form("01.1085", "laṅ")
    assert [d.result, *d.alternatives] == ["asarat", "asarad", "adhāvat", "adhāvad"]


def test_shad_is_middle_by_1_3_60():
    from panini.request import availability, parse_request
    assert availability(parse_request("01.0991", "laṭ", 3, "sg", "active")) == (
        "śad takes ātmanepada before an affix marked ś, as in laṭ and laṅ", "1.3.60")
    assert availability(parse_request("01.0991", "laṭ", 3, "sg", "middle")) is None
    d = form("01.0991", "laṅ", voice="middle")
    assert d.result == "aśīyata" and "1.3.60" in _rule_ids(d) and "1.3.78" not in _rule_ids(d)
    assert form("01.0991", voice="active").status.value == "unavailable"


def test_history_aside():
    s = next(s for s in form("01.1074").steps if "7.3.78" in s.rule_ids)
    assert "Latin bibit" in s.history and s.history_italic == ("bibit",)
    assert s.to_json()["history"] == s.history and s.to_json()["history_italic"] == ["bibit"]


def test_history_asides_for_each_root():
    got = {c: next(s for s in form(c, voice=v).steps if s.rule_ids[0] in ("7.3.78", "7.3.77")).history
           for c, v in [("01.1075", "active"), ("01.1077", "active"), ("01.0990", "active"), ("01.1143", "active"),
                        ("01.1079", "active"), ("01.1086", "active"), ("01.1137", "active"),
                        ("01.1076", "active"), ("01.1078", "active"), ("01.0991", "middle")]}
    assert got["01.1075"] == "a reduplicated present"
    assert "Greek hístēmi" in got["01.1077"] and "(*si-sd-)" in got["01.0990"]
    assert "spaś ‘see’" in got["01.1143"] and "yam ‘hold out’" in got["01.1079"]
    assert got["01.1086"] == "a present in *-sḱe-" and got["01.1137"].endswith("Greek báskō")
    assert got["01.1076"] is None and got["01.1078"] is None and got["01.0991"] is None


def test_trace_shows_history_at_v_only():
    from panini.trace import render_text
    d = form("01.1074")
    assert "historically" not in render_text(d)
    assert "historically: a reduplicated present, cf. Latin bibit" in render_text(d, verbosity=1)


# -- Task 8: bugs from the sweep -------------------------------------------

def test_6166_spares_a_root_initial_v():
    # vraj, vraṇ: 6.1.66 would delete the v of the upadeśa itself (vacanasāmarthya)
    assert form("01.0286").result == "vrajati"
    assert form("01.0519").result == "vraṇati"
    assert "6.1.66" not in _rule_ids(form("01.0286"))


def test_6166_still_deletes_the_y_of_iy():
    d = form("01.0002", "laṅ", number="du", voice="middle")   # edh: aidh + a + iytām
    assert d.result == "aidhetām" and "6.1.66" in _rule_ids(d)


def test_chad_ih_marker():
    assert form("01.0925").result == "chadati"


# yuch and uch are stored with cch (scripts/vendor_dhatupatha.py), because 6.1.73 tuk and 7.3.86
# guṇa bleed each other and no meta-rule decides (docs/findings.md). With the cch stored, neither
# rule applies and the full grade can't happen.
@pytest.mark.parametrize("code, tense, expected", [
    ("01.0242", "laṭ", "yucchati"), ("01.0242", "laṅ", "ayucchat"),
    ("01.0244", "laṭ", "ucchati"), ("01.0244", "laṅ", "aucchat")])
def test_stored_cch_roots(code, tense, expected):
    d = form(code, tense)
    assert d.status is Status.OK and d.result == expected


@pytest.mark.parametrize("text, code", [("yuch", "01.0242"), ("yucch", "01.0242"), ("uch", "01.0244"),
                                        ("uchī", "01.0244"), ("ucch", "01.0244"), ("uñch", "01.0243")])
def test_stored_cch_roots_found_by_taught_spelling(text, code):
    assert lookup_root(text).code == code


@pytest.mark.parametrize("code, tense, voice, expected, rule", [
    ("01.1144", "laṭ", "active", "daśati", "6.4.25"), ("01.1142", "laṭ", "active", "sajati", "6.4.25"),
    ("01.1131", "laṭ", "middle", "svajate", "6.4.25"), ("01.1131", "laṅ", "middle", "asvajata", "6.4.25"),
    ("01.1154", "laṭ", "active", "rajati", "6.4.26"), ("01.1154", "laṭ", "middle", "rajate", "6.4.26")])
def test_nasal_loss_before_shap(code, tense, voice, expected, rule):
    d = form(code, tense, voice=voice)
    assert d.result == expected and rule in _rule_ids(d)


# -- Task 9: closing the sweep ------------------------------------------------

@pytest.mark.parametrize("tense, number, expected", [
    ("laṭ", "pl", "gāte"), ("laṅ", "pl", "agāta"), ("laṭ", "sg", "gāte")])
def test_jh_becomes_at_after_a_base_not_in_short_a(tense, number, expected):
    # gāṅ: ā + śap's a merge (6.1.101), so the base before jh ends in ā, not short a (7.1.5)
    d = form("01.1101", tense, number=number, voice="middle")
    assert d.result == expected
    if number == "pl":
        ids = _rule_ids(d)
        assert "7.1.5" in ids and "7.1.3" not in ids
        assert any(l.rule_id == "7.1.3" and "7.1.5" in l.reason for s in d.steps for l in s.losers)


def test_jh_becomes_ant_after_short_a():
    d = form("01.0002", number="pl", voice="middle")   # edh: edha + jhe, the base ends in short a
    assert d.result == "edhante" and "7.1.3" in _rule_ids(d) and "7.1.5" not in _rule_ids(d)


@pytest.mark.parametrize("tense, voice, expected", [
    ("laṭ", "active", "gūhati"), ("laṅ", "middle", "agūhata"), ("laṭ", "middle", "gūhate")])
def test_guh_takes_long_u_after_guna(tense, voice, expected):
    # 6.4.89 names the root as goha, its full-grade form: guṇa first (7.3.86), then o → ū
    d = form("01.1043", tense, voice=voice)
    ids = _rule_ids(d)
    assert d.result == expected and ids.index("7.3.86") < ids.index("6.4.89")
    note = next(s.note for s in d.steps if "6.4.89" in s.rule_ids)
    assert "{full grade|guṇa}" in note and "ū" in note


@pytest.mark.parametrize("code, tense, expected", [
    ("01.0866", "laṭ", "kalpate"), ("01.0875", "laṭ", "kalpate"), ("01.0866", "laṅ", "akalpata")])
def test_krp_r_becomes_l(code, tense, expected):
    d = form(code, tense, voice="middle")
    assert d.result == expected and "8.2.18" in _rule_ids(d)


def test_krap_is_not_krp():
    assert "8.2.18" not in _rule_ids(form("01.0876", voice="middle"))   # krapa~, a different root


# 7.1.61 radhijabhor aci: jabh gets num before śap's vowel. 01.0150 jaBa~ is Kṣīrasvāmin's reading
# of the same root and is out of scope (docs/findings.md).
@pytest.mark.parametrize("tense, expected", [("laṭ", "jambhate"), ("laṅ", "ajambhata")])
def test_jabh_takes_nasal_before_a_vowel(tense, expected):
    d = form("01.0453", tense, voice="middle")
    assert d.result == expected and "7.1.61" in _rule_ids(d)


def test_jabha_variant_is_out_of_scope():
    req = parse_request("01.0150", "laṭ", 3, "sg", "active")
    assert availability(req) == OUT_OF_SCOPE["01.0150"]


# -- 1.3.12 anudāttaṅita ātmanepadam: the note names the marker that applies -----

@pytest.mark.parametrize("code, says, not_says", [("01.0002", "anudātta", "marked ṅ"), ("01.1099", "marked ṅ", "anudātta")])
def test_1312_note_names_the_marker(code, says, not_says):
    note = next(s.note for s in form(code, voice="middle").steps if "1.3.12" in s.rule_ids)
    assert says in note and not_says not in note
