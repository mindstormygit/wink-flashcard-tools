<!-- Generated copy. Source: WinkNotes App repository, supportfiles/specs/wink-spec-markdown-format.md, app version 2.21.0, copied 2026-11-09. Do not edit here: edit the App copy, then rerun scripts/package_skills.py. -->

# TwinklingCard Markdown Interchange Format (dialect v2)

The markdown dialect used by TwinklingCard MCP tools that read or write note card content.
`get_card` reports it as `"markdown_dialect": "v2"`. Call `get_markdown_help` with `{}` for a topic directory and example, or with `{"topic":"choices"}` for choice blocks. Use the current v2 rules.

This document is the single source of truth for the dialect. The MCP help topics, the
flashcard-authoring Skill and the Chinese user docs are derived from it.

Each MCP `front` or `back` string contains the body of one side. Send just that body.
The version header and the `<!-- card -->` and `<!-- back -->` separators belong only to
offline `.winkmd` files (see *Offline .winkmd files*). The app decodes each submitted body into its native document model. Block structure follows GFM
(parsed by swift-markdown); TwinklingCard's own notation sits on top as `{{…}}` tags.
Start with *Authoring tiers* to see which forms to write.

**Card types**: `note` cards speak the full dialect below. A choice question is a **block inside
a note** (see *Choice blocks*); there is no separate choice card type. **Word cards accept plain
text only** (`create_cards` word items, `edit_word_card`).

`edit_note_card` replaces each submitted side in full, so only submitted sides may lose styles or attributes the dialect cannot express, while omitted sides retain their native content. An explicit empty string clears that side.

Example note item for `create_cards.items`:

```json
{"type":"note","front":"Capital of France?","back":"Paris"}
```

### Round-trip fidelity

All 28 node types and all 15 mark types in the current native note schema have a dialect
representation. Containers such as table rows and choice options are implied by the syntax.
When editing, carry forward existing cloze and choice ids, attachment references and
`{{ruby64=…}}` tags. For a new card the app can generate ids, and `{{ruby=reading}}` is sufficient.

- A table column takes its first cell's alignment. Each cell keeps its own number format,
  currency and background. For example, `{{format=percent}}25` keeps both the number and its format.
- Each opening `{{note=…}}` creates a fresh annotation id. Export places `mute` and `ruby`
  outside annotations. If either starts or ends inside an annotation, one explanation can
  come back as two annotations. For example, `{{note=血管}}主{{mute}}动脉{{/mute}}{{/note}}`
  still skips 动脉 during speech, but the annotation can be attached to 主 and 动脉 separately.
- The encoder currently writes an empty inline formula as `$$`, which comes back as plain
  text. With an unescaped dollar in its LaTeX, `a$b` exports as `$a$b$` and only `a`
  comes back as math. Authors can write `{{math}}a$b{{/math}}` to read that expression in full.
- Attachment bytes, intrinsic image dimensions and image content versions come from the
  resolved attachment and the card. The text carries the reference, caption and optional display width.
  An empty image caption reads as an absent `alt`. An empty audio title or the literal title
  `录音` reads as the default title.

## Authoring tiers

Write **common** forms freely. Use **occasional** forms only when the learning goal or the
user asks for them. **Do not write** the last group in new content: the app produces those
forms itself for round trips, or reads them only for compatibility.

| Tier | Forms |
|---|---|
| Common | paragraphs; `**bold**`, `*italic*`; headings; bullet and numbered lists; `[label](https://…)`; `{{cloze}}…{{/cloze}}`; `{{mute}}…{{/mute}}`; `$…$` and `$$` formulas; fenced code; images and recordings `![…](att:…)`; `<details>` for hints; choice blocks; backslash escapes |
| Occasional | tables and their markers; `{{ruby=…}}`; `{{note=…}}`; `{{color:…}}`; cloze colors; `{{sup}}` / `{{sub}}`; `{{u}}`; `~~strike~~`; inline code; `>` quotes; to-do lists; dividers; `{{align=…}}`; `{{indent=N}}`; `{{width=…}}`; `{{br}}`; `{{math}}…{{/math}}`; mermaid code blocks; `{{size:…}}` and `{{font:…}}` only when the user asks |
| Do not write | ids (`{{cloze:id=…}}`, `:::choice{#…}`, option `{#…}`); `{{ruby64=…}}`; the tag forms `{{b}}`, `{{i}}`, `{{s}}`, `{{code}}`; `{{u:wavy}}`, `{{u:dashed}}`, `{{u:dotted}}`; `{{header=row}}`; `{{indent=0}}` empty paragraphs; `&#32;`; v1 and Anki notation; remote image URLs |

