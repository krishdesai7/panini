<!-- markdownlint-disable MD025 -->

# Findings, slice 1

What implementing the meta-rules taught us. These are cases where the engine
needed a decision the spec didn't spell out, a `blocks` entry turned out to be
missing, or the engine knowingly departs from a pure reading of the grammar.

## Expected failures

None. All 162 slice-1 forms match the reference (Vidyut 0.4), including the
optional variant _abhavat / abhavad_.

## Missing blocking relations the resolver found

The resolver raised `UnresolvedConflict` in two places. Both were missing
utsarga/apavāda entries, and both are textbook cases of Kiparsky's blocking
condition (_Architecture_ (19) and (23)):

- **7.2.81 _āto ṅitaḥ_ blocks 6.1.101 and 6.1.87** (found on _edha + ātām_).
  Wherever 7.2.81 can apply (an a-final base followed by the ā of a ṅit
  ending), 6.1.101 and 6.1.87 can apply too. Its domain is properly included
  in theirs (_yena nāprāpte_), so it is their exception.
- **6.1.97 _ato guṇe_ also blocks 6.1.88 _vṛddhir eci_** (found on
  _edha + e_). The domain of 6.1.97 (short a + a/e/o) lies inside the union
  of 6.1.101 (a + a), 6.1.88 (a + e/o) and 6.1.87. That is collective
  blocking, the same reasoning Kiparsky gives for 6.1.97 against 6.1.101 and
  6.1.87 (his (32)).

The final review found a third gap of the same kind, this time a missing rule:
**1.1.5 _kṅiti ca_** (no guṇa before an affix marked k/ṅ) was absent. Every
form still came out right, because śap always intervenes before guṇa applies.
But the trace told the learner that guṇa of _nī_ before the ṅit _tas_ was
merely deferred, when the grammar forbids it. It is now a niṣedha that blocks
7.3.84 and 7.3.86, like 1.3.4.

## Precisions to the restricted siddha principle

The local resolver in the spec needed three clarifications to work on real
derivations. None of them is a rule-specific ordering.

- **An order-independent step goes first.** When candidates conflict, the
  resolver first applies any candidate that commutes with all the others,
  because its order can't affect the result. The new state often settles the
  conflict. In _nī + iṭ_, tagging the ending sārvadhātuka (3.4.113) lets
  3.1.68 insert śap, which as the nitya rule bleeds the premature root+ending
  contraction (6.1.101).
- **"Commute" compares results.** If two rules give different intermediate
  states but the same final form, their order is immaterial. This follows
  Kiparsky's definition of the siddha relation, (39), which is stated over
  results. In _naya + iṭ_, 3.4.79 (i → e) first and 6.1.87 (a + i → e) first
  both lead to _naye_. The resolver checks this with one level of lookahead,
  and the trace records "order … is immaterial: both orders give naye". This
  is a small step towards the slice-2 search.
- **Markers are read when an upadeśa is introduced.** This is amendment A2,
  generalized from the tripādī to the whole grammar: whenever a rule
  introduces new upadeśa material (a lakāra, an ending, śap, an augment, or
  _ru~_ in the tripādī), the it-rules run on it immediately. Without this,
  3.4.78 (replace l) comes out nitya over marking the ṭ of _la~ṭ_: replacing
  the term destroys the ṭ, and the ṭ is what 3.4.79 needs through 1.1.56. The
  principle "an upadeśa is read together with its markers" matches the
  Siddhānta Kaumudī and Vidyut.

## Explicit meta-rules the slice needed

- **1.1.56 _sthānivad ādeśo 'nalvidhau_.** A substitute keeps a link to what
  it replaced. Tags and markers are inherited through that link, while rules
  conditioned by a single sound read the current sounds, which is the
  _al-vidhi_ exception. Laṅ depends on it: the endings count as ṅit because
  the _l_ did. Rules that ask about the lakāra (3.4.79, 3.4.99–101) follow
  the chain back to the lakāra itself. The ending's own markers must not count
  here: _iṭ_ is itself ṭit and _mahiṅ_ is itself ṅit, and counting them made
  laṭ behave like laṅ.
- **6.1.85 _antādivac ca_.** A single substitute counts as the end of the
  preceding element and the beginning of the following one. Without it, after
  _bhava + anti_ → _bhava + nti_ the ending would "begin" with n, and 7.3.101
  would lengthen the a (_bhavānti_).
