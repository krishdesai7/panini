# panini

A Pāṇinian *prakriyā* engine: watch the Aṣṭādhyāyī derive Sanskrit verb forms
step by step. Each step cites its sūtra, explains what it did, and records which
competing rules lost and why.

The rules are declarative. A resolver decides which rule applies next:
blocking (utsarga/apavāda, including collective blocking), the narrow para
rule (1.4.2), nitya preference, and a commutation check. After that, the
tripādī runs once in sūtra order. Where the tradition is divided, the engine
follows Paul Kiparsky's analysis. The design is in
`docs/superpowers/specs/2026-11-24-prakriya-engine-design.md`.

It covers laṭ (present) and laṅ (imperfect) of the whole bhvādi class, in both
voices where the root allows them: 1,132 of the 1,156 roots (the other 24 need
present stems or suffixes the engine doesn't derive yet, or are a variant reading
the sources conjugate against the sūtra). 21,555 of 21,564 forms match the
reference (Vidyut 0.4). The 9 that don't need a rule not yet modelled (8.4.65),
documented in `docs/findings.md`.

## Use

```sh
uv run panini site --open              # build the explorer and its rule pages under build/
uv run panini serve --open             # serve every root locally, deriving one root at a time
uv run panini derive paṭh present 3 sg # one derivation in the terminal
uv run panini derive bhū laṅ 3 pl -v   # -v adds the competitors each step beat
```

Either vocabulary works: `present imperfective` or `laṭ`, `3` or `prathama`,
`sg` or `ekavacana`, `middle` or `ātmanepada`.

`site` and `serve` cache each root's derivations on disk, in `$PANINI_CACHE_DIR`
(default `.cache/panini/`), so a restarted server doesn't derive them again. The
cache is keyed by a hash of the engine's code and data, so any change to the rules
starts a fresh one. `--no-cache` bypasses it.

Choose **Rules** in the explorer to browse the catalogue, or follow a linked
sūtra in a verb trace. Worked examples link back to the exact step.
Export the [rule catalogue](docs/rule-catalog.md) as JSON with
`uv run panini rules`, or pass a sūtra number to select one article.

## Development

```sh
uv run pytest                                  # fast tests
uv run pytest -m slow                          # every form of the class against the reference
uv run --group dev scripts/make_reference.py   # regenerate the reference forms (Vidyut)
```

## Limitations

See `docs/findings.md`. Notable ones: no optional doubling (8.4.46–47), no
accent, and the 6.4.22 and 6.1.86 asiddha domains are only partly modelled.