- When editing a card through MCP, carry forward what `get_card` returned, including ids
  and `ruby64` tags. The "do not write" tier applies to content you author.
- Cloze colors: omit `color` for the default yellow. To group clozes by meaning, use the
  app's highlighter presets: `#FFD345` yellow, `#FF644E` red, `#F06292` pink, `#FEAE00`
  orange, `#1DB100` green, `#00AB8E` teal, `#00A2FF` blue, `#BA68C8` purple.
- `wink-dialect-v2-samples.json` (App repository) lists bodies that a strict
  reader must accept or reject. The app's tests and the Skill's validator both check it.

## Inline styles

| Syntax | Meaning |
|---|---|
| `**text**` | bold |
| `*text*` | italic |
| `~~text~~` | strikethrough (double tilde only) |
| `` `text` `` | inline code |
| `[text](url)` | link |
| `{{u}}text{{/u}}` | underline (single solid line, the default; input also accepts `{{u:solid}}`) |
| `{{u:wavy}}text{{/u}}`, `{{u:dashed}}text{{/u}}`, `{{u:dotted}}text{{/u}}` | wavy / dashed / dotted underline (kept for compatibility; the app itself only offers the single line) |
| `{{sup}}text{{/sup}}` / `{{sub}}text{{/sub}}` | superscript / subscript |
| `{{color:#RRGGBB}}text{{/color}}` | text color |
| `{{cloze:id=c1;color=#RRGGBB}}text{{/cloze}}` | highlighter = cloze deletion (covered during review) |
| `{{ruby=shōushi}}收拾{{/ruby}}` | pronunciation guide above the original text (any language) |
| `{{note=狐狸}}fox{{/note}}` | text annotation; its explanation does not change the original text |
| `{{mute}}text{{/mute}}` | skip when reading aloud: the text is shown, searched and reviewed as usual but never spoken (use it for translations and side notes; questions, answers, explanations and hints are read aloud) |
| `$x^2$` | inline formula (LaTeX) |
| `{{math}} x {{/math}}` | inline formula whose LaTeX starts or ends with whitespace (`$…$` cannot); the text in between is raw LaTeX |
| `{{size:large}}text{{/size}}` | font size level: `small` (0.8×), `large` (1.25×), `x-large` (1.5×), `xx-large` (2×); normal size has no tag |
| `{{font:Georgia}}text{{/font}}` | font family (name after the colon may contain spaces; a font name containing `}` is rejected); the default font has no tag. A device that lacks the font falls back to the pack font, then the system font |

- Superscript and subscript are mutually exclusive. Tags nest: `{{color:#FF644E}}**red bold**{{/color}}`.
- **Read aloud** never speaks code blocks (including mermaid), display formulas or inline
  formulas; inline code is spoken. Wrap any other text that should stay silent in
  `{{mute}}…{{/mute}}`. Output always places `{{mute}}` outermost.
- **Cloze == highlight.** On input `id` and `color` are both optional (`{{cloze}}text{{/cloze}}`);
  a missing id is generated, a missing color uses the default highlighter color. Output always carries the
  id. Cloze ids are unique across the whole card (both sides).
