# Changelog

All notable changes to Generate WinkNotes Pack are documented here.

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