- **1.1.46 _ādyantau ṭakitau_** places aṭ/āṭ (ṭit, at the beginning) and tuk
  (kit, at the end). It reads the marker from the augment's upadeśa, because
  the augment is placed as taught. tuk is added to the vowel before ch
  (6.1.71 _hrasvasya_), so its t is written at the end of that vowel, in the
  vowel's term: in laṅ of _cham_ it ends the augment's term (_at + cham_).

## Engine exceptions (vacanasāmarthya)

Two it-rules must not apply where the grammar's own wording shows they can't.
The tradition argues these from _vacanasāmarthya_ ("otherwise the rule would
be pointless"). A local resolver can't make that argument, so each exclusion
is written into the rule and shown as a near-miss note in the trace.

- **A3: 1.3.7 _cuṭū_ skips the jh of _jhi_/_jha_.** 7.1.3 _jho 'ntaḥ_
  replaces that jh, which would be impossible if it were a marker.
- **1.3.8 _laśakvataddhite_ skips the l of laṭ/laṅ.** 3.4.77 _lasya_ ("in
  place of l") refers to that l, so it must survive.

## Kiparsky vs. tradition

Across all 162 forms, comparing our step order with Vidyut's (a stand-in for
the traditional derivation), every pair of operational rules applied in a
different order acts on independent material. Examples: 6.1.97 merging
_a + anti_ before or after 7.3.84 guṇa on the root, or 6.4.71 aṭ before or
after 7.1.3. These pairs commute, and the engine orders them by sūtra number,
arbitrarily. Every pair where order matters (pinned in `tests/test_goldens.py`)
agrees with the traditional order. Slice 1 therefore shows no case where
Kiparsky's meta-rules and the tradition derive differently. The debated cases
lie outside laṭ/laṅ of these roots (Joshi & Kiparsky's _adhītya_,
_sed-vas-Ṅas_) and are slice 2's job.

## Notes for slice 2

- **Nitya depends on step granularity.** 3.1.68 counts as nitya over 7.3.84
  partly because the newly inserted śap isn't yet tagged sārvadhātuka in the
  very next state. The derivation search in slice 2 should compare
  derivations, not single states, which removes this sensitivity.
- **The one-step checks ignore blocking.** `still_applies` and the commutation check
  apply a rule's edit and look again, but they don't ask whether a rule that still
  matches is now blocked. 7.1.5 (slice 1.5) shows it (see "Task 9" below). They
  used to ignore marker reading too; since slice 1.5 they apply A2 (Task 9).
- **The tripādī never re-checks a blocked candidate.** It stays skipped even
  if its blocker later disappears. No slice-1 form is affected.
- **The page build looks for the style skill in a fixed home-directory
  location.** `PANINI_STYLE_DIR` overrides it, which is enough for a
  personal tool.

## Known limitations

- **No 8.4.46–47 doubling** (_aco rahābhyāṃ dve_, _anaci ca_). Forms are
  given undoubled.
- **No 8.4.68 _a a_** (closed ă). It is invisible in IAST.
- **No exceptions to 8.4.40–41.** 8.4.42 _na padāntāṭ ṭor anām_ and 8.4.43
  _toḥ ṣi_ (which limit 8.4.41) and 8.4.44 _śāt_ (which limits 8.4.40) are not
  modelled; no bhvādi form in laṭ or laṅ needs them.
- **6.4.22 _asiddhavat_ is detected, not modelled.** When two ābhīya rules
  apply in one derivation, the step carries a warning.
- **6.1.86 _ṣatvatukor asiddhaḥ_ is not modelled.** The `tuk_or_satva` flag
  exists, but no slice form needs the shadow evaluation: in _gacchati_, tuk
  isn't affected by 6.1.87–110.
- **1.1.47 _mid aco 'ntyāt paraḥ_** wasn't needed in slice 1 (no mit augment
  occurs); slice 1.5 adds it for num (below).
- **Accent** is out of scope. The only exception is the lexical accent of a
  root's marker vowel, which drives pada (1.3.12, 1.3.72).

# Findings, slice 1.5

## Pada against Vidyut

`scripts/check_pada.py` asks Vidyut which voices it derives for laṭ 3sg of each
bhvādi root and compares with `Root.pada` (read from the marker vowel). 1147 of
1156 roots agree. The nine that don't:

- **śad 01.0991** (ours P, Vidyut A): 1.3.60 _śadeḥ śitaḥ_ makes it ātmanepada
  when the stem takes śit. Slice 1.5 Task 7 adds this rule.
- **sthā 01.1077, vad 01.1164, kram 01.0545** (ours P, Vidyut both): the
  alternative middle voice is meaning- or prefix-conditioned (1.3.23, 1.3.47,
  1.3.38–43). Preverbs are out of scope, so the marker-based pada stands.
- **paṇ 01.0507, pan 01.0508** (Vidyut both / parasmaipada only): 3.1.28 gives
  these an _-āya-_ stem in the praise sense, which is out of scope here. They
  are now in `OUT_OF_SCOPE`.
- **ṛti 01.1166** (ours P, Vidyut A): 3.1.29 _ṛter īyaṅ_ gives an _-īya-_ stem,
  which is ātmanepada by ṅit. Now in `OUT_OF_SCOPE`.
- **Two present stems** (3.1.70 for bhram, bhrāś, bhlāś, laṣ; 3.1.75 for akṣ,
  takṣ): Vidyut gives both stems, the engine would give one. These roots are in
  `OUT_OF_SCOPE` until optional rules are modelled. (sṛ 01.1085 also has two
  stems, via 7.3.78; Task 7.)
- **nāth 01.0007, sasj 01.0229** (Vidyut both): not marker-reading bugs (Task 8).
  Vidyut also derives an active of nāth, by the default 1.3.78, although the root's
  marker vowel is anudātta. Vidyut follows the vārttika _āśiṣi nāthaḥ_ (on 1.3.21),
  by which nāth is ātmanepada only in the sense of a blessing, a meaning-conditioned
  rule like those for sthā and vad. Our middle-only nāth is therefore a narrowing:
  it gives every sense the voice of the blessing sense. Vidyut also derives the
  middle of sasj (`zasja~`, no accent on the marker) without any pada rule, so its
  data treats that root as taking both voices. Our marker readings (nāth middle by
  1.3.12, sasj active by 1.3.78) stand.

## Whole-class sweep (before the new rules)

The slow sweep compares every available request with Vidyut. Before Tasks 3–9
about a fifth of the 21,708 non-empty reference entries fail, in two groups:
roots with an _i_-marker that inserts a nasal (7.1.58 _idito num dhātoḥ_,
_vandate_ not _vadate_, 204 roots), and a mixed group (71 roots): initial
_ṣ_/_ṣṭ_ roots (_sṭanati_ for _stanati_, 6.1.64 and its ṭu-substitute), 6.4.x vowel lengthening (_ūrdate_),
_ch_ doubling (6.1.73 before _ch_), the _yam_/_sad_ stems (7.3.78),
_kṛp_ → _kalpate_, and _vraj_ losing its initial _v_ (a bug, fixed in Task 8).

## 7.3.78 and 1.3.60

- **śad 01.0991** is ātmanepada only: 1.3.60 _śadeḥ śitaḥ_ applies before the
  ś-affix śap, so `availability` rules out the active (reason cites 1.3.60) and
  the engine assigns the middle by 1.3.60, blocking 1.3.78.
- **sṛ 01.1085** has two stems, _sarati_ and _dhāvati_. The tradition restricts
  7.3.78's _dhau_ to fast motion (Kāśikā _vegitāyāṃ gatau_); the engine cannot
  know the sense, so the substitution is an optional rule of its own kind
  (`Optionality.SENSE`: not applied by default, the alternative noted), giving _sarati_ first and _dhāvati_ as an alternative, in Vidyut's order.
- **ṛ 01.1086 laṅ** (9 requests): Vidyut also gives _ārchat_ beside _ārcchat_,
  since 8.4.65 _jharo jhari savarṇe_ optionally drops one _c_ of _rcch_. The
  engine has no 8.4.65 yet, so only _ārcchat_ is derived. XFAIL.
- 7.3.78 replaces the whole root, so it overrides guṇa (7.3.84, 7.3.86).
  In laṅ of ṛ, 6.1.90 (nitya) merges ā + ṛ first. 6.1.85 antādivat makes that
  substitute part of the root as well, so 7.3.78 still applies, and by 1.1.56
  sthānivat the stem takes the root's place in the ekādeśa. The engine records
  on each ekādeśa sound the rule and the two sounds (`Sound.ekadesha_rule`,
  `ekadesha_inputs`) and `meta.substitution_edit` applies that rule again to the
  stem's sound: ā + ṛ → ār, then _ccha_ (_ārcchat_).
- Declined optional rules (vibhāṣā, as for sṛ) are recorded per rule and terms
  by the engine: they are not offered again and block nothing, in every branch.

## 7.1.58, 1.1.47 and 6.4.24

- **7.1.58 _idito num dhātoḥ_** gives a root marked with a final _i_ the
  augment num (_kradi~_ → _krand-_). It reads the marker the it-rules set
  (1.3.2) and the upadeśa, because _i~r_ (_dṛś_, `df\Si~r`) is the marker
  _ir_, not _i_: 1.3.2 marks that nasal _i_ too, so the marker alone can't
  tell them apart. The nasal then goes through the tripādī: 8.3.24 makes it
  anusvāra before an obstruent and 8.4.58 turns that into the nasal of the
  following stop (_krandati_, _vaṅkate_, _kampate_).
- **1.1.47** places the augment right after the root's last vowel
  (`meta.mit_position`). In laṅ of a vowel-initial root (_and_ → _āndat_), āṭ
  and the root's vowel may already have merged (6.1.90), leaving the root
  with no vowel of its own. The merged vowel counts as the root's first sound
  (6.1.85), so num goes at the start of what remains. An augment's sound
  written after the merged vowel (tuk, _ā t + ch_) is passed over when looking
  for it, so num still applies after tuk; it is therefore nitya and wins
  (_āñchat_, _auñchat_).
- **6.4.24 _aniditāṃ hala upadhāyāḥ kṅiti_** is the contrast: roots _not_
  marked with _i_ lose a penultimate nasal before a kit/ṅit affix, which is
  why the _i_ marker matters. It is not traced in slice 1.5: in bhvādi laṭ and laṅ
  the root is always followed by śap, which is neither kit nor ṅit. **Since slice
  1.6 it is traced** for tudādi, whose śa counts as ṅit (see "Slice 1.6" below).
- After 7.1.58, 6 of the 196 _i_-marked roots still fail the sweep, for
  missing sound rules rather than the augment: _stambh_ (the ṣṭ-initial bug,
  Task 4), _ghiṇṇ_, _ghuṇṇ_, _ghṛṇṇ_ (n before ṇ needs 8.4.41 _ṣṭunā ṣṭuḥ_:
  ours _ghinṇate_), and _riṇv_, _raṇv_ (n after r needs 8.4.1–2 ṇatva: ours
  _rinvati_).

## ṇatva after ṛ (8.4.1.1) in ghṛṇṇ

For _ghṛṇ_ (`GfRi~\`) our trace cites the vārttika 8.4.1.1 _ṛvarṇāc ceti vaktavyam_ (ṛ/ṝ trigger ṇatva, as in _nṛṇām_) for the n that num inserts (it follows ṛ); Vidyut cites 8.4.41 alone (the n before ṇ). The form is the same (_ghṛṇṇate_). We cite the vārttika because the tripādī runs once in sūtra order (8.2.1 pūrvatrāsiddham), and 8.4.1.1 precedes 8.4.41, so it fires first and 8.4.41 then has nothing left to change.

## Task 8: bugs from the sweep

- **6.1.66 _lopo vyor vali_ spares a root's initial v/y.** The rule deleted any
  y/v before a consonant other than y, including the v that _vraj_ and _vraṇ_
  begin with (_rajati_). If the rule always deleted that v, teaching these roots
  with it would be pointless, so by _vacanasāmarthya_ it does not apply there.
  Vidyut 0.4 makes the same exception (`ac_sandhi.rs`, `try_lopo_vyor_vali`:
  "otherwise roots like vraj would be vyartha"). Like A3 and 1.3.8, the exclusion is
  written into the rule, with a near-miss note and a reading that cites it. The y of
  _iy_ (7.2.81, _aidhetām_) is still deleted.
- **`CadiH` 01.0925** is not a recited upadeśa but the root _chad_ cited by name,
  _chadiḥ_ (the root plus ik in the nominative, as roots are named by the vārttika
  _ik-śtipau dhātunirdeśe_ on 3.3.108). Vidyut special-cases it as bare _chad_
  (`dhatu_karya.rs`). `scripts/vendor_dhatupatha.py` now rewrites it as the upadeśa
  `Cada~` (parasmaipada, not idit): _chadati_. The trace therefore shows a marker
  vowel ã that the source entry doesn't have.
- **6.4.25 _daṃśasañjasvañjāṃ śapi_ and 6.4.26 _rañjeś ca_** are in: daṃś, sañj,
  svañj and rañj lose their penultimate nasal before śap (_daśati_, _sajati_,
  _svajate_, _rajati_). Each is one small rule naming its roots by upadeśa, with
  _na lopaḥ_ (6.4.23) and _upadhāyāḥ_ (6.4.24) carried over. 6.4.24 itself is
  still not traced (śap is not kit or ṅit).
- **6.1.73 _che ca_ against 7.3.86 for yuch 01.0242 and uch 01.0244: a gap in the
  grammar, closed by storing the roots with _cch_.** On _yuch + a + ti_ the two rules
  bleed each other. Inserting _t_ makes the _u_ heavy (1.4.11), so full grade can't
  apply. Full grade makes the vowel long, so 6.1.73 can't apply (6.1.75 adds the same
  _t_). Neither nitya nor the siddha principle decides (Kiparsky, "Pāṇini is slick",
  on _ṛch_). The extended siddha principle makes it worse, since it predicts
  _\*yocchati_ even more strongly. Under Joshi and Kiparsky's framework only an
  explicit asiddha stipulation or an exception rule could block _\*yocchati_, and the
  Aṣṭādhyāyī has neither for yuch. The tradition gets _yucchati_ from the antaraṅga
  paribhāṣā, which the spec excludes. Vidyut gets it by running 6.1.73 at an earlier
  stage.
    - **Ruling (user):** `scripts/vendor_dhatupatha.py` rewrites the two roots as
      `yucCa~` and `ucCI~`. With _cch_ stored, neither rule applies: _yucchati_,
      _ayucchat_, _ucchati_, _aucchat_. This is a stipulation that closes the gap, not a
      traditional reading. The dhātupāṭha's upadeśas have a single _ch_ (_yucha_
      pramāde, _uchī_ vivāse). They are recited and printed as _yuccha_ and _ucchī_ only
      because 6.1.73 applies in saṃhitā. Lookup still accepts _yuch_, _uch_ and _uchī_
      (`TAUGHT_AS` in `lexicon.py`). The 27 requests now match Vidyut.
    - **Cost:** the trace no longer shows 6.1.73 for these roots. The fix also can't be
      applied to every root in _ch_. _prach_ (tudādi) has to keep a single _ch_:
      stored as _pracch_, it would break 6.4.19 _chvoḥ śūḍ anunāsike ca_ for _praśna_,
      which forces Patañjali's _cchvoḥ_ reparsing that Kiparsky rejects. So the class is
      split arbitrarily: _yuch_ and _uch_ get _cch_, and _prach_ keeps _ch_. Revisit if a
      later slice adopts a principled ordering device.
    - **Corrected in slice 1.6:** tudādi _ṛch_ (06.0016) and _uch_ (06.0015) do *not* need
      _cch_, as this note used to predict. Before śa, 1.1.5 blocks full grade, so 6.1.73 has
      no rival and the trace shows it (_ṛcchati_, _ucchati_). The stipulation stays for the
      two bhvādi roots only, and `scripts/vendor_dhatupatha.py` now keys it by list code.

## Task 9: closing the sweep

- **7.1.5 _ātmanepadeṣv anataḥ_** (gāṅ 01.1101, 3pl middle). In a middle ending, jh
  becomes _at_, not _ant_, after a base that does not end in short a. After śap's a
  merges into the root's ā (6.1.101) the base ends in ā, so _gā + jhe_ → _gā + ate_ →
  _gāte_ (laṅ _agāta_). It is an apavāda of 7.1.3: wherever it applies, 7.1.3 applies
  too. For every other root of the class the base before the ending ends in śap's a.
  Two things about the trace, both instances of the step-granularity note under
  slice 2:
    - ā + a merge before jh is replaced. That is what nitya gives (6.1.101 applies
      before and after 7.1.3; after the merge 7.1.3 is blocked by 7.1.5), and it is
      Vidyut's order. But the resolver gets there by its tie-break: its one-step
      commutation check doesn't see blocking, so the two look order-independent and the
      lower-numbered 6.1.101 goes first.
    - In every middle 3pl, the base is the bare root before śap arrives (_edh + jha_),
      and that root doesn't end in short a, so the trace reports "7.1.3: blocked by
      7.1.5" at that step. Then śap arrives, its markers are deleted, the base ends in
      a, 7.1.5 no longer applies, and 7.1.3 applies after all. At first nothing in the
      trace said why 7.1.5 dropped out. The resolver's one-step checks applied śap
      without reading its markers, so śaP still seemed to leave 7.1.5 its context, the
      two looked order-independent, and 3.1.68 went first on the tie-break.
    - **Fixed in slice 1.5 (user's ruling: don't defer to slice 2).** The resolver now
      takes a `settle` hook from the engine (`_Runner._settle`). It applies an edit as
      the engine does, reading the markers of a newly introduced upadeśa (A2), and only
      of that term. `still_applies` and the commutation check use it, so the trace now
      says "7.1.5: deferred: 3.1.68 applies either way (nitya)" at the śap step. Two
      supporting changes were needed. (1) The ekādeśa signature names its two terms:
      a + a → a between the root and śap is a different change from a + a → a between
      the root and the ending (śabdāntaraprāpti). Without this, a-final stems (_kakkha_,
      the 7.3.78 stems) raised `UnresolvedConflict` in laṅ 1sg. (2) A rule competing
      with itself at two sites is not reported as a loser, since both applications
      appear as steps. Across the 21,564 requests no form changed. The traces changed
      as follows:
        - +858 "7.1.5: deferred: 3.1.68" (every middle 3pl): the fix.
        - +1,355 "6.1.66: deferred: 3.1.68": correct. On the bare root, a final v/y
          stands before the ending's consonant (_kav + ti_), which is the context of
          _lopo vyor vali_, and śap removes it.
        - −75 "6.1.78: deferred: 3.1.68" and −6 "7.1.61: deferred: 3.1.68": these were
          false. With śap's ś read as a marker, each rule makes the same change before
          and after śap (_ai_ → _āy_, _jabh_ → _jambh_), so śap doesn't bleed it.
        - −29 "7.3.78: order with 6.1.97 is immaterial" (3pl and laṅ 1sg of the 7.3.78
          roots): false matches from the old signature. 6.1.97 now goes before the laṅ
          augment, which commutes with it (10 traces reordered).
        - Cost: the lookahead now reads markers (about 400 settle calls per derivation,
          about 75 distinct, so they're cached per derivation). The full sweep takes
          about 2½ minutes instead of 1½.
- **6.4.89 _ūd upadhāyā gohaḥ_** (guh 01.1043). The sūtra names the root as _goha_,
  guh in its full grade (as the commentaries read it), so the engine applies guṇa
  first (7.3.86, _goh_) and then replaces the penultimate o by ū before the vowel of
  śap (_aci_, from 6.4.77): _gūhati_, _agūhata_. The wording is what keeps the rule out
  of forms without guṇa (before a kit/ṅit affix, as in the perfect _juguhatuḥ_); no
  extra condition is needed. Vidyut applies 6.4.89 to _guh_ directly, in place of
  guṇa (`asiddhavat.rs`, conditioned on a non-kṅit affix). Same form, different trace.
- **8.2.18 _kṛpo ro laḥ_** (kṛp 01.0866 and 01.0875). In the root kṛp, r becomes l:
  after guṇa _karp_ → _kalp_, _kalpate_. Both roots taught as kṛp are meant (the
  sūtra names the root by its shape, as it does elsewhere); _krap_ 01.0876 is not.
  The rule also covers the r heard inside ṛ (ṛ → ḷ, as in _kḷpta_), which laṭ and laṅ
  never reach because guṇa always applies first.
- **7.1.61 _radhijabhor aci_ for jabh: applied by shape; 01.0150 is out of scope.** The
  rule gives radh and jabh the augment num before a vowel-initial affix. Two bhvādi
  entries are taught as jabh, both "gātravināme": `jaBI~\` (01.0453, ātmanepada) and
  `jaBa~` (01.0150, parasmaipada). Vidyut gives num to the first only (_jambhate_,
  _jabhati_), testing `has_u("jaBI~\\")` in `angasya.rs` with no comment, issue or
  cited reason. What the sources say:
    - **Kāśikā** (7.1.61): _radhi jabhi ity etayor ajādau pratyaye num āgamo bhavati_;
      examples _jambhayati, jambhakaḥ, sādhujambhī, jambhaṃjambham, jambho vartate_. No
      restriction to either jabh.
    - **Siddhānta Kaumudī**: _etayor numāgamaḥ syād aci_; _jambhate, jajambhe, jambhitā,
      jambhiṣṭa_. Its dhātupāṭha has one jabh for this sense (_jabhi jṛbhi
      gātravināme_). No restriction.
    - **Mādhavīya Dhātuvṛtti** 266 (printed pp. 120–121; archive.org
      `madhaviyahdhatuv00sayauoft`, scans 174–175): _jabhi jṛbhi gātravināme. 'jabhī ity
      eke, jabdham' iti Maitreyaḥ. ayam eva pāṭhaḥ prāyeṇa vṛttikārasya sammataḥ_. The
      Kāśikā's counterexample _jabdham_ shows it takes the _jabhī_ reading. Conjugated in
      the middle voice with num, citing 7.1.61: _jambhate, jajambhe, jambhitā …_. At the
      end of the entry: _jabhiḥ vināśanārthe curādau_, and some count a jabh among the
      active-voice roots too.
    - **Kṣīrataraṅgiṇī** (Liebich 1930) I.415–416: _jabha jṛbhi gātravināme. jabhate,
      jṛmbhate. jabhitaḥ … radhijabhor aci iti num: jambhakaḥ, jambhanam, jambhaḥ_.
      Kṣīrasvāmin reads _jabha_ at the same place in the list and gives _jabhate_, middle
      voice and without num before śap. He uses 7.1.61 only for derived nouns and gives no
      reason. Under X.176 he repeats it (_bhvādau jabha jṛbhi jambhane: jabhate_) and adds
      _Candro jabhety āha_. At I.1029, after _yabha_: _jabhi ceti Daurgāḥ: jambhati (VII,
      1, 61)_, a separate active-voice jabh of the Daurga school.
    - ashtadhyayi.com's root data (Vidyut's source) notes on 01.0150 that it is a
      variant reading of _jabhī_ (1.453), absent from the Siddhānta Kaumudī and found in
      the Kṣīrataraṅgiṇī, and tags it ātmanepada. Vidyut's `jaBa~` has no
      unaccented-vowel mark, so it is conjugated as parasmaipada.

    **Ruling (user):** 7.1.61 applies to every root whose bare form is raD or jaB, as
    the sūtra's wording reads. 01.0453 gives _jambhate_, as the Siddhānta Kaumudī, Mādhava
    and Vidyut give it. 01.0150 is in `OUT_OF_SCOPE`, with a reason the explorer shows. It
    is Kṣīrasvāmin's reading of the same root, and his _jabhate_ (no num before śap)
    can't be derived from the sūtra as worded. Vidyut's _jabhati_ is attested in no
    source: Kṣīrasvāmin has middle voice and no nasal, the Daurgas active voice with the
    nasal. So there is no reference form to compare against. Vidyut's restriction by
    upadeśa happens to reproduce Kṣīrasvāmin's missing nasal, but with a voice he doesn't
    give. 7.1.62 _neṭy aliṭi radheḥ_ (radh before iṭ) isn't reached in laṭ and laṅ, and
    radh isn't a bhvādi root.

- **Citation names** now quote a taught nasal at the place of the consonant after it,
  as the tripādī would pronounce it: _sañj_, _svañj_, _rañj_, _añc_, _tump_,
  _śrambh_ (ṃ before a sibilant or h, as in _daṃś_; n before a dental). A name is only
  a display label. Lookup (CLI and explorer) drops every diacritic, so plain spellings
  work (_sanj_, _dams_, _stha_), though a spelling with its diacritics is tried first
  in the CLI, so _pat_ stays _pat_, not _paṭ_. The nasal must be the one the name now
  uses: _tunp_-style spellings no longer resolve (the upadeśa _tunpa_ still does).

## Where slice 1.5 ends

The slow sweep checks 21,564 requests over 1,132 of the 1,156 bhvādi roots (24 are
in `OUT_OF_SCOPE`: other present stems, the _-āya-_/_-īya-_/ṇiṅ suffixes, optional
stems, one variant reading). 21,555 match Vidyut. The 9 documented differences, all in `XFAIL`:

- ṛ 01.1086 laṅ, 9 requests: no 8.4.65 (_ārchat_).

## Slice 1.6: tudādi

The tudādi section (174 roots, codes `06.`) is in, for laṭ and laṅ. Two roots are out of
scope: _vich_ 06.0159 takes _-āya-_ (_vicchāyati_, 3.1.28), and _truṭ_ 06.0102 has two
present stems (_truṭyati_, _truṭati_, 3.1.70), like bhvādi _bhram_ and _laṣ_. The slow
sweep now checks 24,876 requests over both classes: 3,312 of them over 172 tudādi roots.
Everything matches except 18 documented differences, all the 8.4.65 _ārchat_ variant: 9
for bhvādi _ṛ_ and 9 for tudādi _ṛch_ laṅ.

**New rules.** 3.1.77 _tudādibhyaḥ śaḥ_ (śa for śap; with 1.2.4 and 1.1.5, already
present, the zero grade comes free). Then 6.4.24 and 7.1.59 _śe mucādīnām_ with the
vārttika _śe tṛmphādīnāṃ num vācyaḥ_, 6.4.77 _iyaṅ/uvaṅ_, 7.4.28 _riṅ_, 6.1.16
samprasāraṇa with 6.1.108, 7.1.100 _ṝ → ir_, and 8.2.21 _aci vibhāṣā_. 1.3.60 now also
covers tudādi _śad_ (06.0164), which `scripts/check_pada.py` flagged.

**A meta-rule change: guṇa is one operation for nitya (user's rulings).** Adding 6.4.77
and 7.1.100 made bhvādi forms fail with unresolved conflicts:

- _bhū + a_: full grade 7.3.84 gives _bho-_; uvaṅ 6.4.77 gives _bhuv-_, after which 7.3.86
  gives the penultimate _u_ full grade: _\*bhovati_. The same holds for _nī_ and the other
  roots in final i/u.
- _tṝ + a_ (also _dṝ_, _nṝ_): full grade gives _tar-_; 7.1.100 gives _tir-_, then 7.3.86:
  _\*terati_.

Rule by rule, the two bleed each other, so the rule-identity nitya check couldn't decide,
and para (1.4.2) is restricted to saṃjñās. Ruling: 7.3.84 and 7.3.86 share the operation
guṇa (both carry _guṇaḥ_ from 7.3.82; `Rule.operation`). In the nitya check, an
operation survives the other rule if one of its rules still acts on the same sound
afterwards, whatever its result (`resolver.surviving_rule`). So guṇa is nitya over uvaṅ
and over 7.1.100: _bhavati_, _tarati_. In tudādi, 1.1.5 blocks guṇa, so 6.4.77 and
7.1.100 apply: _dhuvati_, _kirati_. The trace says so: "6.4.77: deferred: full grade applies either way (nitya): after 6.4.77, 7.3.86 still applies
at the same place".

This reads nitya more loosely than the tradition's _śabdāntaraprāpti_ caveat, which
says a rule that applies to a changed form afterwards (_bhuv_, _tir_) is not nitya. The
tradition decides both cases by 1.4.2 _vipratiṣedhe paraṃ kāryam_ (7.3.84 is the later
rule). Kiparsky's restriction of 1.4.2 rules that out here. Worth revisiting when the
derivation search (extended siddha) comes in.

**Other calls.**

- **8.2.79 _na bhakurchurām_ is not added.** Vidyut cites it for _churati_. But the _r_
  of _chur_ precedes a vowel in laṭ and laṅ, so 8.2.76–78 never apply and 8.2.79 has
  nothing to block.
- **gṝ: _girati_ first, _gilati_ as the alternative.** 8.2.21 says _vibhāṣā_, which the
  engine reads as "preferably not" (Kiparsky). Vidyut lists _gilati_ first. The paradigm
  test compares this root's forms in any order (`ORDER_DIFFERS`).
- **The tṛmph vārttika applies only once the nasal is gone.** It applies to a root with
  no nasal left before its final consonant, so it follows 6.4.24, which deletes the
  taught nasal. The vārttika exists to undo that loss. 6.4.24 leaves an augment _n_
  alone: num added by 7.1.59 would otherwise be pointless, and Vidyut agrees. A bug the
  sweep caught: in laṅ of _ṛmph_ the root's vowel merges with āṭ (6.1.90), and an earlier
  version added num twice (_\*ārṇmphat_).
- **6.1.108 merges inside the root** (one sound replacing both, 6.1.84), not with the
  cross-term ekādeśa edit.
- **Names now shared across classes** (_uch_, _uñch_, _nud_, _śad_, _sad_, and others) need
  a list code. A featured root breaks a tie only within one class, since the traces differ
  (śap vs śa). _kṛ_
  resolves to tudādi _kṝ_ through the diacritic-free fallback; revisit when a class with
  _kṛ_ arrives.
- **Vidyut cites a code 2542 on _vid_** (06.0168), which is not a sūtra number (not looked into). It gives
  _vindati_ twice; the reference keeps one.
- **6.4.24 now shows as a deferred competitor in bhvādi traces** (about 620 forms, e.g.
  _manth_ laṭ 3pl): "6.4.24: deferred: 3.1.68 applies either way (nitya)". Before śap is
  added, the root stands right before an ending that 1.2.4 makes count as marked ṅ, so 6.4.24
  is briefly a candidate. The line is true under the nitya check, and the same thing already
  happens with 1.1.5 on _bhū + tas_. Keeping it out would mean special-casing the rule, so it
  stays. Slice 1.5's worry that a 6.4.24 note "would mislead" was about a near-miss note;
  this is a resolver loser line. 6.4.77 and 7.1.100 show as deferred competitors in bhvādi
  for the same reason (585 and 54 forms).