- When `**`, `*`, `~~` or `` ` `` cannot be written safely (for example bold right next to CJK
  punctuation), output uses the tag form `{{b}}…{{/b}}`, `{{i}}…{{/i}}`, `{{s}}…{{/s}}`,
  `{{code}}…{{/code}}`. Input accepts both forms.

### Pronunciation guides (ruby)

`{{ruby=shōushi}}收拾{{/ruby}}` wraps a word or group; to annotate character by character,
wrap each character separately. The reading has 1–100 Unicode code points, no control
characters and no leading/trailing whitespace. Escape a backslash as `\\` and a right brace
as `\}` (a literal `}}` can also be written `\}}`). A newline is invalid. Ruby has no id.
Adjacent pieces with matching reading and metadata render as one group, even across bold/color/etc.
Ruby can coexist with notes, links and clozes and can appear in choice options. If any part
of a ruby group is still covered by a cloze, its whole reading stays hidden.

MCP input also accepts Anki notation immediately after Han characters or kana (`.winkmd`
files reject it; see *Offline .winkmd files*): `漢字[かんじ]`,
`收拾[shōushi]`. The bracket reading must pass the same limits (a leading space or more than
100 code points leaves ordinary brackets unchanged). Code, formulas, link destinations and
attachment captions are not interpreted as this alias; a link's visible label can use it.
Escape literal brackets, e.g. `漢字\[plain\]`. Output always uses the canonical ruby tags.
Anki HTML imports also accept standard `<ruby>…<rt>…</rt></ruby>` pairs.

Readings appear above the base in the editor, Note reader and PDF. They do not enter search
projections or machine speech. The pack's “hide pronunciation guides” display preference
can temporarily hide them in the reader; it does not alter stored content or PDF output.
The Note editor selection menu includes “注音…”. Opening the panel is offline; automatic
pronunciation requires an explicit button press, a registered signed-in account, and the DSWordAPI service. It consumes no points. Offline manual editing and saved readings do not require sign-in.

Optional `ruby.attrs.metadata` stores `langCode`, `system`, `accent`, `origin`
(`manual` or `generated`) and a local `group` string (1–64 ASCII letters/digits/underscore/hyphen).
Valid profile triples are `zh/pinyin/cmn-CN`, `zh/zhuyin/cmn-CN`, `zh/zhuyin/cmn-TW`, `ja/hiragana/ja-JP`,
`en/ipa/en-US`, `en/ipa/en-GB`. These are storage slots, not engine availability guarantees.
Adjacent readings merge only when all ruby attributes match. Copy/paste assigns fresh local
groups; existing/manual readings are protected when generating missing readings.

Legacy readings retain `{{ruby=reading}}base{{/ruby}}`. To preserve metadata, use
`{{ruby64=BASE64}}base{{/ruby}}`, where BASE64 is standard Base64 of UTF-8 JSON
`{"text":"reading","metadata":{"langCode":"zh","system":"pinyin","accent":"cmn-CN","origin":"manual","group":"local-1"}}`.
Both forms use the same reading validation and `{{/ruby}}` closing tag. JSON remains the
storage/archive/sync source of truth. Unknown metadata fields in native card JSON make that card read-only;
legacy cards without metadata require no migration. English IPA metadata may also include
`"generation":{"method":"rule","engine":"espeak-ng"}` with optional `version` and
`dictionaryVersion` strings (1–256 Unicode code points without controls or edge whitespace)
or null. Preserve the whole `ruby64` opening tag when the reading is unchanged.

### Text annotations

`{{note=explanation}}original text{{/note}}` wraps one continuous range in a single text
block (paragraph, heading, choice prompt, table cell or collapsible summary). Notes cannot
overlap or nest, and are not allowed in choice options. Bold, color, links and clozes can
coexist with a note. Adjacent notes remain separate, even when their explanations match.

Explanations contain 1–500 Unicode code points, no leading/trailing whitespace and no control
characters other than LF newline. Within the explanation, escape a backslash as `\\`, a
right brace as `\}` (a literal `}}` can also be written `\}}`), and a newline as `\n`.
For example: `{{note=第一行\n第二行，字面 \}}}}原文{{/note}}`.
Note ids are generated on input and never written on output. Search projections append the
explanation in full-width parentheses (`fox（狐狸）`); speech reads the original text only.

## Blocks

| Syntax | Meaning |
|---|---|
| paragraph text, blank line between paragraphs | paragraph |
| trailing `\` at the end of a line | line break inside a paragraph |
| one to six `#` characters followed by a space | heading; a line break inside a heading is written `{{br}}` (a heading is one line) |
| `- item`, `1. item` | bullet / ordered list (nesting by indentation) |
| `- [ ] task`, `- [x] task` | to-do list |
| `---` | divider |
| ```` ``` ```` fenced block (optional language) | code block |
| `$$` … `$$` on their own lines | display formula |
| `{{indent=N}}` at the start of a paragraph | paragraph indent level 0–16 |
| `{{indent=0}}` alone on a line | an empty paragraph |
| `{{align=center}}` / `{{align=right}}` at the start of a paragraph or heading | alignment (left is the default and is never written); combines with indent as `{{indent=2}}{{align=right}}`; for a heading write `## {{align=center}}Title` |
| `![caption](att:<file>)` alone on a line | image; a directly following `{{width=0.5}}` sets the share of the text width (0 < x ≤ 1, by default the smaller of intrinsic and available width) |

