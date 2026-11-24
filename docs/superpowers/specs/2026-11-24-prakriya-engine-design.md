# Prakriyā engine: design (slice 1)

Date: 2026-11-24
Status: draft, awaiting approval

## Intent

A personal tool for watching Pāṇini's grammar work. The user is not a
Pāṇinian specialist and finds the Aṣṭādhyāyī too compact to apply by hand.
They give a root and a target form (in PIE-style or Pāṇinian terms). The tool
derives the form and prints the derivation (prakriyā) one step at a time. Each
step names the sūtra, glosses it in plain English and shows the form before
and after. It also explains the interesting cases where a rule did _not_
apply, or lost to another rule.

The only user is the author. Readability of the derivation matters more than
speed or coverage.

Where the tradition disagrees, the engine follows Paul Kiparsky's analysis
(papers in `docs/papers/`, especially _On the Architecture of Pāṇini's
Grammar_ §1.4.2, §1.6, §4.2, and Joshi & Kiparsky, _The extended
siddha-principle_).

## Goals (slice 1)

- Derive every **laṭ** (present) and **laṅ** (imperfect, technically "past
  not of today", 3.2.111) form of a small set of **bhvādi** roots: 3 persons
  × 3 numbers, parasmaipada and ātmanepada as each root allows, kartari
  (agent) voice only.
- Print a readable derivation trace (format below).
- Accept requests in PIE-style labels and in Pāṇinian labels. Show how the
  first map onto the second.
- Keep the meta-rules explicit and inspectable as data, not buried in
  control flow: blocking relations, rule sections, asiddha domains.
- Structure rules so the slice-2 resolver (extended siddha principle,
  derivation search) can be dropped in without rewriting rules.

## Non-goals (slice 1)

- Accent. It is a future slice. **One exception:** the lexical accent of a
  root's marker vowel is recorded as data, because pada assignment depends
  on it (1.3.12 _anudāttaṅita ātmanepadam_, 1.3.72 _svaritañitaḥ…_).
  Nothing derives or prints accent.
- Other gaṇas, lakāras, kṛt/taddhita, subanta, compounds, sandhi between
  words, passive/impersonal (karmaṇi/bhāve) prayoga, causatives and other
  secondary roots.
- Optional rules (vā / vibhāṣā / anyatarasyām). Slice-1 roots are chosen to
  avoid them. If one is reached, the engine stops with a clear "optional rule
  not supported yet" error. **Exception (design call):** the optional
  tripādī doubling rules 8.4.46–47 (_aco rahābhyāṃ dve_, _anaci ca_) are
  triggered by the endings themselves (e.g. -dhve, and the c of
  _gacchati_), so no choice of roots avoids them. Slice 1 leaves them
  **unimplemented**. Forms are given undoubled, the usual citation form,
  and this is recorded as a known limitation in the README. They come back
  when optional rules are supported.
- Automatic anuvṛtti parsing. Each rule's gloss is written out with the
  inherited words filled in by hand.
- Inferring specificity (utsarga/apavāda) automatically from rule conditions.
- Performance.
- Full 6.4.22 _asiddhavat_ semantics (see "Asiddha domains").

## Anti-goals (would make this a failure even if output is correct)

- **Right forms for the wrong reasons.** Rule-specific ordering hacks or
  hard-coded sequences that bypass the resolver. If the meta-rules as
  implemented give a wrong form, that is a finding to surface, not a thing
  to patch around quietly.
- **Silent guessing.** If the resolver cannot decide between non-commuting
  rules, it raises an error that names the rules and the form. It never
  picks one arbitrarily.
- **Unreadable traces.** Dumping every rule checked at every step, or
  internal encodings, in the default view.

## Constraints

- Python ≥ 3.15, managed with uv (existing scaffold: `pyproject.toml`,
  `src/panini/`).
- Terminal output. IAST for all user-facing input and output.
- Personal use, single machine.

## Approaches considered

**A. Hand-ordered pipeline (Vidyut style).** Each derivation is code that
calls rules in a fixed sequence, with if/else standing in for blocking.
Quickest route to correct forms, but the meta-rules disappear into control
flow, and every "why not" note has to be hand-written. It defeats the point
of watching Pāṇini's system decide. Rejected.

**B. Declarative rules + local resolver (restricted siddha principle).** At
each step: collect every rule with a site where it applies, remove blocked
candidates, then prefer the rule that stays applicable whichever other
candidate fires first (the nitya effect, one step of lookahead). Simple, and
each step explains itself. Wrong for Joshi & Kiparsky's lookahead cases
(_adhītya_, _sed-vas-Ṅas_), but those involve absolutives, participles and
case endings, not bhvādi laṭ/laṅ.

**C. Declarative rules + derivation search (extended siddha principle).**
Explore the possible orders of application. Pairs that commute collapse
into one branch. Choose the derivation that maximizes _crucial_ siddha
relations (Joshi & Kiparsky, Definition 2). Faithful to Kiparsky, and it
can show the road not taken, but noticeably more to build and debug.

**Chosen: B for slice 1, C as slice 2.** Rules are written now so that C
needs only a new resolver: they are pure find/rewrite functions, and two
rewrites can be applied simultaneously to the same input.

## Design

### Representation

- **Phoneme.** A single sound, plus flags. The key flag is `it` (marked as
  a marker, _it-saṃjñā_). Internal encoding is the builder's call (SLP1, one
  character per phoneme, is convenient). Marker status is a flag, never a
  different letter.
