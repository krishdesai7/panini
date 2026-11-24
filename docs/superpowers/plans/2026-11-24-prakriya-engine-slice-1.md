# Prakriyā Engine Slice 1: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Pāṇinian derivation engine for laṭ/laṅ of seven bhvādi roots, with a local (restricted-siddha) resolver, a one-pass tripādī, a text trace, and a generated HTML explorer.

**Architecture:**

- Rules are declarative `Rule` objects. Each has `find`/`rewrite` functions over an immutable `State`, plus hand-annotated `blocks` lists.
- An engine loop collects candidates, and a pluggable `Resolver` picks one: blocking → narrow para → nitya → commuting tie-break, else `UnresolvedConflict`.
- After the main body, the tripādī runs once in sūtra order.
- Every derivation produces a `Derivation` record (JSON-serializable). The CLI trace, the tests and the static HTML page all consume it.

**Tech Stack:** Python 3.15 (stdlib only at runtime; `tomllib` for sūtra data), uv, pytest. Vidyut 0.4 (dev-only, generates the reference fixture). Plain HTML/CSS/JS for the page, styled by the `krish-frontend-style` skill.

**Spec:** `docs/superpowers/specs/2026-11-24-prakriya-engine-design.md`. Read it first. Every task implements part of it. Its "Amendments during planning" section records five decisions made while writing this plan.

## Global Constraints

- All Python runs through uv: `uv run pytest`, `uv run panini …`. Never call `python` directly (a hook blocks it).
- No runtime dependencies. Dev dependency group: `pytest`, `vidyut==0.4.*`.
- Everything the user sees is in IAST. The internal phoneme encoding is SLP1, one character per phoneme.
- Markers (it) display as capitals once marked, are lowercase before that, and the nasal sign `~` always stays visible.
- No rule-specific ordering hacks. A form the meta-rules get wrong becomes `expected_failure` with an explanation in `docs/findings.md`. Fixing a wrong or missing `blocks` entry is allowed, and each entry cites the utsarga/apavāda relation in a comment. Adding a meta-principle (e.g. word-internal antaraṅga) needs the user's OK.
- The resolver never guesses. Non-commuting ties raise `UnresolvedConflict`.
- Fonts are never committed. `build/` is gitignored.
- HTML/CSS work: load the `krish-frontend-style` skill first. Use the app register, liquid-glass dark mode, and the skill's `assets/base.css` (trimmed).
- Work on a feature branch (`slice-1`), not `main`.

## Review Focus

1. **IAST typed in decomposed Unicode** (e.g. `paṭh` with a combining dot below), or with a trailing hyphen (`paṭh-`). Root lookup should still find it. The test is in Task 4.
2. **An unknown root at the CLI.** It should give a clear error listing the available roots, not a traceback. The test is in Task 10.
3. **One derivation raising** (e.g. `UnresolvedConflict`) during `panini site`. The build should finish, and that cell shows an error status. The test is in Task 11.
4. **Missing font directory.** The site still builds, with a warning on stderr, using the fallback font stacks. The test is in Task 11.
5. **A stale or garbage URL hash** (e.g. `#xyz/laṭ/P/9/sg`, or a root removed from the lexicon). The page should fall back to the first root without a JS error. This is checked by the JS hash-parse unit in Task 11 and by eye in the browser.

---

## File map

```text
pyproject.toml                    dev group, script entry panini = "panini.cli:main"
.gitignore                        build/, .venv/, __pycache__/, .pytest_cache/
src/panini/
  __init__.py                     (empty; delete scaffold main)
  translit.py                     IAST ↔ SLP1
  sounds.py                       pratyāhāras, savarṇa, guṇa/vṛddhi, hrasva/dīrgha
  model.py                        Sound, Term, TermKind, Intent (+enums), State, Span, Site
  edits.py                        edit ops, apply_edit, apply_simultaneous, EditConflict
  meta.py                         1.1.56 substitute_term, 1.1.46 augment placement
  rules/base.py                   Rule, Optionality, sūtra ordering helpers
  rules/__init__.py               ALL_RULES, get_rule
  rules/it.py                     1.3.1–1.3.9, 6.1.64–65
  rules/tin.py                    3.2.111, 3.2.123, 1.3.12/72/78, 3.4.78, 3.4.113, 3.1.68, 1.2.4, 1.4.13, 1.4.14
  rules/anga.py                   7.3.84, 7.3.86 (near-miss), 7.3.101, 7.1.3, 7.3.77, 6.1.73, 7.2.81
  rules/sandhi.py                 6.1.66, 6.1.78, 6.1.87, 6.1.88, 6.1.90, 6.1.97, 6.1.101
  rules/endings.py                3.4.79, 3.4.80, 3.4.99, 3.4.100, 3.4.101, 6.4.71, 6.4.72
  rules/tripadi.py                8.2.23, 8.2.39, 8.2.66, 8.3.15, 8.3.24, 8.4.40, 8.4.56, 8.4.58
  data/sutras.toml                text + gloss per implemented sūtra (plus cited-only sūtras)
  resolver.py                     Candidate, Loser, Choice, Resolver, LocalResolver, UnresolvedConflict
  engine.py                       run(), derive()
  derivation.py                   Status, TermView, StepRecord, Derivation (+to_json)
  lexicon.py                      Root, ROOTS, lookup_root, UnknownRoot
  request.py                      Lakara, Purusha, Vacana, Voice, Request, parse_request, availability
  trace.py                        render_text()
  cli.py                          derive / site subcommands
  site/build.py, site/template.html, site/app.js, site/style.css
scripts/make_reference.py         dev-only: Vidyut → tests/data/reference_forms.json
tests/data/reference_forms.json   committed fixture
docs/findings.md                  Kiparsky-vs-tradition findings, expected failures, known limitations
README.md                         usage + known limitations
```

---

### Task 1: Scaffold, transliteration, sound classes

**Files:**

- Modify: `pyproject.toml`, `src/panini/__init__.py`
- Create: `.gitignore`, `src/panini/translit.py`, `src/panini/sounds.py`
- Test: `tests/test_translit.py`, `tests/test_sounds.py`

**Interfaces:**

- Produces:
    - `iast_to_slp1(text: str) -> str` and `slp1_to_iast(text: str) -> str`. Both NFC-normalize their input. `~` passes through unchanged.
    - `pratyahara(name: str) -> frozenset[str]`. Names are in SLP1: `"ik","ak","ac","hal","Jal","yaR","Kar","val","yaY","eN","ec","Sar","jaS","car","cu","wu"`.
    - `is_vowel(c) -> bool`, `is_savarna(a, b) -> bool`, `guna(c) -> str`, `vrddhi(c) -> str`, `is_hrasva(c) -> bool`, `dirgha(c) -> str`.

- [ ] **Step 1: Branch and scaffold.** Run `git switch -c slice-1`. In `pyproject.toml`:
    - set the description;
    - change the script to `panini = "panini.cli:main"`;
    - add `[dependency-groups] dev = ["pytest", "vidyut==0.4.*"]`;
    - add `[tool.pytest.ini_options] testpaths = ["tests"]`.

    Empty `src/panini/__init__.py`. Add the `.gitignore` from the file map. Run `uv sync`.

