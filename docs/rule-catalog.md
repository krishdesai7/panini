# Rule catalogue

The explorer can cite a sūtra as soon as its IAST text and short gloss are in
`src/panini/data/sutras.toml`. Add an entry in
`src/panini/data/rule_articles.toml` when there is enough material for an
article. The same dotted sūtra ID joins the two files and keys the exported
catalogue. Keep the full ID, including a fourth component for a vārttika.

A page can lead with the sūtra and its gloss, then show what kind of rule it is,
how to read it, a worked example, and where to read further. The export
distinguishes three sources of information:

- **Text and editorial notes.** Write the explanation in plain English and
  use `{plain term|Sanskrit term}` for a tooltip and `[[Sanskrit text]]` for
  IAST in running prose, including forms without diacritics. Cite an edition or
  commentary using a bibliography key, locator, and role (`text`, `commentary`,
  or `analysis`). Follow Kiparsky where his work addresses a question of
  interpretation, and cite the particular passage. In the explanation,
  `[@source_key]` links to the source entry. An optional citation `label`
  supplies a short label for that link. Use `related` for a
  sūtra and a short explanation of why it matters. A related sūtra needs a
  text entry and can acquire its own article later.
- **Explorer behavior.** The export pulls readings from `rules/readings.py`
  and blocking relationships from the rule registry. Write an optional
  `scope` note if the implementation covers only part of the traditional
  rule. Definitions like 1.1.1 can inform an operation without having a
  standalone entry in the rule registry.
- **Worked examples.** Record the request using a Dhātupāṭha code, tense,
  person, number, and voice. Supply `step_rule` when another sūtra performs
  the operation that illustrates the article. The exporter runs the same
  engine as the verb explorer and emits the request key, result, and selected
  step with its before and after terms. A missing or ambiguous step fails the
  export. Set a one-based `occurrence` only when the same sūtra appears
  several times and you want a specific occurrence.

Run `uv run panini rules` for the full catalogue or
`uv run panini rules 1.1.1` for one article. Both emit JSON. The explorer
uses the catalogue to render `rules/index.html` and one HTML page per
article. Worked examples link back to the verb trace at the selected step
when the root is available. In the static build, an example for a root
outside the featured set still shows its before and after forms.
