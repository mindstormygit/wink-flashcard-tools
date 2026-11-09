# Contributing

Keep each Skill independently distributable. The note Skill authors `.winkmd` dialect v2; the word Skill continues to build legacy `.wink`. Do not include private user data, internal App source, credentials or copyrighted study materials.

Use supported v2 authoring syntax, not internal document trees, Base64 payloads or IDs. When changing delivery scripts, test packaging and validation and import the resulting manuscript in the App. The lightweight Python validator does not replace the App's rich-document validation.

```bash
python3 -m unittest discover -s tests -v
python3 skills/generate-twinkling-pack/scripts/validate_winkmd.py skills/generate-twinkling-pack/examples/example-pack.winkmd
python3 skills/generate-twinkling-pack/scripts/validate_winkmd.py skills/generate-twinkling-pack/examples/example-card.winkmd
python3 skills/generate-twinkling-pack/scripts/validate_winkmd.py skills/generate-twinkling-pack/examples/example-media.zip
python3 skills/generate-twinkling-word-pack/scripts/validate_word_wink.py skills/generate-twinkling-word-pack/examples/example-word-pack.wink
python3 skills/generate-twinkling-word-pack/scripts/validate_word_wink.py skills/generate-twinkling-word-pack/examples/example-word-card.wink
python3 scripts/package_skills.py
```

Update examples and changelog when changing the format or authoring workflow. GitHub release publishing still requires an explicitly requested release/tag.
