# Findings, slice 1

What implementing the meta-rules taught us. These are cases where the engine
needed a decision the spec didn't spell out, a `blocks` entry turned out to be
missing, or the engine knowingly departs from a pure reading of the grammar.

## Expected failures

None. All 162 slice-1 forms match the reference (Vidyut 0.4), including the
optional variant *abhavat / abhavad*.

## Missing blocking relations the resolver found

The resolver raised `UnresolvedConflict` in two places. Both were missing
utsarga/apavāda entries, and both are textbook cases of Kiparsky's blocking
condition (*Architecture* (19) and (23)):

- **7.2.81 *āto ṅitaḥ* blocks 6.1.101 and 6.1.87** (found on *edha + ātām*).
  Wherever 7.2.81 can apply (an a-final base followed by the ā of a ṅit
  ending), 6.1.101 and 6.1.87 can apply too. Its domain is properly included
  in theirs (*yena nāprāpte*), so it is their exception.
- **6.1.97 *ato guṇe* also blocks 6.1.88 *vṛddhir eci*** (found on
  *edha + e*). The domain of 6.1.97 (short a + a/e/o) lies inside the union
  of 6.1.101 (a + a), 6.1.88 (a + e/o) and 6.1.87. That is collective
  blocking, the same reasoning Kiparsky gives for 6.1.97 against 6.1.101 and
  6.1.87 (his (32)).

The final review found a third gap of the same kind, this time a missing rule:
**1.1.5 *kṅiti ca*** (no guṇa before an affix marked k/ṅ) was absent. Every
form still came out right, because śap always intervenes before guṇa applies.
But the trace told the learner that guṇa of *nī* before the ṅit *tas* was
merely deferred, when the grammar forbids it. It is now a niṣedha that blocks
7.3.84 and 7.3.86, like 1.3.4.

## Precisions to the restricted siddha principle

The local resolver in the spec needed three clarifications to work on real
derivations. None of them is a rule-specific ordering.

- **An order-independent step goes first.** When candidates conflict, the
  resolver first applies any candidate that commutes with all the others,
  because its order can't affect the result. The new state often settles the
  conflict. In *nī + iṭ*, tagging the ending sārvadhātuka (3.4.113) lets
  3.1.68 insert śap, which as the nitya rule bleeds the premature root+ending
  contraction (6.1.101).
- **"Commute" compares results.** If two rules give different intermediate
  states but the same final form, their order is immaterial. This follows
  Kiparsky's definition of the siddha relation, (39), which is stated over
  results. In *naya + iṭ*, 3.4.79 (i → e) first and 6.1.87 (a + i → e) first
  both lead to *naye*. The resolver checks this with one level of lookahead,
  and the trace records "order … is immaterial: both orders give naye". This
  is a small step towards the slice-2 search.
- **Markers are read when an upadeśa is introduced.** This is amendment A2,
  generalized from the tripādī to the whole grammar: whenever a rule
  introduces new upadeśa material (a lakāra, an ending, śap, an augment, or
  *ru~* in the tripādī), the it-rules run on it immediately. Without this,
  3.4.78 (replace l) comes out nitya over marking the ṭ of *la~ṭ*: replacing
  the term destroys the ṭ, and the ṭ is what 3.4.79 needs through 1.1.56. The
  principle "an upadeśa is read together with its markers" matches the
  Siddhānta Kaumudī and Vidyut.

## Explicit meta-rules the slice needed

- **1.1.56 *sthānivad ādeśo 'nalvidhau*.** A substitute keeps a link to what
  it replaced. Tags and markers are inherited through that link, while rules
  conditioned by a single sound read the current sounds, which is the
  *al-vidhi* exception. Laṅ depends on it: the endings count as ṅit because
  the *l* did. Rules that ask about the lakāra (3.4.79, 3.4.99–101) follow
  the chain back to the lakāra itself. The ending's own markers must not count
  here: *iṭ* is itself ṭit and *mahiṅ* is itself ṅit, and counting them made
  laṭ behave like laṅ.
