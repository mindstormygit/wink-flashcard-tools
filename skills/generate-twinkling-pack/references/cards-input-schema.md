# Cards Input Schema

The builder supports two products and three selection modes:

- Automatic (default): one final card selects the standalone-card product; two or more select the pack product.
- Pack (`--product pack`): the root contains a non-empty `name`, an optional non-empty `tags` array, and a non-empty `cards` array. This can intentionally contain one card.
- Standalone card (`--product card`, or automatic mode with one card): the root contains only `cards`, with exactly one card. Do not include root `name`, root `tags`, or a card-level `tag`.

Example standalone-card input:

```json
{
  "cards": [
    {
      "front": "What does active recall test?",
      "back": "Whether the learner can retrieve an answer without seeing it."
    }
  ]
}
```

The standalone `.wink` imports into a pack chosen by the user. If more than one card is needed, build a pack instead.

## Card Types

The `cards` array may mix:

- Note cards: omit `type` or set `"type": "note"`. These use `front` and `back` and support text, ordinary images, and native image occlusion.
- Choice cards: set `"type": "choice"`. These use `question`, `options`, and an optional explanatory `note`. Read [choice-cards.md](choice-cards.md) before authoring them.

The builder preserves the input order. In pack mode, both types may reference the same pack-level tags.

## Tags

Each tag definition contains:

- `id`: Required stable reference used only in the input JSON. Use 1–64 ASCII letters, digits, hyphens, or underscores; start with a letter or digit.
- `name`: Required display name, one line and at most 200 characters.
- `parent`: Optional ID of another tag in `tags`.
- `color`: Optional `#RRGGBB`; defaults to `#29B6F6`.

IDs must be unique. Parent references may appear before or after their definitions, but must exist and must not form a cycle. Sibling tags must not resolve to the same name. Hierarchies may be at most 32 levels deep.

Each note card must contain `front` and `back`, plus an optional `tag` containing one tag ID. WinkNotes currently assigns at most one tag to a card. A card that omits `tag` is imported as untagged.

Each side may be either:

- A non-empty string for unformatted text.
- A non-empty array containing text, ordinary-image, and/or native image-occlusion segments. The builder concatenates them in order and inserts attachments inline at their segment positions.

## Text Segments

A text segment requires `text`. Add only the formatting fields needed:

- `bold`: Boolean.
- `highlight`: Boolean for the default mark-pen color, or a `#RRGGBB` string for a custom color.
- `textColor`: `#RRGGBB`.
- `underline`: Boolean.
- `strikethrough`: Boolean.
- `script`: `superscript` or `subscript`.
- `link`: Absolute HTTP or HTTPS URL.

## Image Segments

An image segment contains exactly one field:

- `image`: A non-empty local path to a HEIC, PNG, JPEG/JPG, WebP, or TIFF file.

Relative paths resolve from the directory containing the cards JSON file. Absolute paths are also accepted. Remote HTTP URLs are not accepted; download the image to a local file first. Put any caption or source note in an adjacent text segment. Each image occurrence becomes a separate attachment, even when the same source file is reused. A card side may contain at most 15 images.

## Native Image-Occlusion Segments

A native image occlusion contains exactly one `richImage` object:

```json
{
  "richImage": {
    "image": "images/cell-diagram.png",
    "masks": [
      {
        "x": 0.12,
        "y": 0.24,
        "width": 0.20,
        "height": 0.08,
        "color": "#FFD60A"
      },
      {
        "x": 0.60,
        "y": 0.48,
        "width": 0.18,
        "height": 0.07
      }
    ]
  }
}
```

- `image`: Local source-image path, with the same path and file-type rules as an ordinary image segment.
- `masks`: Non-empty array of rectangular redactions; at most 200 per RichImage.
- `x`, `y`, `width`, `height`: Normalized image coordinates in `0...1`, measured from the top-left. Width and height must be positive, and every rectangle must fit inside the image.
- `color`: Optional `#RRGGBB` legacy mask color. Omit it unless a specific mask color is useful.

The builder embeds the original image and redaction rectangles in one native binary-plist `.rimg` file. Do not pre-draw or bake the masks into the source image. An occlusion segment counts as one attachment toward the 15-attachment side limit.

Do not calculate offsets or add internal WinkNotes keys. The builder converts segment boundaries to UTF-16 `f/l` ranges, combines style bits, creates attachment IDs, serializes native RichImages, copies media into `media/`, and omits spans from unformatted text.

## Example

```json
{
  "name": "操作系统基础",
  "tags": [
    {
      "id": "core",
      "name": "核心概念",
      "color": "#29B6F6"
    },
    {
      "id": "memory",
      "name": "内存管理",
      "parent": "core",
      "color": "#08BF54"
    },
    {
      "id": "packaging",
      "name": "封装工艺",
      "color": "#BA68C8"
    }
  ],
  "cards": [
    {
      "front": "什么是进程？",
      "back": [
        {
          "text": "进程",
          "bold": true,
          "highlight": true
        },
        {
          "text": "是正在执行的程序实例，拥有独立的执行状态和系统资源。"
        }
      ],
      "tag": "core"
    },
    {
      "front": [
        {
          "text": "虚拟内存",
          "bold": true,
          "textColor": "#0066CC"
        },
        {
          "text": "解决了什么问题？"
        }
      ],
      "back": [
        {
          "text": "它让进程使用统一且可能大于物理内存的地址空间，并提供隔离。"
        },
        {
          "text": "\n来源：第 12 页",
          "link": "https://example.com/source.pdf"
        }
      ],
      "tag": "memory"
    },
    {
      "front": "观察下图：传统封装中芯片与基板如何连接？",
      "back": [
        {
          "text": "结构示意：\n",
          "bold": true
        },
        {
          "image": "images/package-cross-section.png"
        },
        {
          "text": "\n芯片通过键合线或凸点与基板建立电气连接。"
        }
      ],
      "tag": "packaging"
    },
    {
      "front": [
        {
          "text": "根据图像回忆被遮挡的细胞结构：\n",
          "bold": true
        },
        {
          "richImage": {
            "image": "images/cell-diagram.png",
            "masks": [
              {
                "x": 0.18,
                "y": 0.31,
                "width": 0.22,
                "height": 0.09
              }
            ]
          }
        }
      ],
      "back": "答案：线粒体。",
      "tag": "core"
    }
  ]
}
```

The builder converts tag IDs and parent references into the internal hierarchical paths expected by `TagVO`; never put WinkNotes' `/$-#-$/` separator in the input. It rejects duplicate IDs or paths, missing parents, cycles, undefined card tags, malformed colors or links, unknown fields, invalid images or RichImage masks, more than 15 attachments on one side, whitespace-only content, exact duplicate cards, invalid JSON, and an existing output path. Inputs without `tags` remain valid.
