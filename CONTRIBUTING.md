# Contributing

Keep the unified Skill `generate-twinkling-pack` self-contained and independently distributable. Note and choice cards author dialect-v2 `.winkmd` (or media ZIPs); native word cards build `.wink` (`WordDocument`) files via the bundled scripts. Do not include private user data, internal App source, credentials, or copyrighted study materials.

For note and choice cards, use supported v2 authoring syntax rather than internal document trees, Base64 payloads, or IDs. When changing delivery scripts, test packaging and validation and import the resulting file in the App. The lightweight Python `.winkmd` validator does not replace the App's full rich-document validation.

```bash
python3 -m unittest discover -s tests -v
python3 skills/generate-twinkling-pack/scripts/validate_winkmd.py skills/generate-twinkling-pack/examples/example-pack.winkmd
python3 skills/generate-twinkling-pack/scripts/validate_winkmd.py skills/generate-twinkling-pack/examples/example-card.winkmd
python3 skills/generate-twinkling-pack/scripts/validate_winkmd.py skills/generate-twinkling-pack/examples/example-media.zip
python3 skills/generate-twinkling-pack/scripts/validate_word_wink.py skills/generate-twinkling-pack/examples/example-word-pack.wink
python3 skills/generate-twinkling-pack/scripts/validate_word_wink.py skills/generate-twinkling-pack/examples/example-word-card.wink
python3 scripts/package_skills.py
```

Update examples and changelogs when changing the format or authoring workflow. GitHub release publishing still requires an explicitly requested release/tag.
