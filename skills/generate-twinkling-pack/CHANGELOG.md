# Changelog

All notable changes to Generate WinkNotes Pack are documented here.

## 2.0.0 — 2026-11-22

- Merges native `WordDocument` vocabulary card/pack authoring (`.wink`, previously in `generate-twinkling-word-pack`) into this single Skill, with clear format routing and separate `.wink` / `.winkmd` delivery when a request needs both.
- Authors dialect-v2 `.winkmd` instead of legacy document JSON for note and choice cards; ZIP includes media only when needed.
- Supports multi-card files, hierarchical categories and colors, stars, suggested pack names and new-pack fill preference.
- Adds mute for translations/notes and collapsed hints; supports ordinary images, recordings and carrying back existing `.rimg`.
- Syncs the dialect-v2 choice block additions from the App spec: optional per-question `shuffle=true/false` attribute (validated by `validate_winkmd.py`) and inline `:::explanation` blocks.
- New-card image occlusion is no longer authored. Legacy `.wink` note/choice output remains available from earlier Skill releases; the App still imports it.
- Uses small standard-library builders and validators (`build_winkmd.py` / `validate_winkmd.py` for `.winkmd` and media ZIPs; `build_word_wink.py` / `validate_word_wink.py` for `.wink` word cards/packs). Full rich-document semantics for `.winkmd` are checked by the App.
- Ships the App's dialect spec unchanged as `references/wink-spec-markdown-format.md`, copied at packaging time; `advanced-v2.md` is removed. SKILL.md keeps the workflow and points to spec sections.
- The builder writes `generator: generate-twinkling-pack <version>` into each delivered `.winkmd` header, so a later App can suggest updating an old Skill.

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
