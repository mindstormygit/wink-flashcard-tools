# Note & Choice Cards Workflow (`.winkmd` / ZIP)

Write one or many recall, cloze, and choice cards directly in dialect-v2 `.winkmd`; include ordinary pictures or recordings in a ZIP when needed.

## Compatibility

- `.winkmd` import targets WinkNotes **3.0** (the **2.21.0** public beta series also includes `.winkmd` import).
- Per-question `:::choice{shuffle=true/false}` overrides and inline `:::explanation` blocks require a build with those choice additions (target release 3.0; 2.21.0 beta builds vary by build date). If the user specifically targets an earlier v2 build, use bare `:::choice`, put single-question explanations on `<!-- back -->`, and note that per-question shuffle overrides are unavailable on that build.
- Older `.wink` note/choice files remain readable by the App, but this Skill authors v2 manuscripts.

## Before writing

1. Read the source, then [card-authoring-guidelines.md](card-authoring-guidelines.md). Cover the useful learning objectives, honor requested counts, and keep each card answerable by itself. Choose recall questions by default and choice blocks when distinguishing alternatives is the learning objective. Do not invent facts missing from the source.
2. All syntax is defined in [wink-spec-markdown-format.md](wink-spec-markdown-format.md), the App's dialect spec copied unchanged. Read its **Authoring tiers** and **Offline .winkmd files** sections first. Look up another section (Tables, Pronunciation guides, Text annotations, Choice blocks, Escaping, Attachments) only when a card needs it. If this guide and the spec disagree, follow the spec.

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
:::explanation
右心室经肺动脉把血液泵向肺。
:::
```

- Write common forms. Use occasional forms only when the learning goal or the user asks for them, and never write the "do not write" tier (spec: Authoring tiers). Omit styling that has no learning purpose.
- `category` is one parent-to-child path, not a list of tags; omit it for uncategorized cards. `pack_name` only pre-fills a new pack's name (spec: Offline .winkmd files).
- Put a cloze inside the sentence the learner should complete, usually on the front. Do not wrap the back's answer in a cloze: the learner has already flipped to see it.
- Put translations and side notes (such as `备注：…`) inside `{{mute}}…{{/mute}}`. Questions, answers, explanations, and hints are learning content and are read aloud; do not mute them.
- Put hints in a **collapsed** details block:

  ```markdown
  <details>
  <summary>提示</summary>

  从心室的出口考虑。

  </details>
  ```

- In `:::choice` blocks: several `- [x]` options mean several correct answers. Put a question's explanation inside `:::explanation` after the last option (unmuted, using paragraphs, lists, images, formulas, or code — no `<details>` inside). Use `<!-- back -->` for card-level notes or when targeting an earlier v2 build. Omit `shuffle` to follow the pack setting; write `:::choice{shuffle=false}` only when option order must stay fixed (or `shuffle=true` to force shuffling).
- Escape literal punctuation with a backslash (spec: Escaping). Citation marks are the common case: write `参考文献\[1\]`, not `参考文献[1]`, which the App rejects. Close every `{{tag}}` in the same paragraph, in reverse opening order.

## Attachments and delivery

Write `![diagram](att:heart.png)` or `![原声](att:reading.m4a)` on its own line and put the file directly in `media/` (spec: Offline .winkmd files → Attachments and ZIP). Obtain files from the source or available tools; never fabricate media bytes. For new cards, deliver ordinary images. Do not generate `.rimg` occlusions or simulate them by baking masks into a picture. When revising an existing manuscript, keep supplied `.rimg` attachments unchanged.

Use the bundled helpers relative to `SKILL.md`:

```bash
# No attachments: a plain, UTF-8 multi-card file
python3 <skill-dir>/scripts/build_winkmd.py draft.winkmd output.winkmd

# With attachments: exactly one manuscript at ZIP root, media/ next to it
python3 <skill-dir>/scripts/build_winkmd.py draft.winkmd output.zip --media ./media

python3 <skill-dir>/scripts/validate_winkmd.py output.winkmd
python3 <skill-dir>/scripts/validate_winkmd.py output.zip
```

The validator checks packaging, metadata, attachments, and the strict v2 rejections the App applies on import; the App checks the remaining document rules. Resolve missing media before delivery even though the App can recover missing pictures as placeholders and skip missing audio. Choose a new output path rather than overwriting an existing file. Deliver the file with its card count and category structure; explain that import lets the user choose or create a pack.
