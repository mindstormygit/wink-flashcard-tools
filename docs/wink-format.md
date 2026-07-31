# WinkNotes Format Index

`.wink` is an importable, self-contained flashcard format used by WinkNotes. It can contain one standalone card or one card pack.

## Container

- File extension: `.wink`
- Container: unencrypted ZIP
- Root document: UTF-8 `content.json` containing one `CardVO` or `CardPackVO`
- Optional note-card media: files under `media/`
- Current pack document version: `6`

## Card document types

| Type | Document | Current version | Detailed reference |
| --- | --- | --- | --- |
| `1` | `NoteLegacyDocument` | `3` | [Note and choice pack format](../skills/generate-twinkling-pack/references/wink-format.md) |
| `2` | `ChoiceDocument` | `100` | [Note and choice pack format](../skills/generate-twinkling-pack/references/wink-format.md) |
| `3` | `WordDocument` | `100` | [Word pack format](../skills/generate-twinkling-word-pack/references/wink-format.md) |

## Why the detailed references live inside each Skill

Every Skill release archive must be complete when downloaded by itself. Its builder, validator, input schema, format reference, and user guide therefore travel together inside the Skill directory.

Do not create `content.json`, Base64 document payloads, tag paths, attachment IDs, or ZIP contents by hand. Use the bundled builders and always run the matching validator before delivering a card or pack.
