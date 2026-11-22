# Card Authoring Guidelines

## Grounding

- Use only claims supported by the source.
- Omit unreadable or ambiguous material instead of guessing.
- Preserve qualifiers, units, conditions, negations, and exceptions.
- Add a short page or section reference to the back when it materially aids verification.

## Card Shape

- Test one idea per card.
- Make the front answerable without hidden context such as “this,” “the above,” or an unexplained acronym.
- Keep the back concise but sufficient to distinguish the correct idea from nearby concepts.
- Prefer recall questions over yes/no questions.
- Split lists when individual items deserve independent recall; keep a list together when the relationship among its items is the learning target.
- Remove exact and near-duplicate cards.

## Choosing a Card Type

- Use a front/back note card when the learner should produce an answer without cues, explain a mechanism, reconstruct a process, inspect an image, or recall a hidden label.
- Use a choice card when distinguishing plausible alternatives, exceptions, classifications, or common misconceptions is the learning objective.
- Keep a deliberate mix: recognition questions should supplement rather than replace free recall.
- A pack may freely mix both card types and assign either type to the same tag hierarchy.

## Choice Cards

- Write one clear decision target per question.
- Use exactly one correct option for single-choice and multiple correct options only when the wording clearly signals “哪些” or otherwise makes multiple answers expected.
- Make distractors plausible from the source or from nearby concepts; do not invent bizarre alternatives merely to fill the list.
- Keep options grammatically parallel and similar in scope and length.
- Avoid “all of the above,” “none of the above,” overlapping options, double negatives, and formatting that reveals the answer.
- Do not duplicate option text. Include at least two options and at least one correct answer.
- Add a concise explanatory note that states why the correct option is correct and, when useful, why a tempting distractor is wrong. Attach per-question explanations inline with `:::explanation` after the last option (unmuted); reserve `<!-- back -->` for card-level notes or when targeting an earlier v2 build without inline explanations.
- Omit `shuffle` on `:::choice` so the pack's shuffle setting applies; add `:::choice{shuffle=false}` only when option order carries meaning (such as ordered steps or position-dependent options).
- Do not prefix option content with letters or numbers; WinkNotes displays option labels.

## Formatting

- Use plain text when formatting adds no learning value.
- Use bold for a term, condition, or conclusion that deserves visual emphasis.
- Use `{{cloze}}` only for the words the learner should recall; WinkNotes covers them until revealed.
- Use text color sparingly to distinguish categories, warnings, or contrasted concepts.
- Use underline and strikethrough only when their conventional meaning is clear.
- Use super/subscript for compact scientific or mathematical notation.
- Use links only for genuinely useful source or reference destinations.
- Do not style an entire card by default; style the smallest meaningful phrase.
- Write dialect-v2 Markdown directly; use mute for translations/notes and collapsed details for hints.
- Use a small table when its row/column relationships are the learning objective.

## Images

- Include an image only when recognizing a diagram, structure, spatial relationship, visual distinction, or labeled component is part of the learning goal.
- Prefer a focused crop or one clear diagram over a decorative screenshot of an entire page.
- New cards use ordinary images. Preserve supplied `.rimg` when revising a manuscript; do not create new image occlusion or bake masks into an image.
- Keep the question answerable: state what the learner should inspect instead of relying on “the image above.”
- Put a short caption, orientation cue, or source note in adjacent text when it prevents ambiguity.
- Preserve labels and resolution needed to answer the question; do not use an unreadably small image.
- Avoid adding images that merely repeat the complete written answer.
- Use images the user supplied or is authorized to reuse, and preserve source attribution when appropriate.

## Tags

- Use tags for recurring subject areas that make filtering or focused review useful.
- Prefer a compact taxonomy over one tag per card; three to eight meaningful categories is usually enough for a small pack.
- Add hierarchy only when both the parent category and its children help navigation.
- Assign the most specific useful tag to a card; the imported hierarchy preserves its parent context.
- Use stable, concise display names and consistent colors for related categories.
- Do not use tags as a substitute for writing a self-contained question.

## Coverage

- Prioritize definitions, mechanisms, cause-and-effect relationships, contrasts, procedures, constraints, and conclusions.
- Skip decorative examples and repeated explanations unless they add a distinct testable idea.
- When the user does not request a count, choose a compact set that covers the source’s important ideas rather than one card per paragraph.
