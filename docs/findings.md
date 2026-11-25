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
  the augment is placed as taught.

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
- **The tripādī never re-checks a blocked candidate.** It stays skipped even
  if its blocker later disappears. No slice-1 form is affected.
- **The page build looks for the style skill in a fixed home-directory
  location.** `PANINI_STYLE_DIR` overrides it, which is enough for a
  personal tool.

## Known limitations

- **No 8.4.46–47 doubling** (*aco rahābhyāṃ dve*, *anaci ca*). Forms are
  given undoubled.
- **No 8.4.68 *a a*** (closed ă). It is invisible in IAST.
- **6.4.22 *asiddhavat* is detected, not modelled.** When two ābhīya rules
  apply in one derivation, the step carries a warning.
- **6.1.86 *ṣatvatukor asiddhaḥ* is not modelled.** The `tuk_or_satva` flag
  exists, but no slice form needs the shadow evaluation: in *gacchati*, tuk
  isn't affected by 6.1.87–110.
- **1.1.47 *mid aco 'ntyāt paraḥ*** isn't implemented, since no mit augment
  occurs in the slice.
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
  these an *-āya-* stem in the praise sense, which is out of scope here. Vidyut
  returns no middle forms at all for pan, so its fixture entries are empty (see
  the XFAIL table). Candidates for `OUT_OF_SCOPE`.
- **ṛti 01.1166** (ours P, Vidyut A): 3.1.29 *ṛter īyaṅ* gives an *-īya-* stem,
  which is ātmanepada by ṅit. Out of scope; Vidyut's active fixture entries
  are empty. Candidate for `OUT_OF_SCOPE`.
- **nāth 01.0007, sasj 01.0229** (Vidyut both): unexplained. Both are marker
  readings worth a second look before slice 1.5 closes.

## Whole-class sweep (before the new rules)

The slow sweep compares every available request with Vidyut. Before Tasks 3–9
about a fifth of the 21,708 non-empty reference entries fail, in two groups:
roots with an *i*-marker that inserts a nasal (7.1.58 *idito num dhātoḥ*,
*vandate* not *vadate*, 204 roots), and a mixed group (71 roots): initial
*ṣ*/*ṣṭ* roots (*sṭanati* for *stanati*, 6.1.64 and its ṭu-substitute), 6.4.x vowel lengthening (*ūrdate*),
*ch* doubling (6.1.73 before *ch*), the *yam*/*sad* stems (7.3.78),
*kṛp* → *kalpate*, and *vraj* losing its initial *v* (a bug, to be
investigated).