- **6.1.85 *antādivac ca*.** A single substitute counts as the end of the
  preceding element and the beginning of the following one. Without it, after
  *bhava + anti* → *bhava + nti* the ending would "begin" with n, and 7.3.101
  would lengthen the a (*bhavānti*).
- **1.1.46 *ādyantau ṭakitau*** places aṭ/āṭ (ṭit, at the beginning) and tuk
  (kit, at the end). It reads the marker from the augment's upadeśa, because
  the augment is placed as taught. tuk is added to the vowel before ch
  (6.1.71 *hrasvasya*), so its t is written at the end of that vowel, in the
  vowel's term: in laṅ of *cham* it ends the augment's term (*at + cham*).

## Engine exceptions (vacanasāmarthya)

Two it-rules must not apply where the grammar's own wording shows they can't.
The tradition argues these from *vacanasāmarthya* ("otherwise the rule would
be pointless"). A local resolver can't make that argument, so each exclusion
is written into the rule and shown as a near-miss note in the trace.

- **A3: 1.3.7 *cuṭū* skips the jh of *jhi*/*jha*.** 7.1.3 *jho 'ntaḥ*
  replaces that jh, which would be impossible if it were a marker.
- **1.3.8 *laśakvataddhite* skips the l of laṭ/laṅ.** 3.4.77 *lasya* ("in
  place of l") refers to that l, so it must survive.

## Kiparsky vs. tradition

Across all 162 forms, comparing our step order with Vidyut's (a stand-in for
the traditional derivation), every pair of operational rules applied in a
different order acts on independent material. Examples: 6.1.97 merging
*a + anti* before or after 7.3.84 guṇa on the root, or 6.4.71 aṭ before or
after 7.1.3. These pairs commute, and the engine orders them by sūtra number,
arbitrarily. Every pair where order matters (pinned in `tests/test_goldens.py`)
agrees with the traditional order. Slice 1 therefore shows no case where
Kiparsky's meta-rules and the tradition derive differently. The debated cases
lie outside laṭ/laṅ of these roots (Joshi & Kiparsky's *adhītya*,
*sed-vas-Ṅas*) and are slice 2's job.

## Notes for slice 2

- **Nitya depends on step granularity.** 3.1.68 counts as nitya over 7.3.84
  partly because the newly inserted śap isn't yet tagged sārvadhātuka in the
  very next state. The derivation search in slice 2 should compare
  derivations, not single states, which removes this sensitivity.
- **The one-step checks ignore blocking and marker reading.** `still_applies` and
  the commutation check apply a rule's edit and look again, but they don't apply A2
  (markers of a new term) and they don't ask whether a rule that still matches is
  now blocked. 7.1.5 (slice 1.5) shows both (see "Task 9" below).
- **The tripādī never re-checks a blocked candidate.** It stays skipped even
  if its blocker later disappears. No slice-1 form is affected.
- **The page build looks for the style skill in a fixed home-directory
  location.** `PANINI_STYLE_DIR` overrides it, which is enough for a
  personal tool.

## Known limitations

- **No 8.4.46–47 doubling** (*aco rahābhyāṃ dve*, *anaci ca*). Forms are
  given undoubled.
- **No 8.4.68 *a a*** (closed ă). It is invisible in IAST.
- **No exceptions to 8.4.40–41.** 8.4.42 *na padāntāṭ ṭor anām* and 8.4.43
  *toḥ ṣi* (which limit 8.4.41) and 8.4.44 *śāt* (which limits 8.4.40) are not
  modelled; no bhvādi form in laṭ or laṅ needs them.
- **6.4.22 *asiddhavat* is detected, not modelled.** When two ābhīya rules
  apply in one derivation, the step carries a warning.
- **6.1.86 *ṣatvatukor asiddhaḥ* is not modelled.** The `tuk_or_satva` flag
  exists, but no slice form needs the shadow evaluation: in *gacchati*, tuk
  isn't affected by 6.1.87–110.
- **1.1.47 *mid aco 'ntyāt paraḥ*** wasn't needed in slice 1 (no mit augment
  occurs); slice 1.5 adds it for num (below).
- **Accent** is out of scope. The only exception is the lexical accent of a
  root's marker vowel, which drives pada (1.3.12, 1.3.72).

# Findings, slice 1.5

## Pada against Vidyut

`scripts/check_pada.py` asks Vidyut which voices it derives for laṭ 3sg of each
bhvādi root and compares with `Root.pada` (read from the marker vowel). 1147 of
1156 roots agree. The nine that don't:

- **śad 01.0991** (ours P, Vidyut A): 1.3.60 *śadeḥ śitaḥ* makes it ātmanepada
  when the stem takes śit. Slice 1.5 Task 7 adds this rule.
- **sthā 01.1077, vad 01.1164, kram 01.0545** (ours P, Vidyut both): the
  alternative middle voice is meaning- or prefix-conditioned (1.3.23, 1.3.47,
  1.3.38–43). Preverbs are out of scope, so the marker-based pada stands.
- **paṇ 01.0507, pan 01.0508** (Vidyut both / parasmaipada only): 3.1.28 gives
  these an *-āya-* stem in the praise sense, which is out of scope here. They
  are now in `OUT_OF_SCOPE`.
- **ṛti 01.1166** (ours P, Vidyut A): 3.1.29 *ṛter īyaṅ* gives an *-īya-* stem,
  which is ātmanepada by ṅit. Now in `OUT_OF_SCOPE`.
- **Two present stems** (3.1.70 for bhram, bhrāś, bhlāś, laṣ; 3.1.75 for akṣ,
  takṣ): Vidyut gives both stems, the engine would give one. These roots are in
  `OUT_OF_SCOPE` until optional rules are modelled. (sṛ 01.1085 also has two
  stems, via 7.3.78; Task 7.)
- **nāth 01.0007, sasj 01.0229** (Vidyut both): not marker-reading bugs (Task 8).
  Vidyut also derives an active of nāth, by the default 1.3.78, although the root's
  marker vowel is anudātta. Vidyut follows the vārttika *āśiṣi nāthaḥ* (on 1.3.21),
  by which nāth is ātmanepada only in the sense of a blessing, a meaning-conditioned
  rule like those for sthā and vad. Our middle-only nāth is therefore a narrowing:
  it gives every sense the voice of the blessing sense. Vidyut also derives the
  middle of sasj (`zasja~`, no accent on the marker) without any pada rule, so its
  data treats that root as taking both voices. Our marker readings (nāth middle by
  1.3.12, sasj active by 1.3.78) stand.

## Whole-class sweep (before the new rules)

The slow sweep compares every available request with Vidyut. Before Tasks 3–9
about a fifth of the 21,708 non-empty reference entries fail, in two groups:
roots with an *i*-marker that inserts a nasal (7.1.58 *idito num dhātoḥ*,
*vandate* not *vadate*, 204 roots), and a mixed group (71 roots): initial
*ṣ*/*ṣṭ* roots (*sṭanati* for *stanati*, 6.1.64 and its ṭu-substitute), 6.4.x vowel lengthening (*ūrdate*),
*ch* doubling (6.1.73 before *ch*), the *yam*/*sad* stems (7.3.78),
*kṛp* → *kalpate*, and *vraj* losing its initial *v* (a bug, fixed in Task 8).

## 7.3.78 and 1.3.60

- **śad 01.0991** is ātmanepada only: 1.3.60 *śadeḥ śitaḥ* applies before the
  ś-affix śap, so `availability` rules out the active (reason cites 1.3.60) and
  the engine assigns the middle by 1.3.60, blocking 1.3.78.
- **sṛ 01.1085** has two stems, *sarati* and *dhāvati*. The tradition restricts
  7.3.78's *dhau* to fast motion (Kāśikā *vegitāyāṃ gatau*); the engine cannot
  know the sense, so the substitution is an optional rule of its own kind
  (`Optionality.SENSE`: not applied by default, the alternative noted), giving *sarati* first and *dhāvati* as an alternative, in Vidyut's order.
- **ṛ 01.1086 laṅ** (9 requests): Vidyut also gives *ārchat* beside *ārcchat*,
  since 8.4.65 *jharo jhari savarṇe* optionally drops one *c* of *rcch*. The
  engine has no 8.4.65 yet, so only *ārcchat* is derived. XFAIL.
- 7.3.78 replaces the whole root, so it overrides guṇa (7.3.84, 7.3.86).
  In laṅ of ṛ, 6.1.90 (nitya) merges ā + ṛ first. 6.1.85 antādivat makes that
  substitute part of the root as well, so 7.3.78 still applies, and by 1.1.56
  sthānivat the stem takes the root's place in the ekādeśa. The engine records
  on each ekādeśa sound the rule and the two sounds (`Sound.ekadesha_rule`,
  `ekadesha_inputs`) and `meta.substitution_edit` applies that rule again to the
  stem's sound: ā + ṛ → ār, then *ccha* (*ārcchat*).
- Declined optional rules (vibhāṣā, as for sṛ) are recorded per rule and terms
  by the engine: they are not offered again and block nothing, in every branch.

## 7.1.58, 1.1.47 and 6.4.24

- **7.1.58 *idito num dhātoḥ*** gives a root marked with a final *i* the
  augment num (*kradi~* → *krand-*). It reads the marker the it-rules set
  (1.3.2) and the upadeśa, because *i~r* (*dṛś*, `df\Si~r`) is the marker
  *ir*, not *i*: 1.3.2 marks that nasal *i* too, so the marker alone can't
  tell them apart. The nasal then goes through the tripādī: 8.3.24 makes it
  anusvāra before an obstruent and 8.4.58 turns that into the nasal of the
  following stop (*krandati*, *vaṅkate*, *kampate*).
- **1.1.47** places the augment right after the root's last vowel
  (`meta.mit_position`). In laṅ of a vowel-initial root (*and* → *āndat*), āṭ
  and the root's vowel may already have merged (6.1.90), leaving the root
  with no vowel of its own. The merged vowel counts as the root's first sound
  (6.1.85), so num goes at the start of what remains. An augment's sound
  written after the merged vowel (tuk, *ā t + ch*) is passed over when looking
  for it, so num still applies after tuk; it is therefore nitya and wins
  (*āñchat*, *auñchat*).
- **6.4.24 *aniditāṃ hala upadhāyāḥ kṅiti*** is the contrast: roots *not*
  marked with *i* lose a penultimate nasal before a kit/ṅit affix, which is
  why the *i* marker matters. It is not traced in this slice: in laṭ and laṅ
  the root is always followed by śap, which is neither kit nor ṅit, so the
  rule can never come close to applying and a near-miss note would mislead.
  Its text and gloss are in `sutras.toml`.
- After 7.1.58, 6 of the 196 *i*-marked roots still fail the sweep, for
  missing sound rules rather than the augment: *stambh* (the ṣṭ-initial bug,
  Task 4), *ghiṇṇ*, *ghuṇṇ*, *ghṛṇṇ* (n before ṇ needs 8.4.41 *ṣṭunā ṣṭuḥ*:
  ours *ghinṇate*), and *riṇv*, *raṇv* (n after r needs 8.4.1–2 ṇatva: ours
  *rinvati*).

## ṇatva after ṛ (8.4.1.1) in ghṛṇṇ

For *ghṛṇ* (`GfRi~\`) our trace cites the vārttika 8.4.1.1 *ṛvarṇāc ceti vaktavyam* (ṛ/ṝ trigger ṇatva, as in *nṛṇām*) for the n that num inserts (it follows ṛ); Vidyut cites 8.4.41 alone (the n before ṇ). The form is the same (*ghṛṇṇate*). We cite the vārttika because the tripādī runs once in sūtra order (8.2.1 pūrvatrāsiddham), and 8.4.1.1 precedes 8.4.41, so it fires first and 8.4.41 then has nothing left to change.

## Task 8: bugs from the sweep

- **6.1.66 *lopo vyor vali* spares a root's initial v/y.** The rule deleted any
  y/v before a consonant other than y, including the v that *vraj* and *vraṇ*
  begin with (*rajati*). If the rule always deleted that v, teaching these roots
  with it would be pointless, so by *vacanasāmarthya* it does not apply there.
  Vidyut 0.4 makes the same exception (`ac_sandhi.rs`, `try_lopo_vyor_vali`:
  "otherwise roots like vraj would be vyartha"). Like A3 and 1.3.8, the exclusion is
  written into the rule, with a near-miss note and a reading that cites it. The y of
  *iy* (7.2.81, *aidhetām*) is still deleted.
- **`CadiH` 01.0925** is not a recited upadeśa but the root *chad* cited by name,
  *chadiḥ* (the root plus ik in the nominative, as roots are named by the vārttika
  *ik-śtipau dhātunirdeśe* on 3.3.108). Vidyut special-cases it as bare *chad*
  (`dhatu_karya.rs`). `scripts/vendor_dhatupatha.py` now rewrites it as the upadeśa
  `Cada~` (parasmaipada, not idit): *chadati*. The trace therefore shows a marker
  vowel ã that the source entry doesn't have.
- **6.4.25 *daṃśasañjasvañjāṃ śapi* and 6.4.26 *rañjeś ca*** are in: daṃś, sañj,
  svañj and rañj lose their penultimate nasal before śap (*daśati*, *sajati*,
  *svajate*, *rajati*). Each is one small rule naming its roots by upadeśa, with
  *na lopaḥ* (6.4.23) and *upadhāyāḥ* (6.4.24) carried over. 6.4.24 itself is
  still not traced (śap is not kit or ṅit).
- **6.1.73 *che ca* against 7.3.86 for yuch 01.0242 and uch 01.0244: a gap in the
  grammar, closed by storing the roots with *cch*.** On *yuch + a + ti* the two rules
  bleed each other. Inserting *t* makes the *u* heavy (1.4.11), so full grade can't
  apply. Full grade makes the vowel long, so 6.1.73 can't apply (6.1.75 adds the same
  *t*). Neither nitya nor the siddha principle decides (Kiparsky, "Pāṇini is slick",
  on *ṛch*). The extended siddha principle makes it worse, since it predicts
  *\*yocchati* even more strongly. Under Joshi and Kiparsky's framework only an
  explicit asiddha stipulation or an exception rule could block *\*yocchati*, and the
  Aṣṭādhyāyī has neither for yuch. The tradition gets *yucchati* from the antaraṅga
  paribhāṣā, which the spec excludes. Vidyut gets it by running 6.1.73 at an earlier
  stage.
  - **Ruling (user):** `scripts/vendor_dhatupatha.py` rewrites the two roots as
    `yucCa~` and `ucCI~`. With *cch* stored, neither rule applies: *yucchati*,
    *ayucchat*, *ucchati*, *aucchat*. This is a stipulation that closes the gap, not a
    traditional reading. The dhātupāṭha's upadeśas have a single *ch* (*yucha*
    pramāde, *uchī* vivāse). They are recited and printed as *yuccha* and *ucchī* only
    because 6.1.73 applies in saṃhitā. Lookup still accepts *yuch*, *uch* and *uchī*
    (`TAUGHT_AS` in `lexicon.py`). The 27 requests now match Vidyut.
  - **Cost:** the trace no longer shows 6.1.73 for these roots. The fix also can't be
    applied to every root in *ch*. *prach* (tudādi) has to keep a single *ch*:
    stored as *pracch*, it would break 6.4.19 *chvoḥ śūḍ anunāsike ca* for *praśna*,
    which forces Patañjali's *cchvoḥ* reparsing that Kiparsky rejects. So the class is
    split arbitrarily: *yuch*, *uch* and (when tudādi comes in) *ṛch* and tudādi *uch*
    get *cch*, and *prach* keeps *ch*. Revisit if a later slice adopts a principled
    ordering device.

## Task 9: closing the sweep

- **7.1.5 *ātmanepadeṣv anataḥ*** (gāṅ 01.1101, 3pl middle). In a middle ending, jh
  becomes *at*, not *ant*, after a base that does not end in short a. After śap's a
  merges into the root's ā (6.1.101) the base ends in ā, so *gā + jhe* → *gā + ate* →
  *gāte* (laṅ *agāta*). It is an apavāda of 7.1.3: wherever it applies, 7.1.3 applies
  too. For every other root of the class the base before the ending ends in śap's a.
  Two things about the trace, both instances of the step-granularity note under
  slice 2:
  - ā + a merge before jh is replaced. That is what nitya gives (6.1.101 applies
    before and after 7.1.3; after the merge 7.1.3 is blocked by 7.1.5), and it is
    Vidyut's order. But the resolver gets there by its tie-break: its one-step
    commutation check doesn't see blocking, so the two look order-independent and the
    lower-numbered 6.1.101 goes first.
  - In every middle 3pl, the base is the bare root before śap arrives (*edh + jha*),
    and that root doesn't end in short a, so the trace reports "7.1.3: blocked by
    7.1.5" at that step. Śap then comes first (3.1.68 and 7.1.5 commute while śap
    still has its markers) and, once its markers are deleted, the base ends in a,
    7.1.5 no longer applies, and 7.1.3 applies after all. Nothing in the trace says
    why 7.1.5 dropped out. A resolver whose lookahead reads the markers of a new term
    (amendment A2) reports "7.1.5: deferred: 3.1.68 (nitya)" instead. We tried that.
    It also changes about 200 other traces in the class: new deferral notes for
    6.1.66, reorderings in laṅ 1sg of the 7.3.78 roots, and one rule shown as
    deferred by itself. It also needs the ekādeśa signature to name its terms. So it
    was left out pending a decision.
- **6.4.89 *ūd upadhāyā gohaḥ*** (guh 01.1043). The sūtra names the root as *goha*,
  guh in its full grade (as the commentaries read it), so the engine applies guṇa
  first (7.3.86, *goh*) and then replaces the penultimate o by ū before the vowel of
  śap (*aci*, from 6.4.77): *gūhati*, *agūhata*. The wording is what keeps the rule out
  of forms without guṇa (before a kit/ṅit affix, as in the perfect *juguhatuḥ*); no
  extra condition is needed. Vidyut applies 6.4.89 to *guh* directly, in place of
  guṇa (`asiddhavat.rs`, conditioned on a non-kṅit affix). Same form, different trace.
- **8.2.18 *kṛpo ro laḥ*** (kṛp 01.0866 and 01.0875). In the root kṛp, r becomes l:
  after guṇa *karp* → *kalp*, *kalpate*. Both roots taught as kṛp are meant (the
  sūtra names the root by its shape, as it does elsewhere); *krap* 01.0876 is not.
  The rule also covers the r heard inside ṛ (ṛ → ḷ, as in *kḷpta*), which laṭ and laṅ
  never reach because guṇa always applies first.
- **7.1.61 *radhijabhor aci* for jabh: applied by shape; 01.0150 is out of scope.** The
  rule gives radh and jabh the augment num before a vowel-initial affix. Two bhvādi
  entries are taught as jabh, both "gātravināme": `jaBI~\` (01.0453, ātmanepada) and
  `jaBa~` (01.0150, parasmaipada). Vidyut gives num to the first only (*jambhate*,
  *jabhati*), testing `has_u("jaBI~\\")` in `angasya.rs` with no comment, issue or
  cited reason. What the sources say:
  - **Kāśikā** (7.1.61): *radhi jabhi ity etayor ajādau pratyaye num āgamo bhavati*;
    examples *jambhayati, jambhakaḥ, sādhujambhī, jambhaṃjambham, jambho vartate*. No
    restriction to either jabh.
  - **Siddhānta Kaumudī**: *etayor numāgamaḥ syād aci*; *jambhate, jajambhe, jambhitā,
    jambhiṣṭa*. Its dhātupāṭha has one jabh for this sense (*jabhi jṛbhi
    gātravināme*). No restriction.
  - **Mādhavīya Dhātuvṛtti** 266 (printed pp. 120–121; archive.org
    `madhaviyahdhatuv00sayauoft`, scans 174–175): *jabhi jṛbhi gātravināme. 'jabhī ity
    eke, jabdham' iti Maitreyaḥ. ayam eva pāṭhaḥ prāyeṇa vṛttikārasya sammataḥ*. The
    Kāśikā's counterexample *jabdham* shows it takes the *jabhī* reading. Conjugated in
    the middle voice with num, citing 7.1.61: *jambhate, jajambhe, jambhitā …*. At the
    end of the entry: *jabhiḥ vināśanārthe curādau*, and some count a jabh among the
    active-voice roots too.
  - **Kṣīrataraṅgiṇī** (Liebich 1930) I.415–416: *jabha jṛbhi gātravināme. jabhate,
    jṛmbhate. jabhitaḥ … radhijabhor aci iti num: jambhakaḥ, jambhanam, jambhaḥ*.
    Kṣīrasvāmin reads *jabha* at the same place in the list and gives *jabhate*, middle
    voice and without num before śap. He uses 7.1.61 only for derived nouns and gives no
    reason. Under X.176 he repeats it (*bhvādau jabha jṛbhi jambhane: jabhate*) and adds
    *Candro jabhety āha*. At I.1029, after *yabha*: *jabhi ceti Daurgāḥ: jambhati (VII,
    1, 61)*, a separate active-voice jabh of the Daurga school.
  - ashtadhyayi.com's root data (Vidyut's source) notes on 01.0150 that it is a
    variant reading of *jabhī* (1.453), absent from the Siddhānta Kaumudī and found in
    the Kṣīrataraṅgiṇī, and tags it ātmanepada. Vidyut's `jaBa~` has no
    unaccented-vowel mark, so it is conjugated as parasmaipada.

  **Ruling (user):** 7.1.61 applies to every root whose bare form is raD or jaB, as
  the sūtra's wording reads. 01.0453 gives *jambhate*, as the Siddhānta Kaumudī, Mādhava
  and Vidyut give it. 01.0150 is in `OUT_OF_SCOPE`, with a reason the explorer shows. It
  is Kṣīrasvāmin's reading of the same root, and his *jabhate* (no num before śap)
  can't be derived from the sūtra as worded. Vidyut's *jabhati* is attested in no
  source: Kṣīrasvāmin has middle voice and no nasal, the Daurgas active voice with the
  nasal. So there is no reference form to compare against. Vidyut's restriction by
  upadeśa happens to reproduce Kṣīrasvāmin's missing nasal, but with a voice he doesn't
  give. 7.1.62 *neṭy aliṭi radheḥ* (radh before iṭ) isn't reached in laṭ and laṅ, and
  radh isn't a bhvādi root.
- **Citation names** now quote a taught nasal at the place of the consonant after it,
  as the tripādī would pronounce it: *sañj*, *svañj*, *rañj*, *añc*, *tump*,
  *śrambh* (ṃ before a sibilant or h, as in *daṃś*; n before a dental). A name is only
  a display label. Lookup (CLI and explorer) drops every diacritic, so plain spellings
  work (*sanj*, *dams*, *stha*), though a spelling with its diacritics is tried first
  in the CLI, so *pat* stays *pat*, not *paṭ*. The nasal must be the one the name now
  uses: *tunp*-style spellings no longer resolve (the upadeśa *tunpa* still does).

## Where slice 1.5 ends

The slow sweep checks 21,564 requests over 1,132 of the 1,156 bhvādi roots (24 are
in `OUT_OF_SCOPE`: other present stems, the *-āya-*/*-īya-*/ṇiṅ suffixes, optional
stems, one variant reading). 21,555 match Vidyut. The 9 documented differences, all in `XFAIL`:

- ṛ 01.1086 laṅ, 9 requests: no 8.4.65 (*ārchat*).