Do not rely on "two trailing spaces" for line breaks; use the trailing backslash. Output never
uses smart punctuation.

## Tables

GFM tables. Every row has the same number of cells (no merged cells, no column widths).
By default the first row is the header row; a marker line right above the table changes that.

```
| 单词 | 释义 |
| --- | :---: |
| apple | 苹果<br>名词{{p}}![图片](att:3f2c….png) |
```

- Marker line (optional, on its own line directly above the table): `{{header=none}}` (no header
  row: the GFM header row is just the first body row), `{{header=column}}` (the first cell of every
  row is a header, the first row is a body row), `{{header=both}}` (header row and header column),
  `{{stripes}}` (shade every other body row). Markers can be combined: `{{header=column}}{{stripes}}`.
  No marker line means header row on, header column off, no stripes. Input also accepts the default `{{header=row}}`.
- Cell attributes go at the very start of a cell, in any order:
  `{{format=number}}`, `{{format=percent}}`, `{{format=currency:CNY}}` (ISO 4217 code, three capital
  letters) and `{{bg=yellow}}` (one of `gray red yellow pink green cyan blue purple brown`).
  A formatted cell stores exactly what you type: write plain numbers like `1234.5`, `25`, `-3`
  (no thousands separators, no `%`, no currency sign) and the app shows `1,234.5`, `25%`, `¥1,234.50`
  in the reader's locale. `percent` does not multiply by 100. Cells that are not a plain number
  are shown as typed. The format and background apply to that cell. Repeat the marker on each cell you want to format.
  An unknown value is an error.
- Column alignment goes in the delimiter row: `:---:` center, `---:` right, `---` / `:---` left. Alignment is per column: on output
  the first row's alignment is written for the whole column, so a body cell aligned differently
  from the first row takes its alignment after a round trip.
- A cell holds paragraphs, ordinary or rich images, and audio bars. `<br>` (also `<br/>`) is a line break inside a cell,
  `{{p}}` starts a new paragraph, an image reference sits in the cell like in a paragraph.
- A literal `|` in a cell is escaped `\|`. Missing cells in a short row are filled empty.
- Tables sit at the top level or inside a collapsible block, not inside lists or other tables.

## Collapsible blocks

```
<details>
<summary>例句</summary>

Any content: paragraphs, lists, tables, headings, nested `<details>` …

</details>
```

- `<details open>` means expanded by default; plain `<details>` is collapsed by default. Viewers
  can toggle it while reading; that does not change the card.
- The `<summary>` is one line of text with the usual inline styles (no line breaks); it may sit
  on the same line as `<details>`. Leave a blank line after `<summary>` and before `</details>`.
- `<details>` must start at the beginning of a line (not inside a list). No choice blocks inside.

## Quote blocks

```
> {{bg=yellow}}
>
> 一段引用，可以有 **样式**。
>
> - 列表
> - ![图片](att:3f2c….png)
```

- Every line starts with `> `. A quote holds paragraphs, headings, lists, dividers, images, code
  blocks and display formulas; tables, choice blocks, collapsible blocks and other quotes are not
  allowed inside (they are moved out after the quote).
