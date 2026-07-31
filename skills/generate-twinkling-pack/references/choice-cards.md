# Choice Cards

Use a choice card when the learner should distinguish among plausible alternatives. Note cards and choice cards may appear together in the same `cards` array and use the same pack-level tags.

## Input Shape

```json
{
  "type": "choice",
  "question": [
    {
      "text": "关于半导体封装，哪些说法正确？",
      "bold": true
    }
  ],
  "options": [
    {
      "content": "封装可以保护芯片并建立外部电气连接。",
      "correct": true
    },
    {
      "content": "所有封装都不需要基板。",
      "correct": false
    },
    {
      "content": "封装会影响散热与信号完整性。",
      "correct": true
    }
  ],
  "note": [
    {
      "text": "解析：",
      "bold": true
    },
    {
      "text": "封装同时承担机械保护、电气连接和热管理等作用。"
    }
  ],
  "tag": "packaging"
}
```

- `type`: Must be `choice`.
- `question`: Required non-empty string or non-empty text-segment array.
- `options`: Required array containing 2–26 option objects.
- `options[].content`: Required non-empty string or non-empty text-segment array.
- `options[].correct`: Required Boolean. Exactly one `true` creates a single-choice card; two or more create a multiple-choice card.
- `note`: Optional explanation as a non-empty string or text-segment array.
- `tag`: Optional pack-level tag ID.

Option text must be unique within a card. At least one option must be correct. Do not prefix options with `A.` or `B.`; WinkNotes supplies option labels.

## Formatting

Choice questions, options, and notes support:

- `bold`
- `highlight`
- `textColor`
- `strikethrough`
- `link`

Their values and color/link rules match the text segments in [cards-input-schema.md](cards-input-schema.md). Choice cards do not support `underline`, `script`, `image`, or `richImage` in this version.

## Authoring

- Use a note card for free recall and explanation; use a choice card when discrimination among nearby concepts is the skill being tested.
- Keep one decision target per question.
- Make distractors plausible, source-grounded, grammatically parallel, and mutually distinct.
- Avoid clues such as one unusually long option, repeated wording from the stem, or visible formatting that marks the correct answer.
- State whether multiple answers are expected when the wording could be ambiguous, for example “以下哪些说法正确？”
- Add a concise explanation in `note`, especially when a distractor represents a common misconception.
- Do not turn every recall fact into a choice question. Recognition is usually easier than unaided recall.

## Mixed-Pack Example

```json
{
  "name": "混合复习卡包",
  "tags": [
    {
      "id": "core",
      "name": "核心概念",
      "color": "#29B6F6"
    }
  ],
  "cards": [
    {
      "type": "note",
      "front": "封装的三个核心作用是什么？",
      "back": "机械保护、电气连接与热管理。",
      "tag": "core"
    },
    {
      "type": "choice",
      "question": "下列哪一项属于封装的核心作用？",
      "options": [
        {
          "content": "热管理",
          "correct": true
        },
        {
          "content": "晶圆曝光",
          "correct": false
        }
      ],
      "note": "封装需要把芯片产生的热量有效导出。",
      "tag": "core"
    },
    {
      "type": "choice",
      "question": "下列哪些因素可能受封装设计影响？",
      "options": [
        {
          "content": "散热",
          "correct": true
        },
        {
          "content": "信号完整性",
          "correct": true
        },
        {
          "content": "机械可靠性",
          "correct": true
        },
        {
          "content": "光刻胶显影",
          "correct": false
        }
      ],
      "note": "前三项都与芯片封装结构和材料有关。",
      "tag": "core"
    }
  ]
}
```
