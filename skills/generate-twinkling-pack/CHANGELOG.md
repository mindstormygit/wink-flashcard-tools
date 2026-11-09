# Changelog

All notable changes to Generate WinkNotes Pack are documented here.

## 2.0.0 — 2026-11-09

- Authors dialect-v2 `.winkmd` instead of legacy document JSON; ZIP includes media only when needed.
- Supports multi-card files, hierarchical categories and colors, stars, suggested pack names and new-pack fill preference.
- Adds mute for translations/notes and collapsed hints; supports ordinary images, recordings and carrying back existing `.rimg`.
- New-card image occlusion is no longer authored. Legacy `.wink` output remains available from earlier Skill releases; the App still imports it.
- Uses a small standard-library builder and envelope validator; full rich-document semantics are checked by the App. The validator also rejects what the App's strict import rejects: legacy/Anki syntax, unescaped brackets after CJK text, caret superscripts, and unclosed or misordered tags.
- Examples put clozes in the sentence to complete; explanations stay read aloud, only translations and side notes are muted.
- Ships the App's dialect spec unchanged as `references/wink-spec-markdown-format.md`, copied at packaging time; `advanced-v2.md` is removed. SKILL.md keeps the workflow and points to spec sections.
- The validator also checks known tag values, and the tests read the App's shared accept/reject samples.
- The builder writes `generator: generate-twinkling-pack <version>` into each delivered header, so a later App can suggest updating an old Skill.

## 1.2.1 — 2026-07-30

- Aligns the Chinese product name with “闪卡” and the English product name with WinkNotes.

## 1.2.0 — 2026-07-30

- Adds standalone note or choice `.wink` cards as an alternative to pack output.
- Adds `--product card`, strict one-card input rules, standalone-card validation, documentation, and an example.
- Adds automatic product selection by final card count while allowing explicit `--product pack` and `--product card` overrides.

## 1.1.0 — 2026-07-24

- Adds text-only `ChoiceDocument` cards.
- Supports both single-answer and multiple-answer choices.
- Allows choice cards and `NoteLegacyDocument` cards to coexist in one pack and share hierarchical tags.
- Adds strict validation for choice blocks, option IDs, correct-answer sets, summaries, spans, and occlusion flags.
- Adds mixed-pack examples and choice-card authoring guidance.

### Current limitations

- Images and native RichImage occlusions are supported on note cards, not inside choice cards.
- Word cards, audio, video, and freehand rich-image drawings are not supported.
- Image occlusion supports rectangles only.

## 1.0.0 — 2026-07-24

- First public release.
- Generates front/back `NoteLegacyDocument` flashcards.
- Supports hierarchical tags and rich-text spans.
- Supports ordinary image attachments.
- Supports native rectangular `.rimg` image occlusions.
- Validates WinkNotes structure, versions, attachments, tag paths, and duplicate cards.
- Includes a Chinese user guide, format specification, input schema, authoring guide, and example pack.

### Limitations in 1.0.0

- Choice cards and word cards are not supported.
- Audio, video, and freehand rich-image drawings are not supported.
- Image occlusion supports rectangles only.
