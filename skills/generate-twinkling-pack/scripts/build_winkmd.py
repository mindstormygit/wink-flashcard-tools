#!/usr/bin/env python3
"""Deliver authored winkmd as a plain file or ZIP with its referenced media."""
from __future__ import annotations

import argparse
import shutil
import zipfile
from pathlib import Path
from validate_winkmd import InputError, validate


def build(source, output, media=None):
    source, output = Path(source), Path(output)
    if source.suffix.lower() != ".winkmd":
        raise InputError("source must be a .winkmd manuscript")
    info = validate(source, media)
    references = sorted({ref for _, ref in info["references"]})
    expected = ".zip" if references else ".winkmd"
    if output.suffix.lower() != expected:
        raise InputError(f"use {expected} for this manuscript")
    output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation protects previous deliverables, including a source passed as output.
    with output.open("xb") as stream:
        try:
            if references:
                root = Path(media) if media else source.parent / "media"
                with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as archive:
                    archive.write(source, source.name)
                    for ref in references:
                        archive.write(root / ref, "media/" + ref)
            else:
                with source.open("rb") as manuscript:
                    shutil.copyfileobj(manuscript, stream)
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