- Quotes have a transparent background and a gray bar on the left by default. An optional
  `{{bg=…}}` marker on the first line sets the bar color. Allowed names are
  `gray red yellow pink green cyan blue purple brown`. An unknown value is an error.
- A quote sits at the top level or inside a collapsible block, not inside a list, a table cell or
  a choice block. Nested quotes (`> >`) are read as one level.
- Obsidian callouts (`> [!note] Title`) are not special: the `[!note]` line is kept as text.

## Choice blocks

```
:::choice{#q1}
下列哪些是名词？
- [x] apple {#a}
- [ ] quickly {#b}
- [x] ![图片](att:3f2c….png) {#c}
:::
```

- Opens with `:::choice` (optional `{#id}`), closes with a line containing only `:::`.
- Write at least one prompt block, then **end with at least one option**. Prompts can contain
  paragraphs, images (including rich images), display formulas, code blocks, bullet or ordered lists and audio bars. `- [x]` marks a correct option, `- [ ]` an incorrect one. Option ids `{#id}` are
  optional on input and generated when missing.
- Each option is either one paragraph of text or exactly one image reference; mixing text and an
  image in one option is an error. Clozes and text annotations are disallowed in options. A text option may start with
  `{{indent=N}}` for an indent.
- A choice block sits at the top level of a side, not inside a list. A card may hold any number
  of choice blocks; a block with no correct option is allowed. The explanation goes on the back
  side as ordinary content.

## Escaping

Output backslash-escapes every literal character that would otherwise read as markup:
`*`, `_`, `~`, backtick, `$`, `[`, `]`, `{`, `}`, `<`, `>`, `&`, `|`, `^`, `\` and a line-leading `#`, `-`, `+`, `:`, `1.`. Leading and trailing
spaces are written as `&#32;`. Input removes the escapes as the last step, so text that merely
looks like markup (`**not bold**` escaped as `\*\*not bold\*\*`) round-trips unchanged.

## Attachments

Bytes never travel inside the text; the text carries references:

| Syntax | Type |
|---|---|
| `![图片](att:<uuid>.<ext>)` | image |
| `![图文](att:<uuid>.rimg)` | rich image (occlusion / drawing / annotation; see the RichImage spec resource) |
| `![标题](att:<uuid>.m4a)` | audio bar (a recording; `.m4a`, `.m4b`, `.wav`, `.mp3`) |

The bracket text becomes the image’s `alt` or the recording’s title. The `att:<file>` destination identifies the attachment. `![…](https://…)` is
rejected; bare `att: https://…` is ordinary text.

**Audio bars**: a recording sits in the text as its own line, `![原声朗读](att:<uuid>.m4a)`.
The brackets hold the title: up to 50 characters, no line breaks, no leading or trailing
spaces; write `![录音](att:…)` or `![](att:…)` for no title. An audio bar may stand at the top
level, inside a list item (not as its first block), a choice prompt, a table cell (written the
same way) or a collapsible block; inside a `>` quote it is moved out like a table. It may reference an existing card recording or a new exchange file. New audio must be playable,
use m4a/m4b/wav/mp3, and be at most 10 MiB. A recording is used by exactly one audio bar;
repeated references are handled as described under **Writing** below.
Recordings that older cards kept outside the text show up in `get_card` as audio bars at the end
of their side.

- **Reading** (`get_card`): existing references are deterministic `<attachment-uuid>.<ext>`.
  Pass `export_attachments: true` to export bytes into a new task directory for this call; the
  top-level `exported` field gives relative paths `task-UUID/uuid.ext`. Without the flag no files
  are written and Downloads access is not needed; fetch an image via `get_card_attachment`.
