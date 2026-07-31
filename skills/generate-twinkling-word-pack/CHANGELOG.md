# Changelog

All notable changes to Generate WinkNotes Word Pack are documented here.

## 1.2.1 — 2026-07-30

- Aligns the Chinese product name with “闪卡” and the English product name with WinkNotes.

## 1.2.0 — 2026-07-30

- Adds standalone native `WordDocument` `.wink` cards as an alternative to pack output.
- Adds `--product card`, strict one-word input rules, standalone-card validation, documentation, and an example.
- Adds automatic product selection by final word count while allowing explicit `--product pack` and `--product card` overrides.

## 1.0.0 — 2026-07-24

- Generates native `WordDocument` vocabulary packs.
- Supports English, Japanese, Korean, German, French, Spanish, Portuguese, and Italian.
- Supports AI-authored pronunciation, concise Chinese definitions, examples, translations, language-specific fields, and optional hierarchical tags.
- Builds and validates unencrypted `.wink` files locally with Python 3.
- Includes a Chinese user guide, format reference, input schema, authoring guidance, and an example pack.

### Current limitations

- Each pack contains one language.
- The Skill does not include images, audio, note cards, or choice cards.
- Lexical content is authored by the selected AI and should be checked against important source material.
