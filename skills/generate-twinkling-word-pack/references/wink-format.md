# Word Pack Wink Format

Use this reference only when maintaining or debugging the serializer.

## Container

- Unencrypted ZIP with extension `.wink`.
- `content.json` is the first and only archive entry.
- UTF-8 JSON without a byte-order mark.

## Pack

The pack uses `CardPackVO.version = 6`. Its Base64 `userInfo` decodes to:

```json
{
  "wordPackInfo": true,
  "wordPackLanguageCode": "en"
}
```

This makes the imported pack a native word pack. Optional tags use the same hierarchical `TagVO` paths as other Wink packs.

## Card

Each `CardVO` has:

```json
{
  "uuid": "32 lowercase hexadecimal characters",
  "sidea": "resilient",
  "sideb": "adj. 能迅速恢复的；有适应力的",
  "flag": 0,
  "rtf": "Base64-encoded WordDocument JSON",
  "sideaAttIds": [],
  "sidebAttIds": [],
  "version": 6
}
```

`sidea` equals `WordDocument.word`; `sideb` equals `WordDocument.definition`.

## WordDocument

Decoded `rtf`:

```json
{
  "version": 100,
  "type": 3,
  "word": "resilient",
  "phonetic": "/rɪˈzɪliənt/",
  "definition": "adj. 能迅速恢复的；有适应力的",
  "examples": [
    {
      "id": "32 lowercase hexadecimal characters",
      "sentence": "The system is resilient to temporary failures.",
      "translation": "该系统能够从暂时性故障中迅速恢复。"
    }
  ],
  "langCode": "en",
  "extras": [
    {
      "id": "32 lowercase hexadecimal characters",
      "label": "音节",
      "content": "re·sil·ient",
      "templateKey": "en.syllable"
    }
  ]
}
```

Custom extras omit `templateKey`.

## Version Sources

- `APP.documentVersion`: `6`
- `WordDocument.currentVersion`: `100`
- `CardDocumentType.word`: `3`
