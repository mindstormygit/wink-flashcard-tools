# Changelog

This file records repository-wide releases. Component-specific changes are documented inside the Skill directory.

## 2.0.0 — 2026-11-22

- Merges `generate-twinkling-word-pack` into `generate-twinkling-pack` so users install and invoke one unified WinkNotes Skill for note, choice, and native vocabulary cards.
- Note/choice authoring uses dialect-v2 `.winkmd` and media ZIPs, with hierarchy, stars, suggested pack names, colors, new-pack fill preference, and choice `shuffle` / `:::explanation` support.
- Native vocabulary card/pack authoring continues delivering `.wink` (`WordDocument`) files via the bundled scripts. Earlier releases retain the standalone legacy Skills.

## 1.2.1 — 2026-07-30

- Aligns the Chinese product name with “闪卡” and the English product name with WinkNotes across both Skills.

## 1.2.0 — 2026-07-30

- Adds standalone note, choice, and word cards as an alternative to pack output.
- Extends both builders and validators to support either a root `CardVO` or `CardPackVO`.
- Selects a standalone card for one final card and a pack for two or more when the product is unspecified; explicit product requests take priority.
- Publishes the note-and-choice Skill and the word-card Skill in one open repository.
- Adds bilingual onboarding, a format index, reproducible release packaging, and automated validation.