- [ ] **Step 2: Write failing tests**

```python
# tests/test_translit.py
import unicodedata
from panini.translit import iast_to_slp1, slp1_to_iast

def test_roundtrip_examples():
    for iast, slp in [("paṭhati", "paWati"), ("gacchati", "gacCati"), ("aidhata", "EData"),
                      ("bhavāmaḥ", "BavAmaH"), ("smṛ", "smf"), ("ṇīñ", "RIY"), ("ḍupacaṣ", "qupacaz"),
                      ("gamḷ~", "gamx~"), ("aṃ", "aM")]:
        assert iast_to_slp1(iast) == slp
        assert slp1_to_iast(slp) == iast

def test_decomposed_input_normalized():
    assert iast_to_slp1(unicodedata.normalize("NFD", "paṭh")) == "paW"
```

```python
# tests/test_sounds.py
from panini.sounds import pratyahara, is_savarna, guna, vrddhi, dirgha

def test_pratyaharas():
    assert pratyahara("ik") == frozenset("iufx") | frozenset("IUFX")   # 1.1.69 savarṇa-inclusive
    assert "a" not in pratyahara("ik")
    assert pratyahara("Jal") >= frozenset("JBGQDjbgqdKPCWTcwtkpSzsh")
    assert pratyahara("yaY") >= frozenset("yvrlYmNRnJBGQD")
    assert pratyahara("val") == pratyahara("hal") - {"y"}

def test_guna_vrddhi():
    assert [guna(c) for c in "iIuUfF"] == ["e", "e", "o", "o", "ar", "ar"]   # 1.1.51 uraṇ raparaḥ
    assert vrddhi("e") == "E" and vrddhi("a") == "A"

def test_savarna_and_dirgha():
    assert is_savarna("a", "A") and not is_savarna("a", "i")
    assert dirgha("a") == "A"
```

- [ ] **Step 3: Run them.** `uv run pytest tests/test_translit.py tests/test_sounds.py -v`. Expected: FAIL (ImportError).

- [ ] **Step 4: Implement both modules.** Build pratyāhāras from the 14 Śiva sūtras, with the final `it` letters excluded. Vowel pratyāhāras include long counterparts (1.1.69 aṇudit). `guna`/`vrddhi` return SLP1 strings. For ṛ/ḷ they return the vowel plus `r`/`l` (1.1.51).

- [ ] **Step 5: Run them.** Same command. Expected: PASS.

- [ ] **Step 6: Commit.** `git add -A && git commit -m "feat: scaffold, IAST/SLP1 transliteration, sound classes"`

---

### Task 2: Data model, edits, sthānivat and augment placement

**Files:**

- Create: `src/panini/model.py`, `src/panini/edits.py`, `src/panini/meta.py`
- Test: `tests/test_model_edits.py`

**Interfaces:**

