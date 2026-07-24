---
name: generate-twinkling-pack
description: Generate importable, unencrypted TwinklingCard .wink flashcard packs from PDFs, documents, notes, images, webpages, or other source material. Use when an agent needs to turn source content into a mixed pack of front/back NoteLegacyDocument cards and single- or multiple-answer ChoiceDocument cards, with optional hierarchical tags, rich-text formatting, ordinary inline images, or native RichImage image-occlusion attachments. Also use when a user asks what this skill can do, how to install, share, or use it, or requests example prompts or troubleshooting. This version excludes word cards, media inside choice cards, freehand rich-image drawings, audio, and other attachment types.
---

# Generate Twinkling Pack

Create a source-grounded set of recall and recognition cards, choosing front/back notes or single-/multiple-answer choices according to the learning objective. Optionally apply a compact tag taxonomy, restrained rich-text formatting, useful inline images, and native image occlusions, then use the bundled scripts to serialize and validate the `.wink` package. Both card types may coexist in one pack and share its tags. Never hand-author `content.json`, `.rimg` property lists, internal tag paths, span offsets, attachment IDs, style bitmasks, or Base64 `rtf` values.

## Help and Onboarding

When the user asks how to install or use this skill, what inputs it accepts, what it can generate, how to share it, or why it is not being discovered, read [user-guide.zh-CN.md](references/user-guide.zh-CN.md) and answer the help request before starting pack generation. Offer one or two copyable prompts tailored to the user's source. Do not require the user to understand the internal cards JSON or `.wink` format.

## Workflow

1. Read the source completely enough to identify its structure and central ideas.
   - For a PDF, use an available PDF extraction or OCR capability first.
   - Ignore repeated headers, footers, page numbers, and OCR noise.
   - Extract or download only images that materially improve recall, and save them as local image files.
2. Read [card-authoring-guidelines.md](references/card-authoring-guidelines.md), then draft atomic cards and select the card type that best tests each objective.
   - Honor a requested card count.
   - If no count is provided, cover the high-value material without mechanically converting every paragraph.
   - Do not add facts that are not supported by the source.
   - Prefer front/back note cards for free recall, explanation, images, and image occlusion.
   - Use choice cards when distinguishing plausible alternatives is itself valuable; write credible distractors and an explanatory note.
   - Add a small hierarchy of reusable tags when it improves navigation or focused review.
3. Read [cards-input-schema.md](references/cards-input-schema.md). When the pack contains choices, also read [choice-cards.md](references/choice-cards.md). Then write a UTF-8 JSON input file containing the pack name, optional tags, and cards.
4. Resolve script paths relative to this `SKILL.md`, then build the pack:

   ```bash
   python3 <skill-dir>/scripts/build_wink.py <cards.json> <output.wink>
   ```

5. Always validate the completed artifact:

   ```bash
   python3 <skill-dir>/scripts/validate_wink.py <output.wink>
   ```

6. Deliver the validated `.wink` file and report its pack name, total card count, note-card count, choice-card count, single-/multiple-choice count, choice-option count, total span count, image-attachment count, native RichImage count, image-occlusion count, tag count, and tagged-card count.

## Constraints

- Generate front/back `NoteLegacyDocument` cards and text-only `ChoiceDocument` cards. They may coexist in any order in one pack.
- A choice card must contain 2–26 unique options and at least one correct option. One correct option makes it single-choice; multiple correct options make it multiple-choice.
- Choice questions, options, and explanations support text formatting described in the choice-card reference, but do not support `image` or `richImage` segments in this version.
- Assign at most one tag to each card. Tags may form a hierarchy and are optional.
- Reference tags by input ID; let the build script generate Wink's internal hierarchical paths.
- Support ordinary inline images and rectangular native image occlusions. Source images may be HEIC, PNG, JPEG/JPG, WebP, or TIFF.
- Never simulate image occlusion by baking colored blocks into a PNG or by putting a masked image on the front and an unmasked image on the back. Use a `richImage` segment so Wink receives one native `.rimg` attachment with interactive redaction objects.
- Do not emit freehand rich-image drawings, ellipse/polygon occlusions, audio, video, or pasted Base64 attachment data.
- Use local image paths in the input JSON. Relative paths resolve from the JSON file's directory; do not place remote URLs in `image` or `richImage.image`.
- Limit each card side to at most 15 images.
- Let the build script compute all UTF-16 span locations and lengths, attachment IDs, and media filenames.
- Create an unencrypted ZIP with `content.json` first at its root and, when needed, image files under `media/`.
- Treat Markdown markers as literal text; express supported formatting through segment fields.
- Use highlight deliberately: TwinklingCard treats mark-pen highlighting as occlusion content during analysis.
- Refuse to deliver a package when validation fails.
- Do not overwrite an existing output file; choose a new path or obtain explicit permission first.

## Format Maintenance

Read [wink-format.md](references/wink-format.md) only when changing the serializer or investigating compatibility. Keep its version constants synchronized with the TwinklingCard Codable models.
