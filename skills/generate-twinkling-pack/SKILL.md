---
name: generate-twinkling-pack
description: Create source-grounded WinkNotes note and choice flashcards as dialect-v2 .winkmd manuscripts or ZIPs with images and audio. Use for offline flashcard authoring from notes, PDFs, images or webpages, and for help with this Skill. Word cards use the separate word-card Skill; editing cards already in the App uses MCP.
---

# Generate WinkNotes Flashcards

Write one or many recall cards directly in `.winkmd`; include ordinary pictures or recordings in a ZIP when needed. Requires the WinkNotes version with `.winkmd` import. Older `.wink` files remain readable by the App, but this Skill now authors v2 manuscripts.

Read the source, then [card-authoring-guidelines.md](references/card-authoring-guidelines.md). Cover the useful learning objectives, honor requested counts, and keep each card answerable by itself. Choose recall questions by default and choice blocks when distinguishing alternatives is the learning objective. Do not invent facts missing from the source.

All syntax is defined in [wink-spec-markdown-format.md](references/wink-spec-markdown-format.md), the App's dialect spec copied unchanged. Before writing, read its **Authoring tiers** and **Offline .winkmd files** sections. Look up another section (Tables, Pronunciation guides, Text annotations, Choice blocks, Escaping, Attachments) only when a card needs it. If this file and the spec disagree, follow the spec.

For installation or usage help, read [user-guide.zh-CN.md](references/user-guide.zh-CN.md). For requests to modify cards already in WinkNotes, use available MCP tools and their `get_markdown_help`; do not invent card UUIDs or replace a whole pack to edit a sentence.

## Author a manuscript

```markdown
---
wink_md_version: 2
pack_name: 循环系统
---

<!-- meta
{"category": ["生物", "循环系统"], "starred": true}
-->

左心室把血液泵入{{cloze}}主动脉{{/cloze}}，送往全身。

<!-- back -->

主动脉是体循环的起点。

<!-- card -->

:::choice
哪条血管接收右心室的血液？
- [ ] 主动脉
- [x] 肺动脉
:::

<!-- back -->

右心室经肺动脉把血液泵向肺。
```

- Write common forms. Use occasional forms only when the learning goal or the user asks for them, and never write the "do not write" tier (spec: Authoring tiers). Omit styling that has no learning purpose.
- `category` is one parent-to-child path, not a list of tags; omit it for uncategorized cards. `pack_name` only pre-fills a new pack's name (spec: Offline .winkmd files).
- Put a cloze inside the sentence the learner should complete, usually on the front. Do not wrap the back's answer in a cloze: the learner has already flipped to see it.
- Put translations and side notes (such as `备注：…`) inside `{{mute}}…{{/mute}}`. Questions, answers, explanations and hints are learning content and are read aloud; do not mute them.
- Put hints in a **collapsed** details block:

  ```markdown
  <details>
  <summary>提示</summary>

  从心室的出口考虑。

  </details>
  ```

- Several checked options in a choice block mean several correct answers. Put explanations on the back, unmuted.
- Escape literal punctuation with a backslash (spec: Escaping). Citation marks are the common case: write `参考文献\[1\]`, not `参考文献[1]`, which the App rejects. Close every `{{tag}}` in the same paragraph, in reverse opening order.

## Attachments and delivery

Write `![diagram](att:heart.png)` or `![原声](att:reading.m4a)` on its own line and put the file directly in `media/` (spec: Offline .winkmd files → Attachments and ZIP). Obtain files from the source or available tools; never fabricate media bytes. For new cards, deliver ordinary images. Do not generate `.rimg` occlusions or simulate them by baking masks into a picture. When revising an existing manuscript, keep supplied `.rimg` attachments unchanged.

Use the bundled helper relative to this `SKILL.md`:

```bash
# No attachments: a plain, UTF-8 multi-card file
python3 <skill-dir>/scripts/build_winkmd.py draft.winkmd output.winkmd

# With attachments: exactly one manuscript at ZIP root, media/ next to it
python3 <skill-dir>/scripts/build_winkmd.py draft.winkmd output.zip --media ./media

python3 <skill-dir>/scripts/validate_winkmd.py output.winkmd
python3 <skill-dir>/scripts/validate_winkmd.py output.zip
```

The validator checks packaging, metadata, attachments and the strict v2 rejections the App applies on import; the App checks the remaining document rules. Resolve missing media before delivery even though the App can recover missing pictures as placeholders and skip missing audio. Choose a new output path rather than overwriting an existing file. Deliver the file with its card count and category structure; explain that import lets the user choose or create a pack.
