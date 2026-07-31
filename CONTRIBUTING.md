# Contributing

Contributions that improve format accuracy, validation, documentation, examples, or card-authoring quality are welcome.

## Before opening a pull request

1. Keep each Skill independently distributable. References required at runtime must remain inside that Skill directory.
2. Do not hand-author Base64 document payloads or ZIP internals when a bundled builder can produce them.
3. Add or update validation for every serializer change.
4. Validate all included example packs.
5. Do not include copyrighted study materials, private user data, credentials, or internal application source code.

Run the local checks:

```bash
python3 skills/generate-twinkling-pack/scripts/validate_wink.py \
  skills/generate-twinkling-pack/examples/example-pack.wink

python3 skills/generate-twinkling-pack/scripts/validate_wink.py \
  skills/generate-twinkling-pack/examples/example-mixed-pack.wink

python3 skills/generate-twinkling-pack/scripts/validate_wink.py \
  skills/generate-twinkling-pack/examples/example-card.wink

python3 skills/generate-twinkling-word-pack/scripts/validate_word_wink.py \
  skills/generate-twinkling-word-pack/examples/example-word-pack.wink

python3 skills/generate-twinkling-word-pack/scripts/validate_word_wink.py \
  skills/generate-twinkling-word-pack/examples/example-word-card.wink

python3 scripts/package_skills.py
```

Format changes must remain compatible with the current WinkNotes Codable models and should include a clear changelog entry.
