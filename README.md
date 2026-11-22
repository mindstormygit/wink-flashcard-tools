# WinkNotes Flashcard Tools

[简体中文](README.zh-CN.md)

One installable Skill, examples, format guidance, and local packaging tools for WinkNotes. The App's private source is not part of this repository.

## Unified Skill: [`generate-twinkling-pack`](skills/generate-twinkling-pack/)

| Format | Output | Capabilities |
| --- | --- | --- |
| Note & choice cards | Multi-card `.winkmd`, or ZIP with `media/` | Recall and choice questions (single/multi-choice, per-question `shuffle`, inline `:::explanation`), cloze, hierarchical categories, stars, collapsed hints, muted translations/notes, tables, formulas, ordinary pictures, and recordings |
| Native word cards | Legacy `.wink` standalone card or single-language pack | Native `WordDocument` templates for `en`, `ja`, `ko`, `de`, `fr`, `es`, `pt`, `it` with AI-authored pronunciation, Chinese definitions, examples, language fields, and optional hierarchical tags |

**Compatibility and separation**:
- `.winkmd` import targets WinkNotes **3.0** (and **2.21.0** public beta builds). Per-question `:::choice{shuffle=true/false}` overrides and inline `:::explanation` blocks depend on the specific 2.21.0 beta build or 3.0+ release (earlier v2 builds should use bare `:::choice` and place single-question explanations on `<!-- back -->`).
- `.wink` word files remain readable by all supported versions; earlier releases retain the legacy standalone note and word Skills.
- Note cards and native word cards stay in separate packs: each supported vocabulary language gets its own `.wink`, and note/choice cards are delivered as an additional `.winkmd` (or media ZIP) when requested. New note cards use ordinary pictures; existing `.rimg` attachments can be carried back unchanged without creating new image occlusions.

## Install and upgrade

Download `generate-twinkling-pack.zip` from [Releases](https://github.com/mindstormygit/wink-flashcard-tools/releases), then unpack the complete folder into your AI tool's Skills directory. Codex defaults to `~/.codex/skills/generate-twinkling-pack/`. Keep `scripts/`, `references/`, and `agents/`, not just `SKILL.md`. Start a new conversation after updating for fresh discovery.

If you previously installed `generate-twinkling-word-pack`, upgrade in this order:
1. Unpack the complete new `generate-twinkling-pack/` directory.
2. Update any saved `$generate-twinkling-word-pack` prompts, automations, or hardcoded script paths to `$generate-twinkling-pack` / `generate-twinkling-pack/`.
3. Remove the old `generate-twinkling-word-pack/` folder so only one word-card Skill is discovered.
4. Start a new conversation and verify with a word-card request.

```text
Use $generate-twinkling-pack to turn this PDF into about 40 flashcards.
Mix recall and choice questions with inline explanations, use chapter-based
hierarchical categories, and star important cards. Mute translations and notes,
collapse hints, and deliver validated .winkmd (or a ZIP with media).
```

```text
Use $generate-twinkling-pack to select 40 useful words from this source,
write source-grounded definitions and examples, and deliver a validated .wink word pack.
```

Open plain `.winkmd` or `.wink` in WinkNotes from Files, or select ordinary media ZIPs through WinkNotes' in-app file import. See the [Skill router](skills/generate-twinkling-pack/SKILL.md) for routing, [note-workflow.md](skills/generate-twinkling-pack/references/note-workflow.md) / [word-workflow.md](skills/generate-twinkling-pack/references/word-workflow.md) for each path, and the [dialect spec](skills/generate-twinkling-pack/references/wink-spec-markdown-format.md) for `.winkmd` syntax. The spec is copied from the WinkNotes App repository when syncing; edit it there, not here. Python helpers use only the standard library; they check delivery envelopes, attachments, word JSON schemas, and the App's strict v2 rejections, while the App validates full dialect semantics.

## Check and package

```bash
python3 -m unittest discover -s tests -v
python3 scripts/package_skills.py
```

Running `package_skills.py` without arguments packages the committed spec copy into `dist/generate-twinkling-pack.zip`. Maintainers with a local WinkNotes App checkout can sync the dialect spec and accept/reject samples first via `python3 scripts/package_skills.py --app-repo ../iOS/TwinklingCard` (or `WINK_APP_REPO`). Local packaging does not publish; explicit release tags use the existing GitHub workflow.

Use source material you are authorized to process. Check AI-authored learning content against the source. OCR, web access, media acquisition, and model inference are supplied by the chosen AI environment; packaging runs locally.

[Website](https://card.detailsoft.cn/) · [App Store](https://apps.apple.com/cn/app/id1515687192) · [Format index](docs/wink-format.md)

MIT License; see [LICENSE](LICENSE).
