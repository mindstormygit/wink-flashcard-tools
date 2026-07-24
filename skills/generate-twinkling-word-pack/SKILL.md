---
name: generate-twinkling-word-pack
description: Generate importable, unencrypted TwinklingCard .wink vocabulary packs containing native WordDocument cards. Use when Codex or another user-selected AI agent needs to turn a word list, textbook, PDF, webpage, lesson, topic, or language-learning source into English, Japanese, Korean, German, French, Spanish, Portuguese, or Italian word cards with AI-authored pronunciation, Chinese definitions, examples, language-specific fields, and optional hierarchical tags. This skill does not call private app services, dictionary APIs, or a separate AI service.
---

# Generate Twinkling Word Pack

Create one-language vocabulary packs whose lexical content is authored by the current user-selected AI agent. Do not call private app services, dictionary APIs, or another AI endpoint. Serialize only through the bundled scripts; never hand-author Base64 `rtf`, `WordDocument` IDs, internal tag paths, pack `userInfo`, or ZIP contents.

## Help and Onboarding

When the user asks how to install, share, or use this skill, read [user-guide.zh-CN.md](references/user-guide.zh-CN.md) and provide a copyable prompt tailored to the user's word list or source.

## Workflow

1. Identify the requested words and one pack language.
   - If the source is a PDF, webpage, or document, extract words that are useful for the learner instead of converting every token.
   - Preserve the source spelling and remove exact or case-only duplicates.
   - Split different languages into separate packs.
2. Read [word-authoring.md](references/word-authoring.md), then author each entry using the current agent's own language knowledge and the supplied context.
   - Provide a concise Chinese definition with part-of-speech markers when known.
   - Add pronunciation and one or two natural examples when confident.
   - Add only the language-template fields that are useful and supportable.
   - Never claim that AI-authored content came from a dictionary.
   - If a required meaning is uncertain, omit that word and report it rather than guessing. Leave an optional field empty by omitting it.
3. Read [input-schema.md](references/input-schema.md), then write a UTF-8 JSON input file.
4. Build a new `.wink` file:

   ```bash
   python3 <skill-dir>/scripts/build_word_wink.py <words.json> <output.wink>
   ```

5. Always validate the artifact:

   ```bash
   python3 <skill-dir>/scripts/validate_word_wink.py <output.wink>
   ```

6. Deliver the validated file and report its pack name, language, word count, example count, extra-field count, tag count, tagged-card count, and any words omitted because confidence was too low.

## Constraints

- Generate only native `WordDocument` cards in a word-pack container.
- Use one of `en`, `ja`, `ko`, `de`, `fr`, `es`, `pt`, or `it` per pack.
- Treat all lexical content as AI-authored unless it was explicitly supplied by the user or source.
- Do not fetch or silently imitate private app or dictionary-service data.
- Do not add fabricated citations, dictionary names, frequency ranks, etymologies, or pronunciation variants.
- Assign at most one optional hierarchical tag to each word.
- Do not include attachments, audio files, images, NoteLegacy cards, Choice cards, or mixed languages.
- Let the scripts create card IDs, `WordDocument` IDs, Base64 data, word-pack metadata, and ZIP structure.
- Refuse to deliver when validation fails.
- Do not overwrite an existing output file.

## Format Maintenance

Read [wink-format.md](references/wink-format.md) only when maintaining the serializer or investigating compatibility. Keep its constants synchronized with the Swift models.