- Consumes: `translit`, `sounds` (Task 1).
- Produces:
    - **`model.py`:**
        - `Sound(char: str, it: bool = False, nasal: bool = False, agama: bool = False)`, frozen.
        - `TermKind(Enum)`: `ROOT, LA, TIN, VIKARANA, AGAMA`.
        - `Term(kind, upadesha: str, sounds: tuple[Sound, ...], tags: frozenset[str] = frozenset(), markers: frozenset[str] = frozenset(), replaced: Term | None = None)`, frozen. Its members:
            - `Term.from_upadesha(kind, upadesha_slp1: str, tags=frozenset()) -> Term`. `~` after a vowel sets `nasal` on it. The accent marks `\` and `^` are stripped from the sounds and recorded as tags: `"anudattet"`/`"svaritet"` when they sit on the marker vowel, otherwise ignored.
            - `.text -> str`: SLP1 of the current sounds.
            - `.has_marker(m: str) -> bool`: checks its own `markers`, then `replaced.has_marker` (1.1.56).
            - `.has_tag(t) -> bool`: same inheritance.
        - `Time(Enum) PRESENT, PAST_NOT_TODAY`; `Coreference(Enum) NONE, ADDRESSEE, SPEAKER`; `Number(Enum) ONE, TWO, MANY`.
        - `Intent(time, coreference, number, fruit_to_agent: bool)`, frozen.
        - `State(terms: tuple[Term, ...], intent: Intent)`, frozen.
        - `Span(term: int, start: int, end: int)`: half-open sound positions. `end == -1` means the whole term.
        - `Site(spans: tuple[Span, ...])` with `.overlaps(other: Site) -> bool`, and `Site.term(i)` for a whole-term site.
    - **`edits.py`:**
        - Ops (frozen dataclasses): `AddTags(term, tags)`, `MarkIt(term, positions: tuple[int, ...], markers: frozenset[str])`, `DeleteSounds(term, positions)`, `ReplaceSounds(term, start, end, sounds)`, `InsertTerm(index, term)`, `ReplaceTerm(index, term)`, `InsertSounds(term, at: int, sounds)`, `Ekadesha(left: int, right: int, sounds)`.
            - `MarkIt` sets `it=True` on the sounds at those positions and adds the marker letters to `term.markers`.
            - `Ekadesha` replaces the last sound of `left` and the first sound of `right` with `sounds`. It puts them at the end of `left` and deletes the first sound of `right` (6.1.84–85).
        - `Edit = tuple[Op, ...]`.
        - `apply_edit(state, edit) -> State`.
        - `apply_simultaneous(state, edits: Sequence[Edit]) -> State`. It applies ops in descending position order, so indices stay valid. If two edits touch the same sound, or the same term index via Insert/ReplaceTerm, it raises `EditConflict`.
    - **`meta.py`:**
        - `substitute_term(old: Term, kind: TermKind, upadesha: str) -> Term`: 1.1.56. The new term has `replaced=old` and fresh `markers`. Tags and markers are inherited through `has_tag`/`has_marker`.
        - `sthanivat_note(term: Term) -> str | None`. Example: `"ti counts as ṅit via 1.1.56 (it replaced l)"`.
        - `augment_edit(state, target: int, augment: Term) -> Edit`: 1.1.46. A ṭit augment becomes `InsertTerm(target, …)`, before the target. A kit augment becomes `InsertTerm(target+1, …)`.
        - `augment_in_term_edit(state, term: int, after_pos: int, sounds: tuple[Sound, ...]) -> Edit`: kit augment inside a term (tuk), as `InsertSounds` with `agama=True`.
        - 1.1.47 (mit) isn't needed by the slice. Don't add it.

- [ ] **Step 1: Write failing tests**

```python
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
```

- [ ] **Step 2: Run it.** `uv run pytest tests/test_model_edits.py -v`. Expected: FAIL (ImportError).
- [ ] **Step 3: Implement** `model.py`, `edits.py`, `meta.py` per the Interfaces block.
- [ ] **Step 4: Run it.** Same command. Expected: PASS.
- [ ] **Step 5: Commit.** `git commit -am "feat: state model, edits, sthānivat, augment placement"` (with `git add` for new files).

---

### Task 3: Rule type, sūtra data, resolver, engine loop, tripādī

**Files:**

- Create: `src/panini/rules/base.py`, `src/panini/rules/__init__.py` (empty `ALL_RULES = ()` for now), `src/panini/data/sutras.toml`, `src/panini/resolver.py`, `src/panini/engine.py`, `src/panini/derivation.py`
- Test: `tests/test_engine_meta.py` (toy rules only)

**Interfaces:**

- Consumes: Task 2.
- Produces:
    - **`rules/base.py`:**
        - `Optionality(Enum) VA, VIBHASHA, ANYATARASYAM`.
        - `Rule`, a frozen dataclass:
            - `id: str`, `find: Callable[[State], list[Site]]`, `rewrite: Callable[[State, Site], Edit]`;
            - `blocks: tuple[str, ...] = ()`;
            - `near_miss: Callable[[State], str | None] | None = None`;
            - `note: Callable[[State, Site], str | None] | None = None`;
            - `optional: Optionality | None = None`;
            - `assigns: str | None = None` (the saṃjñā name, for 1.4.2);
            - `tuk_or_satva: bool = False`;
            - `reintroduces_upadesha: bool = False` (see the tripādī step below).
        - Properties: `key -> tuple[int, int, int]`; `in_tripadi` (≥ 8.2.1); `in_ekasamjna` (1.4.1–2.2.38); `in_6_1_86_domain` (6.1.87–6.1.110); `in_abhiya` (6.4.23–6.4.175); `text`, `gloss` (from `sutras.toml`, via `sutra_info(id) -> tuple[str, str]`; a missing entry raises `KeyError`).
    - **`resolver.py`:**
        - `Candidate(rule: Rule, site: Site)`, `Loser(rule_id: str, reason: str)`, `Choice(winner: Candidate, losers: tuple[Loser, ...])`.
        - `class Resolver(Protocol): def choose(self, state: State, candidates: Sequence[Candidate], rules: Sequence[Rule]) -> Choice`.
        - `LocalResolver`.
        - `UnresolvedConflict(Exception)` with attributes `rule_ids`, `sites`, `outcomes: tuple[str, ...]`.
    - **`derivation.py`:**
        - `Status(Enum) OK, EXPECTED_FAILURE, UNAVAILABLE, ERROR`.
        - `TermView(chars: tuple[tuple[str, bool], ...])`: (IAST char, is_marker), with `.iast() -> str` rendering IAST with markers in capitals and the nasal `~` kept.
        - `StepRecord(rule_ids: tuple[str, ...], before: tuple[TermView, ...], after: tuple[TermView, ...], note: str | None, losers: tuple[Loser, ...], near_misses: tuple[str, ...], warnings: tuple[str, ...], alternatives: tuple[str, ...] = ())`.
        - `Derivation(request: dict, status: Status, result: str | None, alternatives: tuple[str, ...], reference: tuple[str, ...] | None, steps: tuple[StepRecord, ...], message: str | None)`, with `.to_json() -> dict` (plain JSON types only).
        - `render_terms(terms) -> tuple[TermView, ...]`.
    - **`engine.py`:**
        - `run(state: State, rules: Sequence[Rule], *, resolver: Resolver | None = None, max_steps: int = 400, disabled: frozenset[str] = frozenset()) -> tuple[State, tuple[StepRecord, ...], tuple[str, ...]]`. Returns the final state, the steps, and alternative final forms from optional rules.
        - `StepLimitExceeded(Exception)`, `OptionalRuleNotSupported(Exception)`.

**Main-body algorithm.** This is spec "Main-body resolver", plus two precisions:

1. **Collect.** Gather `(rule, site)` for every non-tripādī rule that isn't disabled. Exclude pairs already applied to an identical `(site, state.terms)` input (the no-reapplication guard).
2. **Block.** Use the raw `find` of every rule, **without the no-reapplication guard**. This matters for niṣedha rules like 1.3.4, whose rewrite is a no-op tag: they keep blocking after they have applied once.
3. **Para.** Only for two candidates with `assigns` on the same term, both `in_ekasamjna`.
4. **Nitya.** As defined in the spec, including the śabdāntaraprāpti exception: compare `rewrite` output on the same terms.
5. **Ties.** Check commutation with `apply_edit` in both orders. If the results are equal, take the lowest `key`. Otherwise raise `UnresolvedConflict`.

**Tripādī algorithm.** Rules run once each, in `key` order, at all their sites, with blocking still checked.

- **Optional rules (amendment A1):** `VA` applies, `VIBHASHA` skips, `ANYATARASYAM` raises `OptionalRuleNotSupported`. The road not taken is computed by finishing the derivation with that rule disabled. It goes into `alternatives` and the step note: `"optional (vā, ‘preferably’ per Kiparsky): also correct: abhavad"`. The same handling applies in the main body.
- **Amendment A2:** after a rule with `reintroduces_upadesha=True` applies (8.2.66 introduces `ru~`), the engine immediately runs the it-rules (ids 1.3.2–1.3.9) on the result, as recorded steps, then continues the tripādī pass.

**Warnings:**

- If two `in_abhiya` rules apply in one derivation, add the warning `"6.4.22: <a> and <b> are both in the ābhīya section; asiddhavat not modelled in slice 1"` to the later step.
- For `tuk_or_satva` rules, `find` is evaluated on the state with every rewrite from an `in_6_1_86_domain` rule undone. Implement this by keeping a shadow state that skips those edits.

**Near-misses.** After each step, call every `near_miss`. Each distinct message is recorded once, on the step where it first appears.

- [ ] **Step 1: Write failing toy-rule tests** in `tests/test_engine_meta.py`. Toy rules operate on single-term states such as `Term.from_upadesha(TermKind.ROOT, "aba")`. Seed `sutras.toml` with toy ids `"9.9.1"`…`"9.9.9"`, each under a `[toy]` comment (texts `"toy"`). The tests:
    - `test_blocking_special_beats_general`: rule `9.9.2` (a→i anywhere) is blocked by `9.9.3` (a→u word-initially, `blocks=("9.9.2",)`). Result `"ubi"`; the losers in step 1 include `Loser("9.9.2", "blocked by 9.9.3")`.
    - `test_collective_blocking`: `9.9.4` with `blocks=("9.9.2", "9.9.5")` beats both at an overlapping site.
    - `test_nisedha_keeps_blocking`: a no-op rule `9.9.6` blocks `9.9.2` at a site. After it has applied once, `9.9.2` still never applies there.
    - `test_nitya_preference`: X deletes the final vowel, Y changes the second-to-last consonant (still applicable after X), X stays applicable after Y. The test asserts the order chosen and the reason string `"deferred: 9.9.x is nitya"`.
    - `test_commuting_tie_lowest_id` and `test_noncommuting_tie_raises` (`UnresolvedConflict` names both ids).
    - `test_tripadi_one_pass`: a later tripādī rule feeds an earlier one, and the earlier one does not reapply.
    - `test_step_limit`: two rules that undo each other raise `StepLimitExceeded`.
    - `test_optional_va_alternative`: a `VA` tripādī rule applies, and `alternatives` contains the form without it.
    - `test_derivation_to_json_roundtrips_types`: `json.dumps(d.to_json())` works.
- [ ] **Step 2: Run them.** `uv run pytest tests/test_engine_meta.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** `rules/base.py`, `resolver.py`, `engine.py`, `derivation.py`. Toy ids sort after every real sūtra. `in_tripadi` is false for `9.9.x` unless a test overrides it: give `Rule` an optional `section_override: str | None = None` field for tests.
- [ ] **Step 4: Run them.** Same command. Expected: PASS.
- [ ] **Step 5: Commit.** `git add -A && git commit -m "feat: rule type, local resolver, engine loop, one-pass tripādī"`