- **Writing** (`create_cards` / `edit_note_card`): in `edit_note_card` a reference first resolves
  against the card's existing images and recordings (`<uuid>.<ext>` or the bare uuid) —
  "keep/move this image"; images and recordings no longer referenced are deleted. For new files, copy an image or recording the client can read to
  `~/Downloads/闪卡交换/image.png` and write `![图片](att:image.png)`. Create the directory if
  needed; one subdirectory level is allowed (`att:task-1/image.png`). Use safe filenames (ASCII,
  no spaces). No preparation tool or task registration is required. Existing images, rich images, recordings and exchange files may be referenced repeatedly:
  - **New file** from the exchange directory: every occurrence becomes its own attachment.
  - **Existing attachment, first occurrence** in the submitted faces: it keeps the attachment and its id. `<uuid>` and `<uuid>.<ext>` count as the same attachment.
  - **Existing attachment, each later occurrence**: a copy with a new id.
  - **Recording still used by an omitted face**: every occurrence in the submitted face is a copy, because one recording serves one audio bar.

  An omitted face stays unchanged. Any invalid reference rejects the whole call before anything is written.
- Example single note:
  `{"pack_uuid":"<pack UUID>","items":[{"type":"note","front":"![图片](att:image.png)","back":""}]}`.
  Both `front` and `back` are required for a new note; either may be empty.
- External imports accept regular files at the exchange root or one subdirectory below it.
  Files outside that root, `..` traversal, and symlinks are rejected. The exchange root is not
  purged automatically; use unique filenames to avoid overwrites.
- The first real file access may trigger the macOS Downloads permission prompt. If access was
  denied, restore it in System Settings as the error directs. Discovering tools and plain-text
  writes never touch Downloads. This grant does not authorize the external client's own file
  tools.
- **`.rimg` files are accepted** as `att:` targets: produce JSON per the RichImage spec
  (`wink://spec/richimage-format`), place it in the exchange directory, and reference
  `![图文](att:name.rimg)`.
- To copy images to another card, export them and reference the exported task paths instead of
  the source card's uuid references.

**Lossless caveat**: occlusion coordinates, drawings and audio bytes live in the attachment
files, not in the text.

## Diagrams

A fenced ```` ```mermaid ```` block is stored as a code block with language `mermaid` in this
version (diagram rendering comes in a later version). Mind maps and flowcharts can be written that
way already.

## Offline .winkmd files

A `.winkmd` file is a UTF-8 manuscript holding any number of note cards. The user imports it
from the packs list or opens it from Files. Word cards are not supported; they use CSV.

```markdown
---
wink_md_version: 2
pack_name: 心脏结构
---

<!-- meta
{"category": ["医学", "循环系统"], "starred": true}
-->

左心室把血液泵入{{cloze}}主动脉{{/cloze}}，送往全身。

<!-- back -->

主动脉是体循环的起点。

<!-- card -->

![心脏结构图](att:heart.png)

<!-- back -->

![原声](att:reading.m4a)
```

### Header

- The header is optional. It is present only when the first line is `---` and the second
  line starts with one of the keys below (`wink_md_version:`, `pack_name:`, `categories:`,
  `fill_blanks:` or `generator:`), so a body may begin with a divider followed by any other line.
- One `key: value` per line, then a closing `---`. A string may be written bare or as a JSON
  double-quoted string; arrays are JSON. This is not YAML. A repeated key is an error; an
  unknown key is ignored.

| Key | Meaning |
|---|---|
| `wink_md_version` | `2`. Omitted means 2. A larger number asks the user to update the app; any other value is an error. |
| `pack_name` | Pre-fills the name when the user imports into a new pack; defaults to the file name; must not be blank. Importing into an existing pack never renames it. |
| `categories` | Optional JSON array such as `[{"path":["医学"],"color":"#29B6F6"},{"path":["医学","循环系统"],"color":"#13C25C"}]`. It sets the color of categories this import creates. Existing categories keep their color. Paths must be non-empty and unique; colors are `#RRGGBB`. Declare only paths the cards use. |
| `fill_blanks` | `true` (type the cloze answer) or `false` (reveal it). Applies only when the import creates a new pack; omitted means the app default. An existing pack keeps its preference. |
| `generator` | The tool and version that wrote the file, for example `generate-twinkling-pack 2.0.0`. Tools write it; authors do not. The app does not act on it yet; a later version may use it to suggest updating an old tool. |

