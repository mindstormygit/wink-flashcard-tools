# WinkNotes Flashcard Tools

[简体中文](README.zh-CN.md)

Open Skills, format references, builders, validators, and examples for generating importable `.wink` standalone flashcards or flashcard packs for WinkNotes.

This repository contains the complete source of two independent AI-agent Skills:

| Skill | Generates | Highlights |
| --- | --- | --- |
| [`generate-twinkling-pack`](skills/generate-twinkling-pack/) | Standalone front/back note or choice cards, or mixed packs | Rich text, hierarchical tags, inline images, and native rectangular image occlusion on note cards |
| [`generate-twinkling-word-pack`](skills/generate-twinkling-word-pack/) | Standalone native vocabulary cards or vocabulary packs | English, Japanese, Korean, German, French, Spanish, Portuguese, and Italian; pronunciation, Chinese definitions, examples, language-specific fields, and tags |

Both Skills generate unencrypted `.wink` files locally with Python 3 and validate every completed artifact before delivery. Explicit standalone-card or pack requests take priority. When the product is unspecified, one final card becomes a standalone card and two or more become a pack. The WinkNotes source code is not part of this repository.

## Quick start

1. Download a Skill archive from [Releases](https://github.com/mindstormygit/wink-flashcard-tools/releases), or clone this repository.
2. Install the complete Skill directory in the Skills location used by your AI tool. Do not copy only `SKILL.md`.
3. Start a new task so the tool can discover the Skill.
4. Attach your source material and use one of the prompts below.

Codex default locations:

```text
~/.codex/skills/generate-twinkling-pack/
~/.codex/skills/generate-twinkling-word-pack/
```

Other AI tools may use a different location. Follow the tool's own Skill installation instructions.

### Notes and choice cards

```text
Use $generate-twinkling-pack to turn this PDF into 30 note cards,
10 single-answer questions, and 5 multiple-answer questions.
Create tags from the document outline, keep each card atomic,
add a short explanation to every choice question,
then build and validate the .wink pack.
```

### Word cards

```text
Use $generate-twinkling-word-pack to select about 40 useful English
words or phrases from this document. Add concise Chinese definitions,
one natural example with translation, and section-based tags,
then build and validate the .wink vocabulary pack.
```

### Standalone card

```text
Use $generate-twinkling-pack to turn the following fact into one standalone
.wink card, not a pack, then validate the file.
```

WinkNotes asks the user to choose a destination pack when importing a standalone card, so standalone cards do not contain a pack name or tag. Use a pack for multiple cards.

Generic requests such as "make flashcards from this PDF" use the final card count: one card exports as a standalone card; two or more export as a pack. Explicitly requesting a pack still creates a pack when it contains only one card.

## Image occlusion

`generate-twinkling-pack` can create native rectangular `.rimg` image occlusions on note cards. This advanced workflow requires a multimodal model that can understand the source image. Choice cards are text-only in the current version.

## WinkNotes format

Start with the [WinkNotes format index](docs/wink-format.md). Detailed serializer references live with each independently distributable Skill:

- [Note and choice pack format](skills/generate-twinkling-pack/references/wink-format.md)
- [Word pack format](skills/generate-twinkling-word-pack/references/wink-format.md)

## Build release archives

```bash
python3 scripts/package_skills.py
```

The command creates two reproducible ZIP archives in `dist/`. Git tags matching `v*` trigger the release workflow, which validates the examples and attaches both archives with checksums to a GitHub Release.

## Safety and content quality

- Packaging and validation scripts run locally.
- Source extraction, OCR, webpage access, and model inference are provided by the AI environment the user selects.
- `.wink` files are unencrypted. Do not publish packs containing private or sensitive material.
- AI-generated study content can be wrong. Verify important facts against the original source.
- Use only source material and images you are allowed to process and distribute.

## App

- [WinkNotes website](https://card.detailsoft.cn/)
- [WinkNotes on the App Store](https://apps.apple.com/cn/app/id1515687192)

## License

MIT License. See [LICENSE](LICENSE).
