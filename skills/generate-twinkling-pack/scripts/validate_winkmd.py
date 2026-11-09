#!/usr/bin/env python3
"""Check the winkmd delivery envelope, metadata and local attachment references.

This is not a second rich-document parser: the App validates full dialect semantics.
Unknown body markers remain literal. Uses only Python's standard library.
"""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
import zipfile
from pathlib import Path, PurePosixPath

AUDIO = {"m4a", "m4b", "wav", "mp3"}
IMAGES = {"png", "jpg", "jpeg", "heic", "webp", "tiff", "rimg"}
MAX_BYTES = 10 * 1024 * 1024
RESERVED = "/$-#-$/"
# Same rejections as the App's strict v2 import: legacy/Anki syntax, CJK text directly followed by
# unescaped [..] (old ruby; also catches unescaped citations like 参考文献[1]), and caret superscripts.
LEGACY = re.compile(
    r"(?<!\\)\{\{[cC]\d+::|(?<!\\)==\S.*?==|<[uU]>|\[[^\]]+\]\{(?:color|highlight|script)="
    r"|[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff々〆ヶ]\[[^\]]+\](?!\()"
    r"|(?<!\\)\^[^\^\s]+\^"
)
PAIRED = {"cloze", "mute", "note", "ruby", "color", "u", "sup", "sub", "size", "font", "math"}
# Inline formulas, read like the App: `$` + non-space, closing `$` after non-space and not before a digit; or {{math}}…{{/math}}.
INLINE_MATH = re.compile(r"(?<!\\)\$(?=[^\s$])(?:\\.|[^$\\])*?(?<=\S)\$(?!\d)|\{\{math\}\}.*?\{\{/math\}\}")
ATTRIBUTE_TAG = re.compile(r"\{\{(?:note|ruby|ruby64)=(?:\\.|[^}\\])*\}\}")
TAG = re.compile(r"(?<!\\)\{\{(/?)([a-z0-9]+)(?:[:=](?:\\.|[^}\\])*)?\}\}")
# A header exists only when the line after the first "---" starts with a known key (same rule as the App).
HEADER_LINE = re.compile(r"^\s*(?:wink_md_version|pack_name|categories|fill_blanks|generator)\s*:")
# Known tags whose value the App checks; a wrong value rejects the card (spec: Authoring tiers and tag tables).
_HEX = r"#[0-9A-Fa-f]{6}"
_CLOZE_PART = rf"(?:id=[A-Za-z0-9_-]{{1,64}}|color={_HEX})"
_NUMBER = re.compile(r"[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?")


def _attribute_text(value):
    """Decode a note/ruby attribute: only \\n, \\\\ and \\} escapes are allowed (same as the App)."""
    output, index = [], 0
    while index < len(value):
        if value[index] == "\\":
            if index + 1 >= len(value) or value[index + 1] not in "n\\}":
                return None
            output.append("\n" if value[index + 1] == "n" else value[index + 1])
            index += 2
        else:
            output.append(value[index])
            index += 1
    return "".join(output)


def _valid_text(value, limit, allows_newline):
    text = _attribute_text(value)
    return (
        text is not None and 1 <= len(text) <= limit and text == text.strip()
        and not any(unicodedata.category(c) == "Cc" and not (allows_newline and c == "\n") for c in text)
    )


TAG_VALUES = {
    "color:": _HEX,
    "cloze:": rf"{_CLOZE_PART}(?:;{_CLOZE_PART})*",
    "size:": r"small|large|x-large|xx-large",
    "u:": r"solid|wavy|dashed|dotted",
    "font:": r".+",
    # Numbers parse like the App (Swift Int / Double): `01` and `5e-1` are fine; only the range matters.
    "indent=": lambda value: re.fullmatch(r"[+-]?\d+", value) is not None and 0 <= int(value) <= 16,
    "align=": r"center|right",
    "width=": lambda value: _NUMBER.fullmatch(value) is not None and 0 < float(value) <= 1,
    "note=": lambda value: _valid_text(value, 500, allows_newline=True),
    "ruby=": lambda value: _valid_text(value, 100, allows_newline=False),
    "header=": r"none|row|column|both",
    "bg=": r"gray|red|yellow|pink|green|cyan|blue|purple|brown",
    "format=": r"number|percent|currency:[A-Z]{3}",
}


class InputError(ValueError):
    pass


def category_path(value):
    if not isinstance(value, list) or len(value) > 32 or any(
        not isinstance(name, str) or not name.strip() or len(name) > 200
        or "\n" in name or "\r" in name or RESERVED in name for name in value
    ):
        raise InputError("category must be one parent-to-child path, with up to 32 nonempty names (1–200 characters each)")
    return value


