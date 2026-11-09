#!/usr/bin/env python3
"""Deliver authored winkmd as a plain file or ZIP with its referenced media."""
from __future__ import annotations

import argparse
import zipfile
from pathlib import Path
from validate_winkmd import HEADER_LINE, InputError, validate

# Written into every delivered header so a later App can suggest updating an old Skill.
# Keep in step with the top version in this Skill's CHANGELOG.md (a test checks it).
GENERATOR = "generate-twinkling-pack 2.0.0"


def stamp(text):
    """Return the manuscript with `generator: GENERATOR` in its header, adding a header if there is none."""
    lines = text.lstrip("﻿").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    if lines[0] == "---" and len(lines) > 1 and HEADER_LINE.match(lines[1]):
        end = lines.index("---", 1)
        header = [line for line in lines[1:end] if line.split(":", 1)[0].strip() != "generator"]
        return "\n".join(["---", *header, f"generator: {GENERATOR}", *lines[end:]])
    return f"---\nwink_md_version: 2\ngenerator: {GENERATOR}\n---\n\n" + "\n".join(lines)


def build(source, output, media=None):
    source, output = Path(source), Path(output)
    if source.suffix.lower() != ".winkmd":
        raise InputError("source must be a .winkmd manuscript")
    info = validate(source, media)
    references = sorted({ref for _, ref in info["references"]})
    expected = ".zip" if references else ".winkmd"
    if output.suffix.lower() != expected:
        raise InputError(f"use {expected} for this manuscript")
    manuscript = stamp(source.read_text(encoding="utf-8")).encode("utf-8")
    output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation protects previous deliverables, including a source passed as output.
    with output.open("xb") as stream:
        try:
            if references:
                root = Path(media) if media else source.parent / "media"
                with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as archive:
                    archive.writestr(source.name, manuscript)
                    for ref in references:
                        archive.write(root / ref, "media/" + ref)
            else:
                stream.write(manuscript)
        except BaseException:
            output.unlink(missing_ok=True)
            raise
    try:
        validate(output)
    except BaseException:
        output.unlink(missing_ok=True)
        raise
    return info


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manuscript", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--media", type=Path)
    args = parser.parse_args()
    try:
        result = build(args.manuscript, args.output, args.media)
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        parser.exit(1, f"Cannot build: {error}\n")
    print(f"Created {args.output}: {result['cards']} cards, {len(result['references'])} attachment occurrences")


if __name__ == "__main__":
    main()