### Cards and sides

- `<!-- card -->` starts the next card. The first `<!-- back -->` in a card starts its back;
  a later one is dropped and the text after it stays on the back. Without `<!-- back -->`
  the card has only a front.
- Each separator occupies its own line at the top level, with blank lines around it.
  Inside code, formulas, lists, quotes, choice blocks or `<details>` it is ordinary text.
- Cards are imported in the written order. Empty cards are skipped, for example after a
  leading, trailing or repeated `<!-- card -->`. A card left empty after a missing recording
  is removed is also skipped; a missing-image placeholder counts as content. A file with no
  cards is an error. Card numbers in messages count every separator, skipped cards included.

### Card metadata

A card may begin its front with one top-level comment holding a JSON object:

```markdown
<!-- meta
{"category": ["医学", "循环系统"], "starred": true}
-->
```

- `category` is **one path from parent to child**, not a list of tags. The card goes into
  the last level. The import reuses an existing path and creates missing levels. Omitted or
  `[]` means uncategorized; a card never inherits the previous card's category. Each name has
  1–200 characters, no line break, is not blank and does not contain `/$-#-$/`; at most 32 levels.
- `starred` is a boolean; omitted means `false`.
- A wrong type, a second meta comment or a missing `-->` is an error. A top-level meta comment
  anywhere other than the start of the front (after body text, or on the back) counts as a second one. Unknown fields are
  ignored. The comment is not shown on the card. Do not write category ids.

### Attachments and ZIP

- Text-only cards: deliver the `.winkmd` file alone.
- With images or recordings: deliver an ordinary ZIP with **exactly one** `.winkmd` at its
  root and the files directly in a root `media/` folder. Reference a file by its name only:
  `![心脏结构图](att:heart.png)` for `media/heart.png`. Use simple names without spaces;
  the full name, extension included, must match.
- Each `att:` occurrence becomes its own attachment, even when the same file is referenced
  repeatedly.
- A missing image becomes a placeholder; a missing recording's audio bar is removed. The
  import continues and then lists each missing file with its card number and side.
- A file that is present but unreadable, of an unsupported type or larger than 10 MB
  (10 MiB) rejects the whole import. Recordings must be playable m4a, m4b, wav or mp3.
  Images and `.rimg` rich images have the same 10 MiB limit.

### Import

- The user picks an existing note pack or creates one. The free plan's 30-card limit per
  pack is not checked.
- `.winkmd` files accept dialect v2 only. Unlike MCP input, they reject v1 notation, Anki
  `{{c1::…}}`, unescaped brackets right after Han characters or kana (`参考文献[1]` must be
  written `参考文献\[1\]`), caret superscripts `^x^`, a known tag with an invalid value, a tag
  left open at the end of its paragraph or closed in the wrong order, and a choice block,
  `<details>` or `$$` formula without its closing line. The error names the card. Code and
  escaped text are not checked. An unknown `{{…}}` tag stays as literal text.
- The whole file is checked before anything is written. If writing fails part way, the cards
  already written stay, and the message says how many were imported and which card failed.

## Cards that cannot be read

`get_card` returns `editable: false` with a `notice` for a card the app cannot read losslessly
(an old card that cannot be upgraded without loss, a card written by a newer app version, or
corrupt content). Its `front`/`back` are then plain text only; `edit_note_card` refuses it.

## v1 notation (read only)

Earlier sessions may have used dialect v1. MCP input still accepts it; `.winkmd` files reject it. It is never produced:
`==x==` and `[x]{highlight=#…}` → cloze; `[x]{color=#…}` → text color; `[x]{script=super|sub}`,
`^x^` → super/subscript; `<u>x</u>` → underline; Anki `{{cN::x}}` → cloze (group N picks the
5-color rotation yellow, red, green, cyan, blue). The v1 single-tilde subscript `~x~` is literal
text in v2. Write new content in v2.

## Version

Dialect v2 (2026-10; offline `.winkmd` files added 2026-11). The app writes only the current
version. MCP input also reads v1 for compatibility; `.winkmd` files accept v2 only.
