# WinkNotes Flashcard Tools

[简体中文](README.zh-CN.md)

Independently installable Skills, examples, format guidance and local packaging tools for WinkNotes. The App's private source is not part of this repository.

| Skill | Output | Capabilities |
| --- | --- | --- |
| [`generate-twinkling-pack`](skills/generate-twinkling-pack/) | Multi-card `.winkmd`, or ZIP with media | Recall and choice questions, cloze, hierarchical categories, stars, collapsed hints, muted translations/notes, pictures and recordings |
| [`generate-twinkling-word-pack`](skills/generate-twinkling-word-pack/) | Legacy `.wink` word cards or packs | Native word templates, pronunciation, definitions, examples and categories; unchanged |

The new note Skill requires a WinkNotes version supporting `.winkmd` import. The App continues importing legacy `.wink`; earlier Skill releases retain the old builder. New cards use ordinary pictures. Existing `.rimg` attachments can be carried back unchanged; the new Skill does not create image occlusions.

## Install and use

Download a Skill ZIP from [Releases](https://github.com/mindstormygit/wink-flashcard-tools/releases), then unpack the complete folder into your AI tool's Skills directory. Codex defaults to `~/.codex/skills/generate-twinkling-pack/` and `~/.codex/skills/generate-twinkling-word-pack/`. Keep scripts and references, not just SKILL.md. Start a new conversation after updating for fresh discovery.

```text
Use $generate-twinkling-pack to turn this PDF into about 40 flashcards.
Use chapter-based hierarchical categories and star important cards.
Mute translations and notes, collapse hints, and deliver validated .winkmd,
or a ZIP when images or recordings are included.
```

A category array is one parent-to-child path, not several independent tags. Import lets the user choose or create a normal pack. Unclassified cards remain unclassified. A pack name only suggests a new name; existing names, category colors and study preferences are preserved.

```text
Use $generate-twinkling-word-pack to select 40 useful words from this source,
write source-grounded definitions and examples, and deliver a validated .wink word pack.
```

Open plain `.winkmd` in WinkNotes from Files. Select ordinary ZIPs through WinkNotes' in-app file import. See the [note Skill](skills/generate-twinkling-pack/SKILL.md) for the workflow and the [dialect spec](skills/generate-twinkling-pack/references/wink-spec-markdown-format.md) for syntax. The spec is copied from the WinkNotes App repository when packaging; edit it there, not here. Python helpers use only the standard library; they check delivery envelopes, attachments and the App's strict v2 rejections, while the App validates full dialect semantics.

## Check and package

```bash
python3 -m unittest discover -s tests -v
python3 scripts/package_skills.py --app-repo ../iOS/TwinklingCard
```

Packaging first copies the dialect spec and its accept/reject samples from the App checkout (`--app-repo`, or `WINK_APP_REPO`). The `dist/` directory receives independently distributable archives for both Skills. Local packaging does not publish; explicit release tags use the existing GitHub workflow.

Use source material you are authorized to process. Check AI-authored learning content against the source. OCR, web access, media acquisition and model inference are supplied by the chosen AI environment; packaging runs locally.

[Website](https://card.detailsoft.cn/) · [App Store](https://apps.apple.com/cn/app/id1515687192) · [Format index](docs/wink-format.md)

MIT License; see [LICENSE](LICENSE).
