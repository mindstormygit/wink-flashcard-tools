# WinkNotes Format Index

New note/choice authoring uses dialect-v2 `.winkmd`: one UTF-8 manuscript can contain multiple front/back cards. With attachments, use an ordinary unencrypted ZIP containing one root manuscript and files directly under `media/`.

- [Authoring and delivery](../skills/generate-twinkling-pack/SKILL.md)
- [Advanced v2 syntax and metadata](../skills/generate-twinkling-pack/references/advanced-v2.md)
- [Examples](../skills/generate-twinkling-pack/examples/)

The App generates internal document trees and IDs. Do not author those payloads in the note Skill. Metadata supports suggested pack names, hierarchical categories and colors, stars and a new-pack fill preference. Every attachment occurrence is stored independently by the App.

The independent [word Skill](../skills/generate-twinkling-word-pack/SKILL.md) continues generating legacy `.wink`: unencrypted ZIP, root `content.json`, native WordDocument type 3, document version 100, pack version 6. Its [format reference](../skills/generate-twinkling-word-pack/references/wink-format.md) remains inside that Skill so it can ship independently. The App still reads existing legacy note and choice archives.