def parse(text):
    lines = text.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    header = {}
    # Only "---" followed by a known `key: value` line starts a header; a body may begin with a rule.
    if lines[0] == "---" and len(lines) > 1 and HEADER_LINE.match(lines[1]):
        try:
            end = lines.index("---", 1)
        except ValueError:
            raise InputError("file header needs a closing ---")
        for line in lines[1:end]:
            if not line.strip():
                continue
            if ":" not in line:
                raise InputError("header lines must use key: value")
            key, value = map(str.strip, line.split(":", 1))
            if key in header:
                raise InputError(f"duplicate header field: {key}")
            header[key] = value
        lines = lines[end + 1:]
    if header.get("wink_md_version", "2") != "2":
        raise InputError("only wink_md_version: 2 is supported")
    if "pack_name" in header:
        name = header["pack_name"]
        if name.startswith('"'):
            name = json.loads(name)
        if not isinstance(name, str) or not name.strip():
            raise InputError("pack_name must be a nonempty name")
    if "fill_blanks" in header and header["fill_blanks"] not in {"true", "false"}:
        raise InputError("fill_blanks must be true or false")
    seen = set()
    if "categories" in header:
        categories = json.loads(header["categories"])
        if not isinstance(categories, list):
            raise InputError("categories must be a JSON array")
        for entry in categories:
            if not isinstance(entry, dict) or not {"path", "color"} <= entry.keys():
                raise InputError("each category definition needs path and color")
            path = tuple(category_path(entry["path"]))
            if not path or path in seen or not isinstance(entry["color"], str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", entry["color"]):
                raise InputError("category paths must be nonempty and unique; colors use #RRGGBB")
            seen.add(path)

    cards, references, number = [[]], [], 1
    paragraph = []

    def close_paragraph():
        stack = []
        for match in TAG.finditer("\n".join(paragraph)):
            closing, name = match.group(1), match.group(2)
            inner = match.group(0)[2:-2]
            if not closing and inner.startswith("ruby64="):
                raise InputError(f"card {number}: do not write {{{{ruby64=…}}}}; write {{{{ruby=reading}}}} (spec: Authoring tiers)")
            for prefix, rule in TAG_VALUES.items():
                if closing or not inner.startswith(prefix):
                    continue
                value = inner[len(prefix):]
                if not (rule(value) if callable(rule) else re.fullmatch(rule, value)):
                    raise InputError(f"card {number}: {{{{{inner}}}}} has an invalid value; check the tag tables in wink-spec-markdown-format.md")
            name = "ruby" if name == "ruby64" else name
            if name not in PAIRED:
                continue
            if not closing:
                stack.append(name)
            elif stack and stack[-1] == name:
                stack.pop()
            else:
                raise InputError(f"card {number}: {{{{/{name}}}}} has no matching opening tag in this paragraph, or tags close out of order")
        if stack:
            raise InputError(f"card {number}: {{{{{stack[-1]}}}}} must be closed in the same paragraph")
        paragraph.clear()
    fence = None
    container = []
    meta_lines = None
    at_card_start = True
    for line in lines:
        stripped = line.strip()
        if meta_lines is not None:
            if "-->" in line:
                before, after = line.split("-->", 1)
                meta_lines.append(before)
                meta = json.loads("\n".join(meta_lines))
                if not isinstance(meta, dict):
                    raise InputError(f"card {number}: meta must be a JSON object")
                category_path(meta.get("category", []))
                if "starred" in meta and not isinstance(meta["starred"], bool):
                    raise InputError(f"card {number}: starred must be a boolean")
                meta_lines = None
                if after.strip():
                    cards[-1].append(after)
                at_card_start = False
            else:
                meta_lines.append(line)
            continue
        if fence:
            if re.fullmatch(re.escape(fence[0]) + "{" + str(len(fence)) + ",}\\s*", stripped):
                fence = None
            cards[-1].append(line)
            continue
        opening = re.match(r"^(`{3,}|~{3,})", stripped)
        if opening:
            fence = opening[1]
            cards[-1].append(line)
            at_card_start = False
            continue
        top = not line.startswith((" ", "\t", ">", "- ", "* ", "+ "))
        if top and not container and stripped in {"<!-- card -->", "<!-- back -->"}:
            close_paragraph()
        if top and not container and stripped == "<!-- card -->":
            cards.append([])
            number += 1
            at_card_start = True
            continue
        if top and not container and stripped == "<!-- back -->":
            at_card_start = False
            continue
        if top and not container and re.match(r"^<!-- meta(?:\s|$)", line):
            if not at_card_start:
                raise InputError(f"card {number}: meta belongs once at the start of the front")
            raw = line[len("<!-- meta"):]
            if "-->" in raw:
                obj = json.loads(raw.split("-->", 1)[0])
                if not isinstance(obj, dict):
                    raise InputError(f"card {number}: meta must be an object")
                category_path(obj.get("category", []))
                if "starred" in obj and not isinstance(obj["starred"], bool):
                    raise InputError(f"card {number}: starred must be boolean")
                at_card_start = False
            else:
                meta_lines = [raw]
            continue
        if top:
            if stripped.startswith(":::choice"):
                container.append(":::")
            elif stripped.startswith("<details"):
                container.append("</details>")
            elif stripped == "$$":
                if container and container[-1] == "$$":
                    container.pop()
                else:
                    container.append("$$")
            elif container and stripped == container[-1]:
                container.pop()
        # Display formulas are raw LaTeX, like code: no legacy or tag checks inside.
        if stripped == "$$" or (container and container[-1] == "$$"):
            cards[-1].append(line)
            at_card_start = False
            continue
        visible = re.sub(r"(`+).*?\1", "", line)
        visible = INLINE_MATH.sub("", visible)
        # Note and ruby texts are plain attributes; legacy-looking text inside them is literal.
        if LEGACY.search(ATTRIBUTE_TAG.sub("{{attr}}", visible)):
            raise InputError(f"card {number}: use dialect v2 only; rewrite legacy/Anki syntax and escape literal brackets as \\[ \\]")
        if stripped:
            paragraph.append(visible)
        else:
            close_paragraph()
        references.extend((number, ref) for ref in re.findall(r"!\[[^\]]*\]\(att:([^\s)]+)\)", visible))
        cards[-1].append(line)
        if stripped:
            at_card_start = False
    close_paragraph()
    if meta_lines is not None:
        raise InputError(f"card {number}: meta needs a closing -->")
    if fence or container:
        raise InputError(f"card {number}: unclosed code/choice/details/formula block")
    nonempty = sum(bool("\n".join(card).strip()) for card in cards)
    if not nonempty:
        raise InputError("no nonempty cards")
    return {"cards": nonempty, "references": references, "header": header}


def attachment_name(reference):
    if PurePosixPath(reference).name != reference or "\\" in reference or reference in {".", ".."}:
        raise InputError(f"attachment must be directly under media/: {reference}")
    ext = reference.rsplit(".", 1)[-1].lower()
    if ext not in AUDIO | IMAGES:
        raise InputError(f"unsupported attachment extension: {reference}")
    return reference


def validate(path, media=None):
    path = Path(path)
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            if len(names) != len(set(names)) or any(PurePosixPath(n).is_absolute() or ".." in PurePosixPath(n).parts for n in names):
                raise InputError("archive has duplicate or unsafe entries")
            manuscripts = [n for n in names if "/" not in n and n.lower().endswith(".winkmd")]
            if len(manuscripts) != 1:
                raise InputError("ZIP root must contain exactly one .winkmd")
            info = parse(archive.read(manuscripts[0]).decode("utf-8-sig"))
            for number, ref in info["references"]:
                name = "media/" + attachment_name(ref)
                if name not in names:
                    raise InputError(f"card {number}: missing {name}; repair before delivery")
                if archive.getinfo(name).file_size > MAX_BYTES:
                    raise InputError(f"card {number}: {ref} exceeds 10 MiB")
    elif path.suffix.lower() == ".winkmd":
        info = parse(path.read_text(encoding="utf-8-sig"))
        root = Path(media) if media else path.parent / "media"
        for number, ref in info["references"]:
            file = root / attachment_name(ref)
            if not file.is_file() or file.resolve().parent != root.resolve():
                raise InputError(f"card {number}: missing media/{ref}; repair before delivery")
            if file.stat().st_size > MAX_BYTES:
                raise InputError(f"card {number}: {ref} exceeds 10 MiB")
    else:
        raise InputError("expected .winkmd or .zip")
    return info


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--media", type=Path)
    args = parser.parse_args()
    try:
        info = validate(args.input, args.media)
    except (InputError, OSError, ValueError, zipfile.BadZipFile) as error:
        parser.exit(1, f"Invalid: {error}\n")
    print(f"Valid delivery envelope: {info['cards']} cards, {len(info['references'])} attachment occurrences; App checks full dialect semantics")


if __name__ == "__main__":
    main()
