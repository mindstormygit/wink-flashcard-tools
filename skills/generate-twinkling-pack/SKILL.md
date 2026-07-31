---
name: generate-twinkling-pack
description: Generate importable, unencrypted WinkNotes .wink standalone flashcards or flashcard packs from PDFs, documents, notes, images, webpages, or other source material. Use when an agent needs to create one front/back NoteLegacyDocument or ChoiceDocument card for import into an existing pack, or a mixed pack of note and single- or multiple-answer choice cards, with optional pack-level hierarchical tags, rich-text formatting, ordinary inline images, or native RichImage image-occlusion attachments. Also use when a user asks what this skill can do, how to install, share, or use it, or requests example prompts or troubleshooting. This version excludes word cards, media inside choice cards, freehand rich-image drawings, audio, and other attachment types.
---

# Generate WinkNotes Cards and Packs

Create either one standalone card for import into an existing pack or a source-grounded pack of recall and recognition cards. Choose front/back notes or single-/multiple-answer choices according to the learning objective. Packs may use a compact tag taxonomy; both products support restrained rich-text formatting, useful inline images, and native image occlusions where the card type permits them. Use the bundled scripts to serialize and validate the `.wink` artifact. Never hand-author `content.json`, `.rimg` property lists, internal tag paths, span offsets, attachment IDs, style bitmasks, or Base64 `rtf` values.

## Help and Onboarding

When the user asks how to install or use this skill, what inputs it accepts, what it can generate, how to share it, or why it is not being discovered, read [user-guide.zh-CN.md](references/user-guide.zh-CN.md) and answer the help request before starting card or pack generation. Offer one or two copyable prompts tailored to the user's source. Do not require the user to understand the internal cards JSON or `.wink` format.

## Workflow

1. Determine the requested product.
   - If the user explicitly requests a card pack, build a pack even when it contains one card.
   - If the user explicitly requests one standalone `.wink` card, build a standalone card and require exactly one card.
   - Treat generic wording such as "make flashcards from this PDF" as unspecified. After drafting, build a standalone card when the final count is one; build a pack when it is two or more.
   - Standalone cards do not have a pack name or tags. WinkNotes asks the user to choose the destination pack during import.
2. Read the source completely enough to identify its structure and central ideas.
   - For a PDF, use an available PDF extraction or OCR capability first.
   - Ignore repeated headers, footers, page numbers, and OCR noise.
   - Extract or download only images that materially improve recall, and save them as local image files.
3. Read [card-authoring-guidelines.md](references/card-authoring-guidelines.md), then draft atomic cards and select the card type that best tests each objective.
   - Honor a requested card count.
   - If no count is provided, cover the high-value material without mechanically converting every paragraph.
   - Do not add facts that are not supported by the source.
   - Prefer front/back note cards for free recall, explanation, images, and image occlusion.
   - Use choice cards when distinguishing plausible alternatives is itself valuable; write credible distractors and an explanatory note.
   - For a pack, add a small hierarchy of reusable tags when it improves navigation or focused review.
4. Read [cards-input-schema.md](references/cards-input-schema.md). When the artifact contains a choice, also read [choice-cards.md](references/choice-cards.md). Then write the matching UTF-8 JSON input file.
5. Resolve script paths relative to this `SKILL.md`, then build the selected product:

   ```bash
   # Unspecified product: one final card becomes a card; two or more become a pack
   python3 <skill-dir>/scripts/build_wink.py <cards.json> <output.wink>

   # Explicit pack, including a one-card pack
   python3 <skill-dir>/scripts/build_wink.py <cards.json> <output.wink> --product pack

   # Explicit standalone card
   python3 <skill-dir>/scripts/build_wink.py <card.json> <output.wink> --product card
   ```

6. Always validate the completed artifact:

   ```bash
   python3 <skill-dir>/scripts/validate_wink.py <output.wink>
   ```

7. Deliver the validated `.wink` file and identify it as a standalone card or pack.
   - For a standalone card, report its card type, choice-option count when applicable, total span count, image-attachment count, native RichImage count, and image-occlusion count.
   - For a pack, also report its pack name, total card count, note-card count, choice-card count, single-/multiple-choice count, tag count, and tagged-card count.

## Constraints

- Generate front/back `NoteLegacyDocument` cards and text-only `ChoiceDocument` cards as one standalone card or together in any order in a pack.
- A standalone-card product contains exactly one root `CardVO`. It has no pack name or tag; WinkNotes assigns its destination pack and import tag during import.
- A choice card must contain 2–26 unique options and at least one correct option. One correct option makes it single-choice; multiple correct options make it multiple-choice.
- Choice questions, options, and explanations support text formatting described in the choice-card reference, but do not support `image` or `richImage` segments in this version.
- In pack products, assign at most one tag to each card. Tags may form a hierarchy and are optional.
- Reference tags by input ID; let the build script generate WinkNotes' internal hierarchical paths.
- Support ordinary inline images and rectangular native image occlusions. Source images may be HEIC, PNG, JPEG/JPG, WebP, or TIFF.
- Never simulate image occlusion by baking colored blocks into a PNG or by putting a masked image on the front and an unmasked image on the back. Use a `richImage` segment so WinkNotes receives one native `.rimg` attachment with interactive redaction objects.
- Do not emit freehand rich-image drawings, ellipse/polygon occlusions, audio, video, or pasted Base64 attachment data.
- Use local image paths in the input JSON. Relative paths resolve from the JSON file's directory; do not place remote URLs in `image` or `richImage.image`.
- Limit each card side to at most 15 images.
- Let the build script compute all UTF-16 span locations and lengths, attachment IDs, and media filenames.
- Create an unencrypted ZIP with `content.json` first at its root and, when needed, image files under `media/`. `content.json` contains one root `CardVO` for a standalone card or one root `CardPackVO` for a pack.
- Treat Markdown markers as literal text; express supported formatting through segment fields.
- Use highlight deliberately: WinkNotes treats mark-pen highlighting as occlusion content during analysis.
- Refuse to deliver an artifact when validation fails.
- Do not overwrite an existing output file; choose a new path or obtain explicit permission first.

## Format Maintenance

Read [wink-format.md](references/wink-format.md) only when changing the serializer or investigating compatibility. Keep its version constants synchronized with the WinkNotes Codable models.
