---
name: generate-twinkling-word-pack
description: Generate importable, unencrypted WinkNotes .wink standalone vocabulary cards or vocabulary packs containing native WordDocument cards. Use when Codex or another user-selected AI agent needs to turn one word or a word list, textbook, PDF, webpage, lesson, topic, or language-learning source into English, Japanese, Korean, German, French, Spanish, Portuguese, or Italian word cards with AI-authored pronunciation, Chinese definitions, examples, language-specific fields, and optional pack-level hierarchical tags. This skill does not call private app services, dictionary APIs, or a separate AI service.
---

# Generate WinkNotes Word Cards and Packs

Create either one standalone vocabulary card for import into an existing pack or a one-language vocabulary pack. Lexical content is authored by the current user-selected AI agent. Do not call private app services, dictionary APIs, or another AI endpoint. Serialize only through the bundled scripts; never hand-author Base64 `rtf`, `WordDocument` IDs, internal tag paths, pack `userInfo`, or ZIP contents.

## Help and Onboarding

When the user asks how to install, share, or use this skill, read [user-guide.zh-CN.md](references/user-guide.zh-CN.md) and provide a copyable prompt tailored to the user's word list or source.

## Workflow

1. Determine the requested product.
   - If the user explicitly requests a word-card pack, build a pack even when it contains one word.
   - If the user explicitly requests one standalone `.wink` word card, build a standalone card and require exactly one word.
   - Treat generic wording such as "make word cards from this PDF" as unspecified. After drafting, build a standalone card when the final count is one; build a pack when it is two or more.
   - Standalone cards do not have a pack name or tags. WinkNotes asks the user to choose the destination pack during import.
2. Identify the requested words and one language.
   - If the source is a PDF, webpage, or document, extract words that are useful for the learner instead of converting every token.
   - Preserve the source spelling and remove exact or case-only duplicates.
   - Split different languages into separate artifacts; use packs when this produces multiple words.
3. Read [word-authoring.md](references/word-authoring.md), then author each entry using the current agent's own language knowledge and the supplied context.
   - Provide a concise Chinese definition with part-of-speech markers when known.
   - Add pronunciation and one or two natural examples when confident.
   - Add only the language-template fields that are useful and supportable.
   - Never claim that AI-authored content came from a dictionary.
   - If a required meaning is uncertain, omit that word and report it rather than guessing. Leave an optional field empty by omitting it.
4. Read [input-schema.md](references/input-schema.md), then write a UTF-8 JSON input file for the selected product.
5. Build a new `.wink` file:

   ```bash
   # Unspecified product: one final word becomes a card; two or more become a pack
   python3 <skill-dir>/scripts/build_word_wink.py <words.json> <output.wink>

   # Explicit pack, including a one-word pack
   python3 <skill-dir>/scripts/build_word_wink.py <words.json> <output.wink> --product pack

   # Explicit standalone word card
   python3 <skill-dir>/scripts/build_word_wink.py <word.json> <output.wink> --product card
   ```

6. Always validate the artifact:

   ```bash
   python3 <skill-dir>/scripts/validate_word_wink.py <output.wink>
   ```

7. Deliver the validated file and identify it as a standalone card or pack.
   - For a standalone card, report its word, language, example count, extra-field count, and whether it was omitted instead because confidence was too low.
   - For a pack, report its pack name, language, word count, example count, extra-field count, tag count, tagged-card count, and any words omitted because confidence was too low.

## Constraints

- Generate only native `WordDocument` cards, either as one root `CardVO` or in a word-pack `CardPackVO`.
- A standalone-card product contains exactly one word and has no pack name or tag.
- Use one of `en`, `ja`, `ko`, `de`, `fr`, `es`, `pt`, or `it` per artifact.
- Treat all lexical content as AI-authored unless it was explicitly supplied by the user or source.
- Do not fetch or silently imitate private app or dictionary-service data.
- Do not add fabricated citations, dictionary names, frequency ranks, etymologies, or pronunciation variants.
- In pack products, assign at most one optional hierarchical tag to each word.
- Do not include attachments, audio files, images, NoteLegacy cards, Choice cards, or mixed languages.
- Let the scripts create card IDs, `WordDocument` IDs, Base64 data, pack metadata when applicable, and ZIP structure.
- Refuse to deliver when validation fails.
- Do not overwrite an existing output file.

## Format Maintenance

Read [wink-format.md](references/wink-format.md) only when maintaining the serializer or investigating compatibility. Keep its constants synchronized with the Swift models.
