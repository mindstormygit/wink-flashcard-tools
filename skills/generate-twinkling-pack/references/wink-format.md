# WinkNotes Mixed NoteLegacy and Choice Format

Use this reference when maintaining the scripts or diagnosing import compatibility.

## Container

- File extension: `.wink`
- Container: unencrypted ZIP
- First entry: one root-level `content.json`
- Optional entries: ordinary image files and native RichImage `.rimg` files directly under `media/`
- Encoding: UTF-8 JSON without a byte-order mark
- Media filenames: `<32-lowercase-hex-attachment-id>.<extension>`

## Root Product

`content.json` contains either one `CardPackVO` for a pack or one `CardVO` for a standalone card. A standalone card is not wrapped in a one-card pack. During import, WinkNotes asks the user to choose its destination pack and assigns the import tag, so the standalone root omits `tag`.

## Pack

`content.json` is the minimal subset accepted by `CardPackVO`:

```json
{
  "name": "Pack name",
  "cards": [],
  "tags": [
    {
      "name": "晶圆准备",
      "lighthex": "#29B6F6"
    },
    {
      "name": "晶圆准备/$-#-$/背磨",
      "lighthex": "#FFD345"
    }
  ],
  "version": 6
}
```

Omitted pack properties use the application decoder’s defaults. Omit `tags` when the pack has no tags.

## Tag

`TagVO` contains exactly:

```json
{
  "name": "晶圆准备/$-#-$/背磨",
  "lighthex": "#FFD345"
}
```

- `name`: Full hierarchy path. Components are joined with `/$-#-$/`.
- `lighthex`: Tag color as `#RRGGBB`.

Define every parent path separately in the pack-level `tags` array. Paths must be unique. The builder accepts agent-friendly IDs and parent IDs, then creates these internal paths.

## Card

Each `CardVO` contains:

```json
{
  "uuid": "32 lowercase hexadecimal characters",
  "sidea": "Front text",
  "sideb": "Back text",
  "flag": 0,
  "rtf": "Base64-encoded NoteLegacyDocument JSON",
  "sideaAttIds": ["0123456789abcdef0123456789abcdef.png"],
  "sidebAttIds": [],
  "tag": {
    "name": "晶圆准备/$-#-$/背磨",
    "lighthex": "#FFD345"
  },
  "version": 6
}
```

Swift’s default `Data` JSON representation is standard Base64, so `rtf` must be a Base64 string rather than an embedded object.

For a standalone-card product, this `CardVO` is the root value of `content.json` and omits `tag`. For a pack product, it appears inside `CardPackVO.cards`.

`rtf` may contain either Base64-encoded `NoteLegacyDocument` JSON or Base64-encoded `ChoiceDocument` JSON.

For note cards, `sideaAttIds` and `sidebAttIds` list media filenames in inline occurrence order for their respective sides. The same filename is not reused across occurrences. Choice cards in this version are text-only and use empty attachment arrays.

`tag` is optional. When present, it must exactly match a definition in the pack-level `tags` array. A `CardVO` can reference at most one tag. During import, WinkNotes creates the hierarchy first and then assigns the card by its full tag path.

## NoteLegacyDocument

Decode `rtf` to UTF-8 JSON. An unformatted document has this shape:

```json
{
  "v": 3,
  "sa": {"c": "Front text"},
  "sb": {"c": "Back text"}
}
```

`NoteLegacyContent` uses `c` for content and optional `a` for spans. Omit a document `type`; `CardDocumentIdentifier` defaults a missing type to `noteLegacy`.

## NoteLegacySpan

A formatted side adds spans:

```json
{
  "c": "重点内容",
  "a": [
    {
      "f": 0,
      "l": 2,
      "s": 10,
      "mc": "#FFD60A"
    }
  ]
}
```

The location `f` and length `l` use UTF-16 code units, matching `NSRange`; an Emoji outside the BMP therefore counts as two units. Styled segment arrays are responsible for text boundaries, while the build script calculates these values.

Style `s` is an OptionSet bitmask:

- `1`: underline
- `2`: bold
- `4`: strikethrough
- `8`: mark-pen highlight/occlusion
- `16`: super/subscript

Combine styles with bitwise OR. Other optional span keys are:

- `c`: text color as `#RRGGBB`
- `mc`: custom mark-pen color as `#RRGGBB`
- `lk`: absolute HTTP or HTTPS URL
- `sc`: `1` for superscript or `-1` for subscript

An inline image occupies one U+FFFC object-replacement character in `c` and has a dedicated span:

```json
{
  "c": "结构：￼",
  "a": [
    {
      "f": 3,
      "l": 1,
      "at": "0123456789abcdef0123456789abcdef",
      "aes": "png"
    }
  ]
}
```