- **Term.** One morpheme-sized unit in the derivation: a root, an affix, an
  augment. It holds:
    - its _upadeśa_ (form as recited);
    - its current phonemes;
    - a set of saṃjñās (dhātu, pratyaya, tiṅ, sārvadhātuka, aṅga, pada, …);
    - any lexical data (e.g. marker-vowel accent for roots).
- **State.** An immutable sequence of terms plus the speaker's intent
  (_vivakṣā_). The intent records which meanings the grammar responds to:
    - time: present, or past not of today;
    - person, as coreference with the addressee, the speaker, or neither
      (1.4.105–108);
    - number;
    - whether the action's fruit goes to the agent, _kartrabhiprāya_
      (1.3.72).

    Rules like 3.2.123 _vartamāne laṭ_ and 1.4.22 read the intent. They do not
    read a pre-chosen ending. The engine must _derive_ tip, not be handed it.

### Rules

Each rule is a Python object with:

- `id` (e.g. `"3.1.68"`), `text` (IAST), `gloss` (plain English, anuvṛtti
  filled in);
- `section`: main body, or tripādī (8.2.1–8.4.68). Also a membership flag
  for the asiddha domains 6.1.86 (6.1.87–6.1.110) and 6.4.22
  (6.4.23–6.4.175);
- `find(state) -> list[Site]`: every place it applies. A site identifies
  the affected terms/positions, so the engine can tell when two sites
  overlap;
- `rewrite(state, site) -> Edit`: the change it makes, as data, applied by
  the engine. This split makes simultaneous application of several rules
  to one input definable, which slice 2 needs;
- `blocks: list[rule id]`: the rules this rule overrides where their domains
  overlap (utsarga/apavāda). A list, so collective blocking
  (e.g. 6.1.101 over 6.1.77 and 6.1.87) is one entry with several ids.
  Hand-annotated;
- optional `near_miss(state) -> str | None`: a hand-written explanation of
  why a teaching-relevant rule did not apply. Example: 7.3.86 for paṭh,
  "upadhā _a_ is not an ik vowel (1.1.3)".