---

### Task 4: Lexicon, requests, reference fixture

**Files:**

- Create: `src/panini/lexicon.py`, `src/panini/request.py`, `scripts/make_reference.py`, `tests/data/reference_forms.json`
- Test: `tests/test_request_lexicon.py`

**Interfaces:**

- Produces:
    - **`lexicon.py`:**
        - `Root(key: str, upadesha: str, gana: str, meaning: str, pada: Literal["P", "A", "U"])`.
        - `ROOTS: dict[str, Root]`, in this order (upadeśa in SLP1, accents as in Vidyut's dhātupāṭha):

            | key  | upadesha     | meaning                  | pada |
            | ---- | ------------ | ------------------------ | ---- |
            | bhū  | `BU`         | to be, become            | P    |
            | paṭh | `paWa~`      | to speak clearly, recite | P    |
            | gam  | `ga\mx~`     | to go                    | P    |
            | smṛ  | `smf\`       | to remember              | P    |
            | edh  | `eDa~\`      | to grow, prosper         | A    |
            | nī   | `RI\Y`       | to lead                  | U    |
            | pac  | `qupa\ca~^z` | to cook                  | U    |

            All are in gana "bhvādi".

        - `lookup_root(text: str) -> Root`. It NFC-normalizes, strips whitespace and a trailing `-`, and accepts the key or the IAST upadeśa. Otherwise it raises `UnknownRoot(text, available=tuple(ROOTS))`.

    - **`request.py`:**
        - `Lakara(Enum) LAT, LAN`, with `.iast` returning `"laṭ"`/`"laṅ"`.
        - `Purusha(Enum) PRATHAMA, MADHYAMA, UTTAMA`; `Vacana(Enum) EKA, DVI, BAHU`; `Voice(Enum) ACTIVE, MIDDLE`.
        - `Request(root: Root, lakara, purusha, vacana, voice)`, frozen, with these members:
            - `.intent() -> Intent`. Present → PRESENT, laṅ → PAST_NOT_TODAY. Prathama → NONE, madhyama → ADDRESSEE, uttama → SPEAKER. `fruit_to_agent = voice is MIDDLE`.
            - `.key -> str`: `"paṭh|laṭ|P|3|sg"`, where the pada letter is P for ACTIVE and Ā for MIDDLE.
            - `.describe() -> tuple[str, str]`: Pāṇinian, PIE. E.g. `("laṭ · prathama puruṣa ekavacana · parasmaipada", "3sg present imperfective active")`.
        - `parse_request(root: str, tense: str, person: str | int, number: str, voice: str = "active") -> Request` accepts:
            - tense: `laṭ|lat|present|present imperfective` and `laṅ|lan|imperfect|past|past imperfective`;
            - person: `3|prathama`, `2|madhyama`, `1|uttama`;
            - number: `sg|eka|ekavacana`, `du|dvi|dvivacana`, `pl|bahu|bahuvacana`;
            - voice: `active|parasmaipada|P`, `middle|ātmanepada|atmanepada|A|Ā`.

            Anything else raises `ValueError` with the accepted spellings.

        - `availability(req: Request) -> tuple[str, str] | None` returns `(reason, rule_id)` or None. Cases: P root + middle → `("paṭh takes parasmaipada only", "1.3.78")`. A root + active → `("edh takes ātmanepada only: its marker vowel is anudātta", "1.3.12")`.
        - `all_requests() -> list[Request]`: every root × lakāra × voice × person × number (7 × 2 × 2 × 3 × 3 = 252), unavailable ones included.

- [ ] **Step 1: Generate the fixture.** Write `scripts/make_reference.py`. It downloads Vidyut data into `build/vidyut-data` if absent, and derives every available request with `Vyakarana().derive(Pada.Tinanta(dhatu=Dhatu.mula(aupadeshika=…, gana=Gana.Bhvadi), prayoga=Prayoga.Kartari, lakara=…, purusha=…, vacana=…, dhatu_pada=…))`. It writes `{key: [IAST forms…]}` sorted, with no entries for unavailable cells. Run `uv run --group dev scripts/make_reference.py`. Expected: 162 keys. Spot-check:
    - `"bhū|laṅ|P|3|sg": ["abhavat", "abhavad"]`
    - `"edh|laṭ|Ā|2|pl": ["edhadhve"]`
    - `"gam|laṭ|P|3|sg": ["gacchati"]`
    - `"edh|laṅ|Ā|1|pl": ["aidhāmahi"]`
    - `"pac|laṅ|Ā|3|pl": ["apacanta"]`
- [ ] **Step 2: Write failing tests**

```python
# tests/test_request_lexicon.py
import json, unicodedata, pytest
from pathlib import Path
from panini.lexicon import lookup_root, UnknownRoot, ROOTS
from panini.request import parse_request, availability, all_requests, Purusha

def test_lookup_variants():
    assert lookup_root("paṭh").key == "paṭh"
    assert lookup_root(unicodedata.normalize("NFD", "paṭh-")).key == "paṭh"
    assert lookup_root("paṭha~").key == "paṭh"
    with pytest.raises(UnknownRoot) as e:
        lookup_root("kṛ")
    assert "bhū" in e.value.available

def test_parse_both_vocabularies():
    a = parse_request("paṭh", "present imperfective", 3, "sg", "active")
    b = parse_request("paṭh", "laṭ", "prathama", "ekavacana", "parasmaipada")
    assert a == b and a.key == "paṭh|laṭ|P|3|sg"
    assert a.describe()[1] == "3sg present imperfective active"

def test_availability():
    assert availability(parse_request("paṭh", "laṭ", 3, "sg", "middle"))[1] == "1.3.78"
    assert availability(parse_request("edh", "laṭ", 3, "sg", "active"))[1] == "1.3.12"
    assert availability(parse_request("nī", "laṭ", 3, "sg", "middle")) is None

def test_reference_fixture_matches_available_requests():
    ref = json.loads(Path("tests/data/reference_forms.json").read_text())
    avail = [r.key for r in all_requests() if availability(r) is None]
    assert sorted(avail) == sorted(ref) and len(ref) == 162
```

- [ ] **Step 3: Run them.** `uv run pytest tests/test_request_lexicon.py -v`. Expected: FAIL.
- [ ] **Step 4: Implement** `lexicon.py` and `request.py`.
- [ ] **Step 5: Run them.** Expected: PASS.
- [ ] **Step 6: Commit.** `git add -A && git commit -m "feat: lexicon, request vocabulary, Vidyut reference fixture"`

---

### Task 5: First derivation end to end (paṭhati)

**Files:**

- Create: `src/panini/rules/it.py`, `src/panini/rules/tin.py`
- Modify: `src/panini/rules/__init__.py` (`ALL_RULES` = concatenation of each module's `RULES`), `src/panini/engine.py` (add `derive`), `src/panini/data/sutras.toml`
- Test: `tests/test_rules_core.py`

**Interfaces:**

- Consumes: Tasks 2–4.
- Produces: `derive(req: Request, *, resolver: Resolver | None = None, rules: Sequence[Rule] | None = None, disabled: frozenset[str] = frozenset(), reference: Mapping[str, list[str]] | None = None) -> Derivation`; `load_reference(path: Path = Path("tests/data/reference_forms.json")) -> dict[str, list[str]]` (in `request.py`; returns `{}` if the file is absent). Its behaviour:
    - If `availability` returns a reason, give `UNAVAILABLE` with the reason as the message.
    - Otherwise the initial state is `(Term.from_upadesha(ROOT, root.upadesha),)` with `req.intent()`.
    - `UnresolvedConflict`, `StepLimitExceeded` and `OptionalRuleNotSupported` become `ERROR` with the exception message.
    - `reference` is `tuple(reference[req.key])` when a mapping is given and has the key, else None.
    - `request` in the record is `{"key", "root", "panini", "pie"}`.
    - `get_rule(id) -> Rule`.

**Rules for this task.** Each gets a `sutras.toml` entry with an IAST text and a plain-English gloss, anuvṛtti filled in.

| id             | effect                                                                                 | notes                                                                                                                             |
| -------------- | -------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| 1.3.1          | tag root term `dhātu`                                                                  |                                                                                                                                   |
| 1.3.2          | mark nasal vowels in an upadeśa as it                                                  | runs on any term with unmarked nasal vowels                                                                                       |
| 1.3.3          | mark final consonant of an upadeśa                                                     | `blocks` nothing; is blocked by 1.3.4                                                                                             |
| 1.3.4          | niṣedha: final t/th/d/dh, n, s, m of a vibhakti (tiṅ) is not it                        | no-op rewrite (tag), `blocks=("1.3.3",)`                                                                                          |
| 1.3.5          | initial ñi/ṭu/ḍu of a root is it                                                       | pac                                                                                                                               |
| 1.3.7          | initial cu/ṭu of a pratyaya is it                                                      | **find excludes the jh of jhi/jha** with a note; see amendment A3                                                                 |
| 1.3.8          | initial l/ś/ku of a non-taddhita pratyaya is it                                        | śap                                                                                                                               |
| 1.3.9          | delete all it sounds                                                                   |                                                                                                                                   |
| 6.1.64, 6.1.65 | root-initial ṣ→s, ṇ→n                                                                  | nī                                                                                                                                |
| 3.2.123        | add `la~w` (LA) after the dhātu if intent time PRESENT                                 | note: "present time → laṭ"                                                                                                        |
| 3.2.111        | add `la~N` if PAST_NOT_TODAY                                                           | note mentions "past not of today"                                                                                                 |
| 1.3.12         | tag l `ātmanepada` if root `anudattet` or ṅit                                          | `blocks=("1.3.78",)`                                                                                                              |
| 1.3.72         | tag l `ātmanepada` if root `svaritet` or ñit, and `fruit_to_agent`                     | `blocks=("1.3.78",)`                                                                                                              |
| 1.3.78         | tag l `parasmaipada`                                                                   |                                                                                                                                   |
| 3.4.78         | replace l by the tiṅ chosen from pada tag, coreference, number (via `substitute_term`) | note cites 1.4.99/100, 1.4.101 + 1.4.105–108, 1.4.102 + 1.4.22 as the selection; those ids go in `sutras.toml` (cited, not rules) |
| 3.4.113        | tag tiṅ and śit pratyayas `sārvadhātuka`                                               |                                                                                                                                   |
| 3.1.68         | insert `Sap` (VIKARANA) between dhātu and a sārvadhātuka tiṅ (kartari)                 |                                                                                                                                   |
| 1.2.4          | tag apit sārvadhātuka `ṅit-vat`                                                        |                                                                                                                                   |
| 1.4.13         | tag the term before a pratyaya `aṅga` (`assigns="aṅga"`)                               |                                                                                                                                   |
| 1.4.14         | tag the word `pada` once a tiṅ is final                                                | `assigns="pada"`                                                                                                                  |

- [ ] **Step 1: Write failing tests**

```python
# tests/test_rules_core.py
from panini.engine import derive
from panini.derivation import Status
from panini.request import parse_request

def ids(d): return [i for s in d.steps for i in s.rule_ids]

def test_pathati():
    d = derive(parse_request("paṭh", "laṭ", 3, "sg", "active"))
    assert d.status is Status.OK and d.result == "paṭhati"
    assert set(ids(d)) >= {"1.3.1","1.3.2","1.3.9","3.2.123","1.3.3","1.3.78","3.4.78","3.4.113","3.1.68","1.3.8","1.4.13","1.4.14"}
    order = ids(d)
    for a, b in [("3.2.123","3.4.78"), ("3.4.78","3.1.68"), ("3.4.113","3.1.68")]:
        assert order.index(a) < order.index(b)

def test_markers_capitalized_once_marked():
    d = derive(parse_request("paṭh", "laṭ", 3, "sg", "active"))
    rendered = [" + ".join(tv.iast() for tv in s.after) for s in d.steps]
    assert "paṭhA~" in rendered[1]           # after 1.3.2
    assert any("tiP" in r for r in rendered)

def test_tin_selection_note_cites_category_rules():
    d = derive(parse_request("paṭh", "laṭ", 3, "sg", "active"))
    note = next(s.note for s in d.steps if "3.4.78" in s.rule_ids)
    assert "1.4.108" in note and "1.4.22" in note and "1.3.78" in note

def test_unavailable():
    d = derive(parse_request("edh", "laṭ", 3, "sg", "active"))
    assert d.status is Status.UNAVAILABLE and "1.3.12" in d.message
```

- [ ] **Step 2: Run them.** `uv run pytest tests/test_rules_core.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** the rules and `derive`. Find helpers that several rules share (e.g. `anga_span(state, pratyaya_index) -> range`, `upadesha_terms(state)`) live in `rules/base.py`.
- [ ] **Step 4: Run** the whole suite: `uv run pytest -v`. Expected: PASS. If `UnresolvedConflict` is raised, read its outcomes. Fix a genuinely missing `blocks` entry, or record a finding and ask. Never reorder.
- [ ] **Step 5: Commit.** `git add -A && git commit -m "feat: it-rules, lakāra, pada, tiṅ, śap — paṭhati derives"`

---

### Task 6: Aṅga operations and vowel sandhi (main body)

**Files:**

- Create: `src/panini/rules/anga.py`, `src/panini/rules/sandhi.py`
- Modify: `rules/__init__.py`, `data/sutras.toml`
- Test: `tests/test_rules_anga_sandhi.py`

**Rules:**

| id      | effect                                                                                                                                            | blocks / flags                                                                                                                                                           |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 7.3.84  | ik-final aṅga + sārvadhātuka/ārdhadhātuka → guṇa of the final (uses `sounds.guna`, so 1.1.51 rapara is automatic; cite 1.1.51 in the note when ṛ) |                                                                                                                                                                          |
| 7.3.86  | guṇa of a light ik upadhā                                                                                                                         | `near_miss`: if the aṅga upadhā is a light non-ik vowel before sārvadhātuka: "7.3.86 (guṇa of a light penultimate vowel) does not apply: {v} is not an ik vowel (1.1.3)" |
| 7.3.101 | a-final aṅga → ā before a yañ-initial sārvadhātuka                                                                                                |                                                                                                                                                                          |
| 7.1.3   | jh of a pratyaya → ant                                                                                                                            |                                                                                                                                                                          |
| 7.3.77  | final of iṣ/gam/yam → ch before śit                                                                                                               |                                                                                                                                                                          |
| 6.1.73  | tuk after a short vowel before ch (`augment_in_term_edit`)                                                                                        | `tuk_or_satva=True`                                                                                                                                                      |
| 6.1.78  | e/o/ai/au + vowel → ay/av/āy/āv                                                                                                                   |                                                                                                                                                                          |
| 6.1.87  | a/ā + vowel → guṇa (Ekadesha)                                                                                                                     |                                                                                                                                                                          |
| 6.1.88  | a/ā + ec → vṛddhi                                                                                                                                 | `blocks=("6.1.87",)`                                                                                                                                                     |
| 6.1.97  | non-final short a + guṇa vowel → the latter (pararūpa)                                                                                            | `blocks=("6.1.87","6.1.101")`, Kiparsky's collective blocking                                                                                                            |
| 6.1.101 | aK + savarṇa → long                                                                                                                               | `blocks=("6.1.87",)`                                                                                                                                                     |

- [ ] **Step 1: Write failing tests.** These are main-body-only forms that need no tripādī rule. Disable nothing, since the tripādī doesn't exist yet. Use `ids` from Task 5.

```python
# tests/test_rules_anga_sandhi.py
import pytest
from panini.engine import derive
from panini.request import parse_request

@pytest.mark.parametrize("root,person,number,expected", [
    ("bhū", 3, "sg", "bhavati"), ("bhū", 3, "pl", "bhavanti"), ("bhū", 1, "sg", "bhavāmi"),
    ("smṛ", 3, "sg", "smarati"), ("nī", 3, "sg", "nayati"), ("pac", 3, "sg", "pacati"),
])
def test_lat_active_vowel_final_forms(root, person, number, expected):
    assert derive(parse_request(root, "laṭ", person, number, "active")).result == expected

def test_gam_before_tripadi():
    assert derive(parse_request("gam", "laṭ", 3, "sg", "active")).result == "gatchati"

def test_bhavanti_shows_collective_blocking():
    d = derive(parse_request("bhū", "laṭ", 3, "pl", "active"))
    step = next(s for s in d.steps if "6.1.97" in s.rule_ids)
    assert {l.rule_id for l in step.losers} >= {"6.1.101", "6.1.87"}

def test_pathati_near_miss():
    d = derive(parse_request("paṭh", "laṭ", 3, "sg", "active"))
    assert any("7.3.86" in n and "not an ik vowel" in n for s in d.steps for n in s.near_misses)

def test_smarati_cites_rapara():
    d = derive(parse_request("smṛ", "laṭ", 3, "sg", "active"))
    assert "1.1.51" in next(s.note for s in d.steps if "7.3.84" in s.rule_ids)
```

- [ ] **Step 2: Run them.** `uv run pytest tests/test_rules_anga_sandhi.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** the rules.
- [ ] **Step 4: Run** `uv run pytest -v`. Expected: PASS (same conflict policy as Task 5).
- [ ] **Step 5: Commit.** `git add -A && git commit -m "feat: guṇa, aṅga changes, vowel sandhi with collective blocking"`

---

### Task 7: Tripādī rules: laṭ active paradigms complete

**Files:**

- Create: `src/panini/rules/tripadi.py`
- Modify: `rules/__init__.py`, `data/sutras.toml`
- Test: `tests/test_paradigms.py` (a shared harness, extended in Tasks 8–9)

**Rules** (all `in_tripadi`; the engine applies them in sūtra order):

| id     | effect                                                           | flags                        |
| ------ | ---------------------------------------------------------------- | ---------------------------- |
| 8.2.23 | delete the final consonant of a word-final cluster               |                              |
| 8.2.39 | word-final jhal → jaś (t→d)                                      |                              |
| 8.2.66 | word-final s → `ru~` (via `ReplaceSounds` with a fresh `r`,`u~`) | `reintroduces_upadesha=True` |
| 8.3.15 | word-final r → visarga `H`                                       |                              |
| 8.3.24 | non-final n/m before jhal → anusvāra                             |                              |
| 8.4.40 | s/tu-class before or after ś/cu-class → ś/cu-class               | gatch → gacch                |
| 8.4.56 | final jhal at pause → car (d→t)                                  | `optional=Optionality.VA`    |
| 8.4.58 | anusvāra before yay → savarṇa of the following                   |                              |

- [ ] **Step 1: Write the failing paradigm harness**

```python
# tests/test_paradigms.py
import json, pytest
from pathlib import Path
from panini.engine import derive
from panini.derivation import Status
from panini.request import all_requests, availability

REF = json.loads(Path("tests/data/reference_forms.json").read_text())
XFAIL: dict[str, str] = {}   # key -> explanation (mirrors docs/findings.md)
IN_SCOPE = lambda r: r.lakara.iast == "laṭ" and r.voice.name == "ACTIVE"   # widened in Tasks 8 and 9

CASES = [r for r in all_requests() if availability(r) is None and IN_SCOPE(r)]

@pytest.mark.parametrize("req", CASES, ids=lambda r: r.key)
def test_form_matches_reference(req):
    if req.key in XFAIL:
        pytest.xfail(XFAIL[req.key])
    d = derive(req)
    assert d.status is Status.OK, d.message
    assert [d.result, *d.alternatives] == REF[req.key]
```

- [ ] **Step 2: Run it.** `uv run pytest tests/test_paradigms.py -v`. Expected: the forms needing tripādī FAIL (e.g. `bhavataḥ`, `gacchati`).
- [ ] **Step 3: Implement** the rules, and the `ru~` it-processing check of Task 3 against the real 1.3.2/1.3.9.
- [ ] **Step 4: Run** `uv run pytest -v`. Expected: all 54 laṭ-active forms PASS (6 P/U roots × 9).
- [ ] **Step 5: Commit.** `git add -A && git commit -m "feat: tripādī rules; laṭ parasmaipada paradigms pass"`

---

### Task 8: Ātmanepada endings: laṭ middle paradigms

**Files:**

- Create: `src/panini/rules/endings.py` (the ātmanepada part)
- Modify: `rules/sandhi.py` (6.1.66), `rules/anga.py` (7.2.81), `data/sutras.toml`, `tests/test_paradigms.py`

**Rules:**

| id     | effect                                                                          |
| ------ | ------------------------------------------------------------------------------- |
| 3.4.79 | in a ṭit lakāra, the ṭi (last vowel onward, 1.1.64) of an ātmanepada ending → e |
| 3.4.80 | in a ṭit lakāra, thās → se (`blocks=("3.4.79",)`)                               |
| 7.2.81 | ā of a ṅit (incl. ṅit-vat, sthānivat) ending after an a-final aṅga → iy         |
| 6.1.66 | y/v before a val consonant is deleted                                           |

- [ ] **Step 1: Widen the test scope.** Make `IN_SCOPE` cover laṭ in both voices. Add a golden to `tests/test_paradigms.py`:

```python
def test_edhete_order():
    from panini.request import parse_request
    o = [i for s in derive(parse_request("edh", "laṭ", 3, "du", "middle")).steps for i in s.rule_ids]
    for a, b in [("3.4.79", "7.2.81"), ("7.2.81", "6.1.66"), ("6.1.66", "6.1.87")]:
        assert o.index(a) < o.index(b)
```

- [ ] **Step 2: Run it.** `uv run pytest tests/test_paradigms.py -v`. Expected: the Ā forms FAIL.
- [ ] **Step 3: Implement** the rules.
- [ ] **Step 4: Run** `uv run pytest -v`. Expected: all 81 laṭ forms PASS (54 + 27 Ā: edh, nī, pac). Anything else goes through the failure policy into `XFAIL` plus `docs/findings.md`.
- [ ] **Step 5: Commit.** `git add -A && git commit -m "feat: ātmanepada endings; laṭ middle paradigms pass"`

---

### Task 9: Laṅ: all 162 forms, goldens, findings

**Files:**

- Modify: `rules/endings.py`, `rules/sandhi.py` (6.1.90), `data/sutras.toml`, `tests/test_paradigms.py`
- Create: `tests/test_goldens.py`, `docs/findings.md`

**Rules:**

| id      | effect                                                       | notes                                                                                    |
| ------- | ------------------------------------------------------------ | ---------------------------------------------------------------------------------------- |
| 6.4.71  | aṭ (ṭit augment) before an aṅga in laṅ (`augment_edit`)      | `in_abhiya`                                                                              |
| 6.4.72  | āṭ before a vowel-initial aṅga                               | `blocks=("6.4.71",)`, `in_abhiya`                                                        |
| 6.1.90  | āṭ + vowel → vṛddhi                                          | `blocks=("6.1.87","6.1.88")`                                                             |
| 3.4.99  | in a ṅit lakāra, final s of an uttama ending is deleted      | relies on 1.1.56 (the ending `has_marker("N")`); the step note includes `sthanivat_note` |
| 3.4.100 | in a ṅit lakāra, final i of a parasmaipada ending is deleted | same                                                                                     |
| 3.4.101 | in a ṅit lakāra, tas/thas/tha/mip → tām/tam/ta/am            | same                                                                                     |

- [ ] **Step 1: Widen the test scope.** Make `IN_SCOPE` always true (162 cases). Write `tests/test_goldens.py`. Each golden asserts a subset of rule ids and pairwise orders, taken from the traditional derivation (Vidyut's order is the stand-in):
    - `bhavanti`: ids ⊇ {7.1.3, 7.3.84, 6.1.78, 6.1.97, 8.3.24, 8.4.58}; order 7.3.84<6.1.78, 7.1.3<6.1.97, 8.3.24<8.4.58.
    - `gacchati`: 7.3.77<6.1.73<8.4.40.
    - `aidhata`: ids ⊇ {3.2.111, 6.4.72, 6.1.90}; 6.4.72<6.1.90; no 3.4.79.
    - `abhavam`: 3.4.101<6.1.97; 6.4.71 present; the 3.4.101 step note contains `"1.1.56"`.
    - `abhavat`: the 8.4.56 step has `alternatives == ("abhavad",)`, and `d.alternatives == ("abhavad",)`.
    - `abhavan`: 3.4.100<7.1.3; 8.2.23 present.
    - `bhavāmaḥ` (laṭ): 8.2.66 is followed directly by a 1.3.2 step and then 8.3.15 (amendment A2).
- [ ] **Step 2: Run them.** `uv run pytest tests/test_paradigms.py tests/test_goldens.py -v`. Expected: the laṅ forms FAIL.
- [ ] **Step 3: Implement** the rules.
- [ ] **Step 4: Run** `uv run pytest -v`. Expected: 162 paradigm cases pass or are xfail with explanations, and the goldens pass.
- [ ] **Step 5: Write `docs/findings.md`.** Sections:
    - _Expected failures_ (mirror `XFAIL`, one paragraph each).
    - _Kiparsky vs. tradition_: every golden where the resolver's non-commuting order differs from Vidyut's. Find them by running the comparison script inline in the test session and noting the cases.
    - _Engine exceptions_: A2 (ru~ it-processing) and A3 (the 1.3.7 jh exclusion), with their justification.
    - _Known limitations_: no 8.4.46–47 doubling; no 8.4.68 (closed ă, invisible in IAST); 6.4.22 detection only; 1.1.47 not implemented.
- [ ] **Step 6: Commit.** `git add -A && git commit -m "feat: laṅ; all slice-1 paradigms; goldens and findings"`

---

### Task 10: Text trace, CLI, README

**Files:**

- Create: `src/panini/trace.py`, `src/panini/cli.py`, `README.md`
- Test: `tests/test_trace_cli.py`

**Interfaces:**

- Consumes: `derive`, `parse_request`, `lookup_root`, `UnknownRoot`.
- Produces:
    - `render_text(d: Derivation, verbosity: int = 0) -> str`. The format is spec "Target shape of the default output":
        - a header line `"{root}-, {panini}  →  {result}"`;
        - numbered steps: form after, then sūtra id, then text, with the gloss/note on the next line;
        - `↳` lines for near-misses;
        - at `verbosity >= 1`, losers as `"   ✗ {id}: {reason}"`; at `>= 2`, also every rule checked.
        - Consecutive `1.3.x` it-steps on the same term may merge into one line listing both ids.
    - `main(argv: list[str] | None = None) -> int` (argparse) with subcommands:
        - `derive ROOT TENSE PERSON NUMBER [VOICE] [-v|-vv]`;
        - `site [--out PATH] [--open]` (wired in Task 11).

        Errors (`UnknownRoot`, `ValueError` from parsing) print one line to stderr and return 2.

- [ ] **Step 1: Write failing tests**

```python
# tests/test_trace_cli.py
from panini.cli import main
from panini.engine import derive
from panini.request import parse_request
from panini.trace import render_text

def test_render_default_and_verbose():
    d = derive(parse_request("bhū", "laṭ", 3, "pl", "active"))
    out = render_text(d)
    assert out.splitlines()[0].endswith("→  bhavanti") and "6.1.97" in out and "✗" not in out
    assert "✗ 6.1.101" in render_text(d, verbosity=1)

def test_cli_derive(capsys):
    assert main(["derive", "paṭh", "present", "3", "sg"]) == 0
    assert "paṭhati" in capsys.readouterr().out

def test_cli_unknown_root(capsys):
    assert main(["derive", "kṛ", "laṭ", "3", "sg"]) == 2
    err = capsys.readouterr().err
    assert "kṛ" in err and "bhū" in err and "Traceback" not in err
```

- [ ] **Step 2: Run them.** `uv run pytest tests/test_trace_cli.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** `trace.py` and `cli.py`. Write a short `README.md` covering what the tool is, `uv run panini site --open`, `uv run panini derive …`, and a link to `docs/findings.md` for limitations.
- [ ] **Step 4: Run** `uv run pytest -v` and `uv run panini derive gam laṭ 3 sg -v`. Expected: tests PASS, and the trace reads correctly by eye.
- [ ] **Step 5: Commit.** `git add -A && git commit -m "feat: text trace and CLI"`

---

### Task 11: HTML explorer (`panini site`)

**Files:**

- Create: `src/panini/site/__init__.py`, `src/panini/site/build.py`, `src/panini/site/template.html`, `src/panini/site/app.js`, `src/panini/site/style.css`
- Modify: `src/panini/cli.py` (wire `site`), `pyproject.toml` (include `site/*` and `data/*` as package data, if uv_build needs it)
- Test: `tests/test_site.py`

**Interfaces:**

- Consumes: `all_requests`, `derive`, `Derivation.to_json`, `ROOTS`.
- Produces:
    - `site_data() -> dict`, shaped `{"roots": [{key, upadesha_iast, meaning, gana, pada}], "derivations": {request_key: Derivation.to_json()}}`. It contains all 252 requests, unavailable ones included. Derivations run with `reference=load_reference()`. A derivation that raises unexpectedly is caught and stored as `ERROR` with the message.
    - `build_site(out: Path, style_dir: Path | None = None) -> Path`. It writes one HTML file containing:
        - the template;
        - `style.css` inlined;
        - the `@font-face` CSS from `uv run --no-project <fonts_dir>/../../scripts/font_faces.py --embed --faces body,sans,caps,mono`, run as a subprocess;
        - the data as `<script type="application/json" id="data">`;
        - `app.js` inlined.

        `style_dir` (the style skill's root, which holds `scripts/font_faces.py` and `assets/`) defaults to `$PANINI_STYLE_DIR`, else `~/.local/state/claude/skills/krish-frontend-style` (amendment A5). If it's missing, or the script fails, print a warning to stderr and omit the font CSS.

**Page behaviour** (spec "GUI"). Load the `krish-frontend-style` skill before writing CSS. The layout follows the spec sketch.

- **Header:** eyebrow "PĀṆINI", title "Prakriyā explorer", and the `◐` glass theme toggle, with the blocking theme script in `<head>` and storage access wrapped in try/catch.
- **Root picker:** a `<select>` labelled "Root".
- **Tables:** a 2×2 grid of 3×3 tables. Rows are present/past imperfective with laṭ/laṅ; columns are active/middle with parasmaipada/ātmanepada. Inside each table, rows are 3/2/1 (prathama/madhyama/uttama) and columns are sg/du/pl.
    - An unavailable table is greyed with `"{reason} ({rule})"`.
    - A cell with `ERROR`/`EXPECTED_FAILURE`, or whose result is not in `reference`, is marked oxblood (`--neg`) and shows the reference form too.
    - Alternatives show small after the main form (e.g. "abhavat · abhavad").
- **Derivation panel** below the tables:
    - the form, both descriptions, then an ordered list of steps;
    - each step shows the after-form (markers as `<span class="it">` capitals in `--accent`, term boundaries `+`), the sūtra id in Monaspace, the sūtra text, and the gloss/note;
    - near-misses render as `↳` lines;
    - losers go in `<details><summary>competitors</summary>`;
    - warnings render as a muted note.
- **URL hash** `#root/laṭ|laṅ/P|Ā/3|2|1/sg|du|pl`. Write `parseHash(hash, data) -> {root, key|null}` as a pure function in `app.js`. Invalid input falls back to the first root and no selection.
- No network requests. It must work from `file://`.

- [ ] **Step 1: Write failing tests**

```python
# tests/test_site.py
import json, re
from pathlib import Path
from panini.site.build import build_site, site_data
from panini.derivation import Status

def test_site_data_covers_everything():
    d = site_data()
    assert len(d["roots"]) == 7 and len(d["derivations"]) == 252
    assert d["derivations"]["edh|laṭ|P|3|sg"]["status"] == "unavailable"

def test_build_without_fonts(tmp_path, capsys):
    out = build_site(tmp_path / "p.html", style_dir=tmp_path / "nope")
    html = out.read_text()
    assert "warning" in capsys.readouterr().err.lower()
    data = json.loads(re.search(r'<script type="application/json" id="data">(.*?)</script>', html, re.S).group(1))
    assert data["derivations"]["paṭh|laṭ|P|3|sg"]["result"] == "paṭhati"
    assert "http://" not in html and "https://" not in html

def test_one_failing_derivation_does_not_abort(monkeypatch, tmp_path):
    import panini.site.build as b
    real = b.derive
    def flaky(req, **kw):
        if req.key == "gam|laṭ|P|3|sg":
            raise RuntimeError("boom")
        return real(req, **kw)
    monkeypatch.setattr(b, "derive", flaky)
    assert site_data()["derivations"]["gam|laṭ|P|3|sg"]["status"] == "error"
```

- [ ] **Step 2: Run them.** `uv run pytest tests/test_site.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** `build.py`, the template, the CSS (trimmed `base.css` plus page styles) and `app.js`. Wire `panini site` in `cli.py`; `--open` uses `webbrowser.open(out.as_uri())`.
- [ ] **Step 4: Run** `uv run pytest -v`. Expected: PASS.
- [ ] **Step 5: Check by eye.** Run `uv run panini site --open`. In light and dark themes, check:
    - paṭh: middle tables greyed with 1.3.78;
    - click paṭhati: the steps show `paṭhA~`, then `tiP`, and the 7.3.86 near-miss;
    - bhavanti: competitors list 6.1.101 and 6.1.87;
    - abhavat shows "· abhavad";
    - load with `#xyz/laṭ/P/9/sg`: falls back without console errors;
    - phone width (≤ 480px): tables stack.

    Run through the style skill's checklist (faces, numerals, warm colours, texture subtle, glass has colour behind it). Fix anything off.

- [ ] **Step 6: Commit.** `git add -A && git commit -m "feat: static HTML explorer"`

---

## Self-review notes

- **Spec coverage:**
    - intent/goals (Tasks 5–11); non-goals respected (no accent, other gaṇas or anuvṛtti parsing);
    - anti-goals (failure policy in Global Constraints, `UnresolvedConflict` in Task 3, verbosity levels in Tasks 10–11);
    - representation (Task 2); rules (Task 3); resolver (Task 3); tiṅ choice (Task 5); sthānivat/augments (Tasks 2 and 9);
    - tripādī (Tasks 3 and 7); asiddha domains (Task 3); request vocabulary (Task 4); display (Tasks 3, 5, 10, 11);
    - data format (Task 3); GUI (Task 11); CLI (Task 10); lexicon (Task 4); testing (Tasks 4, 7–9, 11).
    - Slice-2 preservation: pure rules, `apply_simultaneous`, the `Resolver` protocol, and room for alternatives in `StepRecord`.
- **Proportion:** this plan gives signatures, rule tables and tests, not rule bodies. Each rule body is a few lines of `find`/`rewrite`, written by the implementer from the table row and the sūtra.
