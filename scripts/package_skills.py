#!/usr/bin/env python3
"""Create reproducible release ZIP files for both WinkNotes Skills.

Before packaging, copy the dialect spec and its accept/reject samples from the WinkNotes App
repository. The App's copy is the only one that is edited; the Skill's copies are generated.
"""

from __future__ import annotations

import argparse
import datetime
import os
import re
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

DEFAULT_APP_REPO = Path(os.environ.get("WINK_APP_REPO", ROOT.parent / "iOS" / "TwinklingCard"))
APP_SPEC = Path("supportfiles/specs/wink-spec-markdown-format.md")
APP_SAMPLES = Path("supportfiles/specs/wink-dialect-v2-samples.json")
SKILL_SPEC = ROOT / "skills/generate-twinkling-pack/references/wink-spec-markdown-format.md"
SKILL_SAMPLES = ROOT / "tests/fixtures/wink-dialect-v2-samples.json"
GENERATED_MARK = "<!-- Generated copy."
SAMPLES_LINK = "[wink-dialect-v2-samples.json](wink-dialect-v2-samples.json)"


def app_version(app_repo: Path) -> str:
    project = app_repo / "com.lm.william.TwinklingCard.xcodeproj/project.pbxproj"
    match = re.search(r"APP_VERSION = ([0-9.]+);", project.read_text(encoding="utf-8"))
    return match.group(1) if match else "unknown"


def skill_spec_body(app_spec: str) -> str:
    """The Skill copy's text after its header. The samples link only resolves in the App repo."""
    return app_spec.replace(SAMPLES_LINK, "`wink-dialect-v2-samples.json` (App repository)")


def strip_generated_header(text: str) -> str:
    if text.startswith(GENERATED_MARK):
        return text.split("-->\n\n", 1)[1]
    return text


def sync_from_app(app_repo: Path) -> None:
    source = app_repo / APP_SPEC
    if not source.is_file():
        raise SystemExit(f"App spec not found: {source}. Pass --app-repo or set WINK_APP_REPO.")
    header = (
        f"{GENERATED_MARK} Source: WinkNotes App repository, {APP_SPEC.as_posix()}, "
        f"app version {app_version(app_repo)}, copied {datetime.date.today().isoformat()}. "
        "Do not edit here: edit the App copy, then rerun scripts/package_skills.py. -->\n\n"
    )
    SKILL_SPEC.write_text(header + skill_spec_body(source.read_text(encoding="utf-8")), encoding="utf-8")
    SKILL_SAMPLES.parent.mkdir(parents=True, exist_ok=True)
    SKILL_SAMPLES.write_bytes((app_repo / APP_SAMPLES).read_bytes())


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
    parser.add_argument(
        "--app-repo",
        type=Path,
        help="WinkNotes App checkout that holds the dialect spec (default: $WINK_APP_REPO or ../iOS/TwinklingCard)",
    )
    args = parser.parse_args()
    if args.app_repo is not None:
        sync_from_app(args.app_repo.resolve())
    elif (DEFAULT_APP_REPO / APP_SPEC).is_file():
        sync_from_app(DEFAULT_APP_REPO.resolve())
    else:
        # CI and other machines have no App checkout: package the committed copy as is.
        print(f"App repository not found at {DEFAULT_APP_REPO}; packaging the committed spec copy")
    output_dir = args.output.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    for skill_name in SKILLS:
        output_path = write_archive(skill_name, output_dir)
        print(output_path)


if __name__ == "__main__":
    main()