- `at`: Attachment ID, equal to the media filename stem.
- `aes`: Lowercase media file extension.
- `l`: Always `1`, because U+FFFC is one UTF-16 code unit.
- `pad`: Omitted; image data lives in `media/`.

Supported ordinary-image extensions are `heic`, `png`, `jpeg`, `jpg`, `webp`, and `tiff`. Native image occlusions use `rimg`. Each side is limited to 15 attachments. Emit all spans in non-overlapping ascending order and omit a formatting span that has no effective formatting.

## Native RichImage Image Occlusion

A native image-occlusion attachment uses `aes: "rimg"` and a media filename ending in `.rimg`. The file is an Apple binary property list. The builder emits the smallest legacy-compatible payload that `RichImage.decode(from:)` upgrades to current `redactRect` objects:

```text
{
  "sv": 2,
  "cv": 1,
  "oi": <original image bytes>,
  "m": [
    {
      "layoutInfo": [[x, y], [width, height]],
      "co": "#FFD60A"
    }
  ],
  "u": "<32-lowercase-hex-attachment-id>"
}
```

- `sv`: RichImage schema version.
- `cv`: Initial content version.
- `oi`: Unmodified source-image bytes.
- `m`: Non-empty legacy mask array. On decode, WinkNotes converts each item into a native rectangular redaction object.
- `layoutInfo`: CGRect property-list representation using normalized top-left coordinates in `0...1`.
- `co`: Optional legacy mask color.
- `u`: Attachment ID, equal to the media filename stem.

Do not bake masks into `oi`. Canvas size and viewport may be omitted because the decoder derives them from the embedded image and falls back to a unit viewport.

## ChoiceDocument

A choice card uses document type `2` and version `100`:

```json
{
  "version": 100,
  "question": [
    {
      "id": "32 lowercase hexadecimal characters",
      "content": {
        "type": 0,
        "payload": {
          "c": "Which statement is correct?"
        }
      },
      "children": [],
      "createdAt": 0
    }
  ],
  "options": [
    {
      "id": "32 lowercase hexadecimal characters",
      "content": {
        "type": 0,
        "payload": {
          "c": "Correct option"
        }
      },
      "children": [],
      "createdAt": 0
    },
    {
      "id": "32 lowercase hexadecimal characters",
      "content": {
        "type": 0,
        "payload": {
          "c": "Distractor"
        }
      },
      "children": [],
      "createdAt": 0
    }
  ],
  "note": [
    {
      "id": "32 lowercase hexadecimal characters",
      "content": {
        "type": 0,
        "payload": {
          "c": "Explanation"
        }
      },
      "children": [],
      "createdAt": 0
    }
  ],
  "correctOptionIDSet": [
    "ID of the correct option"
  ],
  "shuffleOptions": false,
  "type": 2
}
```

The builder emits one text-body `BlockNode` for the question, one for each option, and zero or one for the explanation. Every block ID is unique. `correctOptionIDSet` must be a non-empty subset of the option IDs; one ID represents single-choice and multiple IDs represent multiple-choice.

Choice text formatting uses `RTFPayload` spans:

```json
{
  "c": "Highlighted answer",
  "s": [
    {
      "f": 0,
      "l": 11,
      "ft": 1,
      "st": 0,
      "bc": "#FFF176"
    }
  ]
}
```

- `f`, `l`: UTF-16 range.
- `ft`: Font traits. `1` is bold and `2` is italic; this builder currently emits bold only.
- `st`: Strikethrough style; `0` or `1`.
- `c`: Optional text color.
- `bc`: Optional background/highlight color.
- `lk`: Optional absolute HTTP or HTTPS URL.

Choice cards are text-only in this version. If any choice span has `bc`, the containing `CardVO.flag` is `2` so WinkNotes recognizes occlusion content; otherwise it is `0`. `sidea` contains the question’s plain text, while `sideb` contains the option texts joined by newlines.

## Import Remapping

During import, WinkNotes reads each media filename stem as the old attachment ID, creates a new `CardAttachment`, and calls `NoteLegacyDocument.replacing(attsID:)` to replace `at` with the new UUID. The package therefore remains self-contained while imported note cards receive fresh local attachment IDs. Choice cards in this version contain no attachments and require no remapping.

## Version Sources

- `APP.documentVersion`: `6`
- `NoteLegacyDocument.version`: `3`
- `ChoiceDocument.currentVersion`: `100`
- `CardDocumentType.choice`: `2`

When either source constant changes, review the Codable models, update both scripts and this reference, then regenerate and import-test a sample package.
