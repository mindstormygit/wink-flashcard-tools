# Word Authoring

## General Quality

- Write for a Chinese-speaking learner unless the user requests another definition language.
- Preserve the canonical spelling the learner should memorize.
- Prefer the common contextual meaning over an exhaustive dictionary entry.
- Separate meanings by part of speech and line:

  ```text
  n. 恢复力；韧性
  adj. 能迅速恢复的；有适应力的
  ```

- Keep definitions concise enough to review but specific enough to distinguish nearby words.
- Use one or two natural, self-contained examples. Translate the intended meaning rather than every surface word mechanically.
- Do not create an example that requires an unlisted rare sense.
- Omit doubtful optional data. If the core meaning itself is doubtful, skip the word and tell the user.
- Do not claim a dictionary, corpus, CEFR level, frequency, or etymology unless the user supplied it.

## Pronunciation

Pronunciation is AI-authored and can be error-prone. Use a conventional, internally consistent form:

- English: Prefer IPA for one requested variety. If both are useful, label them, such as `US /.../ | UK /.../`.
- Japanese: Use kana with pitch-accent number when confident, optionally followed by romaji.
- Korean: Use the standard pronunciation, optionally followed by romanization.
- German, French, Spanish, Portuguese, Italian: Prefer IPA.

Do not invent a precise IPA or pitch-accent value when unsure. An empty pronunciation is safer than a confident-looking error.

## Language Templates

Use these `templateKey` values only for the matching language:

| Language | Template key | Label |
| --- | --- | --- |
| English | `en.syllable` | 音节 |
| Japanese | `ja.kana` | 假名 |
| Japanese | `ja.romaji` | 罗马音 |
| Japanese | `ja.accent` | 音调 |
| Korean | `ko.romanization` | 罗马音 |
| German | `de.article` | 冠词 |
| German | `de.plural_form` | 复数形式 |
| French | `fr.article` | 冠词 |
| French | `fr.plural_form` | 复数形式 |
| Spanish | `es.article` | 冠词 |
| Spanish | `es.plural_form` | 复数形式 |
| Portuguese | `pt.article` | 冠词 |
| Portuguese | `pt.plural_form` | 复数形式 |
| Italian | `it.article` | 冠词 |
| Italian | `it.plural_form` | 复数形式 |

Custom fields may omit `templateKey`. Add them sparingly; common useful examples are “搭配” or “易混词”. Do not duplicate the definition in extras.

## Extraction from Sources

- Prefer terms that carry the source's central ideas or recur in important passages.
- Keep phrases when their meaning is not compositional, such as `take into account`.
- Use the surrounding sentence to select the intended sense.
- Do not include names, boilerplate, OCR fragments, or words the learner clearly already knows merely to reach a count.
- When the user requests a fixed count, prioritize useful coverage and report when the source does not support that many good entries.
