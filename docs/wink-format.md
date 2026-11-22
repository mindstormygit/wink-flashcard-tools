# WinkNotes Format Index

The unified Skill [`generate-twinkling-pack`](../skills/generate-twinkling-pack/SKILL.md) supports two WinkNotes authoring formats:

## 1. Note & choice cards (dialect-v2 `.winkmd` / media ZIP)

One UTF-8 `.winkmd` manuscript can contain multiple front/back note, cloze, and choice cards. With attachments, use an ordinary unencrypted ZIP containing one root manuscript and files directly under `media/`.

- [Skill router](../skills/generate-twinkling-pack/SKILL.md)
- [Note & choice workflow](../skills/generate-twinkling-pack/references/note-workflow.md)
- [Dialect v2 specification](../skills/generate-twinkling-pack/references/wink-spec-markdown-format.md)
- [Examples](../skills/generate-twinkling-pack/examples/)

The App generates internal document trees and IDs. Do not author those payloads for note cards. Metadata supports suggested pack names, hierarchical categories and colors, stars, and a new-pack fill preference. Every attachment occurrence is stored independently by the App.

## 2. Native word cards & packs (`.wink`)

Native vocabulary cards continue using legacy `.wink`: unencrypted ZIP, root `content.json`, native `WordDocument` type 3, document version 100, pack version 6.

- [Word cards workflow](../skills/generate-twinkling-pack/references/word-workflow.md)
- [Word authoring guidance](../skills/generate-twinkling-pack/references/word-authoring.md)
- [Word JSON input schema](../skills/generate-twinkling-pack/references/word-input-schema.md)
- [Word `.wink` format reference](../skills/generate-twinkling-pack/references/word-wink-format.md)

The App still reads existing legacy `.wink` note and choice archives.