Rule logic lives in Python modules grouped by adhyāya/pāda. Sūtra text and
glosses may live in a data file next to them (builder's call).

The it-rules (1.3.2–1.3.9) are ordinary main-body rules, not a preprocessing
step, so they appear in the trace.

### Main-body resolver (slice 1, approach B)

Loop until no candidates remain:

1. **Collect.** Every (rule, site) pair where `find` succeeds. Exclude a
   pair whose rule has already applied at that site to the same input
   (no-reapplication guard).
2. **Block.** Drop a candidate (B, s) if some rule A with B in `A.blocks`
   has a candidate site overlapping s.
3. **Para (narrow).** If two candidates assign conflicting saṃjñās to the
   same term and both rules lie in the ekasaṃjñā domain (1.4.1–2.2.38), the
   later one wins (1.4.2, as restricted by Kiparsky). Nowhere else does
   textual order decide anything in the main body.
4. **Nitya preference.** Prefer a candidate X such that, for every other
   candidate Y, X is still applicable after Y applies, but not vice versa.
   _Definition (design call, revisit in slice 2, where Definition 2
   replaces it):_ "X is still applicable after Y" means X's `find` returns
   a site on the same term(s) and its `rewrite` would produce the same
   change. If Y alters the material X would rewrite, so that X would now do
   something different, X does **not** count as still applicable. That is
   the traditional _śabdāntaraprāpti_ exception. It-marking and it-deletion
   rules count as Ys like any other rule.
5. **Remaining ties.** If several candidates remain, the engine checks that
   they commute: applying them in either order gives the same state. If
   they do, apply the lowest sūtra number. The order is arbitrary, the
   result is not. If they don't commute, raise `UnresolvedConflict`, naming
   the rules, the sites and both outcomes.
6. **Apply** the chosen candidate and record the step, including which
   competitors lost and why (blocked by X / deferred for nitya X).

A hard step limit guards against loops and raises with the trace so far.

### Choosing the tiṅ ending (design call)

3.4.78's `find` reads the intent through the category labels, the way the
traditional prakriyā does. It doesn't branch. The ending substituted for
_l_ is the one whose labels match what the intent requires:

- pada: 1.3.12 / 1.3.72 / 1.3.78 → 1.4.99–100;
- puruṣa: 1.4.105–108 → 1.4.101;
- vacana: 1.4.22 → 1.4.102.

The trace cites these rules as the justification for picking tip. The
engine is never handed "tip". It is handed "agent not coreferent with
addressee or speaker; one; fruit not to agent" and works out the rest.

### Substitutes and augments as explicit meta-rules (design call)

- **1.1.56 _sthānivad ādeśo 'nalvidhau_** is an explicit, inspectable
  meta-rule. A substitute inherits the saṃjñās and markers of what it
  replaces, except for rules conditioned by a single sound (_al-vidhi_),
  per the sūtra's own wording. Kiparsky (_Architecture_ §3.3.3) stresses
  that this is how the tiṅ endings inherit the markers of the _l_. E.g. in
  laṅ the ending counts as ṅit, so 3.4.99–100 apply. Each Term records
  what it replaced, so inherited properties can be shown in the trace
  ("ti counts as ṅit via 1.1.56").
- **1.1.46 _ādyantau ṭakitau_** (placement of ṭit/kit augments: aṭ, āṭ,
  tuk) and **1.1.47 _mid aco 'ntyāt paraḥ_** are explicit placement
  meta-rules consulted by the engine when it applies an augment. They are
  not hard-coded per rule.

### Tripādī

After the main body finishes, the engine walks the tripādī rules once, in
sūtra order. Each rule applies at all its sites, and the engine never
returns to an earlier rule or to the main body. That is 8.2.1
_pūrvatrāsiddham_. Blocking still holds inside the tripādī: before applying
rule R at site s, check whether a rule that blocks R applies at an
overlapping site. Kiparsky: "strictly in order, modulo blocking."

### Asiddha domains inside the main body

- **6.1.86** _ṣatvatukor asiddhaḥ_. Rules 6.1.87–6.1.110 are invisible to
  ṣatva and tuk rules. Implement it narrowly: when a ṣatva/tuk rule
  evaluates `find`, it sees the state with those rewrites undone. Needed
  when gam → gaccha (7.3.77 then 6.1.73 tuk) meets vowel-sandhi rules.
  The builder should confirm whether any slice-1 form exercises it; if not,
  implement it with a test from outside the slice or defer it with a
  recorded limitation.
- **6.4.22** _asiddhavat atrā bhāt_. Full semantics (invisibility among
  6.4.23–175 rules sharing a conditioning environment) are deferred. Slice 1
  only _detects_ when two rules from that range apply in one derivation and
  marks the trace with a warning. 6.4.71/6.4.72 (the aṭ/āṭ augments) are in
  that range.

### Request vocabulary

- PIE-style input: _present imperfective_ → laṭ; _past imperfective_ → laṅ
  (the trace notes that laṅ is "past not of today"). _Active_ →
  parasmaipada; _middle_ → ātmanepada (i.e. kartrabhiprāya for ubhayapada
  roots). Person 1/2/3 → uttama/madhyama/prathama via the intent;
  sg/du/pl → eka/dvi/bahuvacana.
- Pāṇinian input: lakāra, puruṣa, vacana, pada names directly.
- An impossible request gets an explanation with the governing rule, not a
  form. Example: "edh, active" → edh takes only ātmanepada (1.3.12, its
  marker vowel is anudātta).

### Display conventions

- IAST throughout.
- **Markers in capitals, from the moment they are marked.** A sound appears
  lowercase as recited, becomes capital at the 1.3.2–1.3.8 step that marks
  it, and disappears at 1.3.9. Example: tip → tiP → ti. The nasal sign on a
  marker vowel stays visible until it is marked, since 1.3.2's condition
  depends on it.
- Default view: applied steps (sūtra id, text, gloss, before → after) plus
  `near_miss` notes. Several rules that apply as one logical step, e.g.
  1.3.3 + 1.3.9, may be shown on one line.
- `-v` adds losing competitors and the reason they lost. `-vv` adds every
  rule checked (for debugging).

Target shape of the default output:

```
paṭh-, laṭ, 3sg parasmaipada  →  paṭhati

 1  paṭha~            1.3.1    bhūvādayo dhātavaḥ    'paṭha~' is a root (dhātu)
 2  paṭhA~            1.3.2    upadeśe 'janunāsika it  nasal a is a marker
 3  paṭh              1.3.9    tasya lopaḥ           markers are deleted
 4  paṭh + laṭ        3.2.123  vartamāne laṭ         present time → laṭ
 …
    ↳ 7.3.86 (guṇa of light penultimate) does not apply: a is not ik (1.1.3)
 n  paṭhati
```

### CLI

- `panini derive <root> <lakāra|tense> <person> <number> [<voice>]`: one
  derivation. Both vocabularies are accepted.
- `panini paradigm <root> <lakāra|tense> [<voice>]`: a 3×3 table of final
  forms. `--trace` prints each derivation.

Exact argument syntax and CLI library are the builder's call.

### Lexicon (slice 1)

Hand-curated dhātupāṭha entries: upadeśa, gaṇa, meaning, marker-vowel
accent / pada class. Chosen to cover distinct rule interactions with no
optional rules:

| root | upadeśa                 | pada | exercises                                                            |
| ---- | ----------------------- | ---- | -------------------------------------------------------------------- |
| bhū  | bhū                     | P    | guṇa 7.3.84, ayādi 6.1.78, 7.3.101, 6.1.97, visarga (8.2.66, 8.3.15) |
| paṭh | paṭha~                  | P    | 1.3.2 marker vowel, 7.3.86 near-miss                                 |
| gam  | gamḷ                    | P    | 7.3.77 chaḥ, 6.1.73 tuk, 8.4.40 ścutva                               |
| smṛ  | smṛ                     | P    | ṛ-guṇa with 1.1.51 uraṇ raparaḥ                                      |
| edh  | edha~ (anudātta marker) | Ā    | ātmanepada endings 3.4.79–80, 7.2.81, āṭ + 6.1.90 in laṅ             |
| nī   | ṇīñ                     | U    | 6.1.65 ṇo naḥ, ñ-marker → 1.3.72 ubhayapada                          |
| pac  | ḍupacaṣ                 | U    | 1.3.5 ḍu-marker, ṣ marker                                            |

The builder should verify each upadeśa against a standard dhātupāṭha and
may swap a root if it unexpectedly hits an optional rule. The replacement
must keep the coverage in the right-hand column.

### Testing

- pytest.
- **Paradigm tests.** Every slice-1 form (≈160) is compared against a
  reference table.
- **Golden trace tests** for a handful of forms (_paṭhati_, _bhavanti_,
  _gacchati_, _aidhata_, _abhavam_). _Design call:_ a golden asserts
    - the **set** of rules applied, and
    - the **relative order of non-commuting pairs only**.

    It does not assert the exact sequence, since commuting ties are ordered
    arbitrarily. Use forms whose traditional derivation (Siddhānta Kaumudī)
    is well attested. If the resolver's order of a non-commuting pair differs
    from SK but the final form is right, record it as a finding (Kiparsky vs.
    tradition) in a findings file. It is not a test failure.

- **Meta-rule tests**: blocking (including collective), the no-reapplication
  guard, `UnresolvedConflict` on a constructed non-commuting tie, the
  tripādī being one-pass.
- Reference forms: build the table from a standard source. If Vidyut's
  Python bindings install on 3.15, use them as an optional dev-only oracle
  for cross-checking (not a runtime dependency).

## Slice 2 preview (approach C), and what slice 1 must preserve

Slice 2 replaces the main-body resolver with a search over derivations,
scored by crucial siddha relations (Definition 2), and tests it on the
Joshi & Kiparsky examples. Slice 1 must therefore keep:

- rules side-effect free (`find`/`rewrite` over immutable state);
- `Edit`s composable, so "apply A and B simultaneously" is defined; if
  their sites overlap, report a conflict;
- the resolver behind an interface (`Resolver.next_step(state, candidates)`
  or similar), so B and C can be swapped and compared;
- trace steps able to carry "alternatives considered" for C's road-not-taken
  notes.

## Left to the builder

Module layout; internal phoneme encoding; data file format for sūtra
text/glosses; CLI library and argument syntax; exact gloss wording; how
`Site` and overlap are represented; whether trace rendering is a separate
module.
