---
name: generate-twinkling-pack
description: >-
  Create source-grounded WinkNotes flashcards in one Skill: dialect-v2 .winkmd
  manuscripts (or media ZIPs) for note, cloze, and choice cards, and native
  WordDocument .wink standalone cards or packs for vocabulary (en, ja, ko, de,
  fr, es, pt, it). Use for offline flashcard authoring from notes, word lists,
  textbooks, PDFs, images, or webpages, and for help with this Skill. Editing
  cards already in the App uses MCP.
---

# Generate WinkNotes Flashcards

One unified Skill covers both WinkNotes offline authoring formats. Route the request first, then read **only** the workflow reference for the chosen path so the two formats never mix.

## Route the request

| User goal | Path to read & follow | Output |
| --- | --- | --- |
| Notes, concepts, Q&A, cloze, multiple-choice, grammar, reading comprehension, tables, formulas, diagrams, or recordings | [references/note-workflow.md](references/note-workflow.md) | `.winkmd`, or `.zip` with `media/` |
| Vocabulary cards, word lists, or word packs in `en`, `ja`, `ko`, `de`, `fr`, `es`, `pt`, or `it` | [references/word-workflow.md](references/word-workflow.md) | Native `WordDocument` `.wink` (standalone card or single-language pack) |
| Both vocabulary cards and note/choice cards from the same source | Follow **both** workflows separately | **One `.wink` per supported language, plus one `.winkmd` (or media ZIP)** |

Apply these boundary decisions before drafting:

1. **Never mix note/choice cards and native word cards in one file.** WinkNotes keeps note packs and word packs separate. When a request covers both (or multiple vocabulary languages plus notes), build and validate each deliverable separately: one `.wink` per supported language, plus one `.winkmd` (or media ZIP) for note/choice cards.
2. **Clarify ambiguous language-learning material.** If the user supplies a foreign-language article, textbook chapter, or PDF without stating the learning goal (for example, "turn this English article into flashcards"), ask one brief question first: whether they want native vocabulary cards, reading/comprehension note cards, or both.
3. **Confirm unsupported vocabulary languages.** Native `WordDocument` templates only support `en`, `ja`, `ko`, `de`, `fr`, `es`, `pt`, and `it`. For a word list in another language (such as Russian or Arabic), state that limitation and ask for confirmation before authoring ordinary Q&A flashcards in `.winkmd` instead.
4. **Preserve explicit word-product requests.** When following the word workflow, honor explicit requests for a standalone card (`--product card`) or a pack (`--product pack`); otherwise let the final word count decide (1 → standalone card, 2+ → pack).

## Help and editing existing cards

- **Installation, migration, or usage help**: read [references/user-guide.zh-CN.md](references/user-guide.zh-CN.md) and provide a copyable prompt tailored to the user's material.
- **Editing cards already in WinkNotes**: use available MCP tools and their `get_markdown_help`; do not invent card UUIDs or replace a whole pack to edit a sentence.
