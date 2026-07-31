#!/usr/bin/env python3
"""Create reproducible release ZIP files for both WinkNotes Skills."""

from __future__ import annotations

import argparse
import stat
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = (
    "generate-twinkling-pack",
    "generate-twinkling-word-pack",
)
IGNORED_NAMES = {".DS_Store", "__pycache__"}
FIXED_TIMESTAMP = (2026, 1, 1, 0, 0, 0)


def included_files(skill_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in skill_dir.rglob("*")
        if path.is_file()
        and not any(part in IGNORED_NAMES for part in path.parts)
        and path.suffix not in {".pyc", ".pyo"}
    )


def write_archive(skill_name: str, output_dir: Path) -> Path:
    skill_dir = ROOT / "skills" / skill_name
    if not (skill_dir / "SKILL.md").is_file():
        raise SystemExit(f"Missing Skill entry point: {skill_dir / 'SKILL.md'}")

    output_path = output_dir / f"{skill_name}.zip"
    with zipfile.ZipFile(
        output_path,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for source_path in included_files(skill_dir):
            relative = source_path.relative_to(skill_dir.parent)
            info = zipfile.ZipInfo(relative.as_posix(), FIXED_TIMESTAMP)
            mode = source_path.stat().st_mode
            permissions = 0o755 if mode & stat.S_IXUSR else 0o644
            info.external_attr = permissions << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, source_path.read_bytes())

    return output_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "dist",
        help="Directory that receives the ZIP files (default: dist/)",
    )
    args = parser.parse_args()
    output_dir = args.output.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    for skill_name in SKILLS:
        output_path = write_archive(skill_name, output_dir)
        print(output_path)


if __name__ == "__main__":
    main()
