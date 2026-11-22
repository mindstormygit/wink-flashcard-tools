# Input Schema

Write one UTF-8 JSON object:

```json
{
  "name": "英语学术词汇",
  "langCode": "en",
  "tags": [
    {
      "id": "core",
      "name": "核心词汇",
      "color": "#29B6F6"
    }
  ],
  "words": [
    {
      "word": "resilient",
      "phonetic": "/rɪˈzɪliənt/",
      "definition": "adj. 能迅速恢复的；有适应力的",
      "examples": [
        {
          "sentence": "The system is resilient to temporary failures.",
          "translation": "该系统能够从暂时性故障中迅速恢复。"
        }
      ],
      "extras": [
        {
          "label": "音节",
          "content": "re·sil·ient",
          "templateKey": "en.syllable"
        }
      ],
      "tag": "core"
    }
  ]
}
```

## Root

- `name`: Required non-empty pack name in the pack product.
- `langCode`: Required; one of `en`, `ja`, `ko`, `de`, `fr`, `es`, `pt`, or `it`.
- `words`: Required non-empty array; at most 5,000 entries.
- `tags`: Optional non-empty array in the pack product.

The default product selection is automatic: one final word becomes a standalone card, while two or more become a pack. Pass `--product pack` to force a pack, including a one-word pack. Pass `--product card` to explicitly require one standalone card.

For a standalone word card, provide exactly one item in `words`. Do not include `name`, `tags`, or the word-level `tag`:

```json
{
  "langCode": "en",
  "words": [
    {
      "word": "resilient",
      "definition": "adj. 能迅速恢复的；有适应力的"
    }
  ]
}
```

The standalone `.wink` imports into a pack chosen by the user. Multiple words automatically use the pack product.

## Word

- `word`: Required non-empty single-line word or phrase, at most 200 characters.
- `phonetic`: Optional single-line pronunciation, at most 500 characters. Omitted values become an empty string.
- `definition`: Required non-empty definition, at most 10,000 characters.
- `examples`: Optional array with at most five objects.
- `extras`: Optional array with at most twenty objects.
- `tag`: Optional input tag ID.

Words are considered duplicates after trimming and Unicode case folding.

## Example

Each example contains exactly:

- `sentence`: Required non-empty source-language sentence, at most 2,000 characters.
- `translation`: Required string, at most 2,000 characters. It may be empty only when a reliable translation is unavailable.

## Extra Field

- `label`: Required non-empty single-line label, at most 100 characters.
- `content`: Required non-empty content, at most 2,000 characters.
- `templateKey`: Optional language-template key listed in [word-authoring.md](word-authoring.md).

Template keys must match the pack language and may appear at most once per word. A custom field omits `templateKey`.

## Tags

Each tag contains:

- `id`: Stable input ID using 1–64 ASCII letters, digits, hyphens, or underscores.
- `name`: Display name, one line and at most 200 characters.
- `parent`: Optional parent tag ID.
- `color`: Optional `#RRGGBB`; defaults to `#29B6F6`.

Tag IDs and resolved paths must be unique. Parent references must exist and may not form cycles. Hierarchies are limited to 32 levels. Each word may use at most one tag.
