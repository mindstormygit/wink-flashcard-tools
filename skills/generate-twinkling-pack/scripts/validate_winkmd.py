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
_CHOICE_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_DETAILS_OPENING = re.compile(
    r'^<details(\s+open(="[^"]*")?)?\s*>\s*(?:<summary>(.*)</summary>)?\s*$',
    re.IGNORECASE,
)
_CONTAINER_MARKERS = re.compile(r"^(?:(?:[-*+]|[0-9]+[.)]|>)[ \t]+)+")
_CHOICE_LIST_ITEM = re.compile(r"^( *)([-*+]|[0-9]{1,9}[.)])( +)(.*)$")
_CHECKBOX_REST = re.compile(r"^\[[ xX]\](?:[ \t]|$)")
_LIST_ITEM_START = re.compile(r"^[ \t]*(?:[-*+]|[0-9]{1,9}[.)])[ \t]+")
_SUMMARY_LINE = re.compile(r"^\s*<summary>.*</summary>\s*$", re.IGNORECASE)
_HEADING_OR_RULE = re.compile(r"^[ ]{0,3}(?:#{1,6}(?:[ \t]|$)|(?:[-*_][ \t]*){3,}$)")
_PARAGRAPH_BREAK_BLOCK = re.compile(
    r"^[ ]{0,3}(?:#{1,6}(?:[ \t]|$)|>|(?:[-*_][ \t]*){3,}$|[0-9]{1,9}[.)][ \t]+)"
)
_NUMBER = re.compile(r"[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?")


class InputError(ValueError):
    pass


def _fence_opening(trimmed):
    """Match WinkMarkdownSource.fenceOpening: backtick fence info strings cannot contain backticks."""
    for marker in ("```", "~~~"):
        if trimmed.startswith(marker):
            ch = marker[0]
            run_len = len(trimmed) - len(trimmed.lstrip(ch))
            rest = trimmed[run_len:]
            if ch == "`" and "`" in rest:
                return None
            return ch * run_len
    return None


def _closes_fence(trimmed, open_fence):
    ch = open_fence[0]
    run_len = len(trimmed) - len(trimmed.lstrip(ch))
    return run_len >= len(open_fence) and not trimmed[run_len:].strip()


def _details_opening(line):
    """Match WinkMarkdownSource.detailsOpening: column-0 <details[ open]>, case-insensitive.

    Returns inline summary string (or '' if no inline summary) when matched; None otherwise.
    """
    if not line[:8].lower() == "<details":
        return None
    match = _DETAILS_OPENING.match(line)
    if not match:
        return None
    return match.group(3) or ""


def _is_details_closing(line):
    """Match WinkMarkdownSource.isDetailsClosing: column-0 </details>, case-insensitive."""
    return bool(line) and not line[0].isspace() and line.strip().lower() == "</details>"


def _choice_opening(line, number):
    """Match WinkMarkdownSource.choiceHeader: column-0 :::choice or :::choice{...}."""
    if not line.startswith(":::choice"):
        return False
    stripped = line.strip()
    rest = stripped[len(":::choice"):]
    if not rest:
        return True
    if not rest.startswith("{"):
        return False
    if not rest.endswith("}"):
        raise InputError(f"card {number}: choice header is missing closing }}")
    inner = rest[1:-1].strip()
    if not inner:
        raise InputError(f"card {number}: choice header attributes cannot be empty")
    seen_id = seen_shuffle = False
    for token in re.split(r"[ \t]+", inner):
        if token.startswith("#"):
            if seen_id or not _CHOICE_ID.fullmatch(token[1:]):
                raise InputError(f"card {number}: invalid choice id {token}")
            seen_id = True
        elif token.startswith("shuffle="):
            if seen_shuffle or token[len("shuffle="):] not in {"true", "false"}:
                raise InputError(f"card {number}: choice shuffle must be true or false (once)")
            seen_shuffle = True
        else:
            raise InputError(f"card {number}: unknown choice attribute {token}")
    return True


def _is_valid_choice_opening(line):
    try:
        return _choice_opening(line, 0)
    except InputError:
        return False


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


def category_path(value):
    if not isinstance(value, list) or len(value) > 32 or any(
        not isinstance(name, str) or not name.strip() or len(name) > 200
        or "\n" in name or "\r" in name or RESERVED in name for name in value
    ):
        raise InputError("category must be one parent-to-child path, with up to 32 nonempty names (1–200 characters each)")
    return value


def _starts_metadata(text):
    return text.startswith("<!-- meta") and (len(text) == 9 or text[9].isspace())


def _protected_lines(lines, *, file_importer=False):
    """Track containers using either body or file-import fence recognition."""
    protected = set()
    fence = None
    choice = False
    details = 0
    math = False
    html_comment = False
    for index, line in enumerate(lines):
        trimmed = line.strip()
        if fence:
            protected.add(index)
            if _closes_fence(trimmed, fence):
                fence = None
            continue
        if html_comment:
            protected.add(index)
            if "-->" in line:
                html_comment = False
            continue
        # The App file splitter accepts any leading backtick run; its body decoder
        # excludes backtick info strings containing backticks (e.g. inline code).
        if file_importer and trimmed.startswith("```"):
            open_fence = trimmed[:len(trimmed) - len(trimmed.lstrip("`"))]
        else:
            open_fence = _fence_opening(trimmed)
        if open_fence:
            fence = open_fence
            protected.add(index)
            continue
        if not choice and not math and trimmed.startswith("<!--") and "-->" not in trimmed:
            html_comment = True
            continue
        if _is_valid_choice_opening(line):
            choice = True
        if _details_opening(line) is not None:
            details += 1
        if trimmed == "$$":
            math = not math
            protected.add(index)
            continue
        if choice or details > 0 or math:
            protected.add(index)
        if trimmed == ":::":
            choice = False
        if _is_details_closing(line):
            details = max(0, details - 1)
    return protected


def _take_metadata(front, number):
    """Mirror WinkMarkdownFile.takeMetadata: validate leading meta, strip it, and trim remaining front."""
    if not _starts_metadata(front):
        return front
    end = front.find("-->")
    if end == -1:
        raise InputError(f"card {number}: meta needs a closing -->")
    raw = front[len("<!-- meta"):end]
    meta = json.loads(raw)
    if not isinstance(meta, dict):
        raise InputError(f"card {number}: meta must be a JSON object")
    category_path(meta.get("category", []))
    if "starred" in meta and not isinstance(meta["starred"], bool):
        raise InputError(f"card {number}: starred must be a boolean")
    remaining = front[end + 3:].strip()
    if _starts_metadata(remaining):
        raise InputError(f"card {number}: meta belongs once at the start of the front")
    return remaining


def _close_paragraph(paragraph, number):
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


def _check_inline_line(line, number, paragraph, references):
    visible = re.sub(r"(`+).*?\1", "", line)
    visible = INLINE_MATH.sub("", visible)
    # Note and ruby texts are plain attributes; legacy-looking text inside them is literal.
    if LEGACY.search(ATTRIBUTE_TAG.sub("{{attr}}", visible)):
        raise InputError(f"card {number}: use dialect v2 only; rewrite legacy/Anki syntax and escape literal brackets as \\[ \\]")
    paragraph.append(visible)
    references.extend((number, ref) for ref in re.findall(r"!\[[^\]]*\]\(att:([^\s)]+)\)", visible))


def _scan_display_math(lines, start, number):
    """Match the spec (`$$` on its own lines, or single-line `$$…$$`) so card splitting stays aligned with the App."""
    after_open = lines[start].strip()[2:]
    if len(after_open) >= 2 and after_open.endswith("$$"):
        return start
    if after_open:
        raise InputError(f"card {number}: put the opening $$ on its own line for a multiline formula")
    end = start + 1
    while end < len(lines):
        trimmed = lines[end].strip()
        if trimmed == "$$":
            return end
        if trimmed.endswith("$$"):
            raise InputError(f"card {number}: put the closing $$ on its own line for a multiline formula")
        end += 1
    raise InputError(f"card {number}: unclosed $$ display formula (put the closing $$ on its own line)")


def _validate_choice_body(body_lines, number):
    """Ensure choice body has a non-empty prompt and ends with a top-level checkbox option list."""
    body = list(body_lines)
    while body and not body[-1].strip():
        body.pop()
    if not body:
        raise InputError(f"card {number}: choice block must include a prompt and options")

    prompt_has_content = False
    in_list = False
    list_marker = None
    list_content_col = 0
    trailing_options = 0
    option_has_children = False
    blank = False
    i = 0

    while i < len(body):
        line = body[i]
        stripped = line.strip()
        open_fence = _fence_opening(stripped)
        if open_fence:
            end = i + 1
            while end < len(body) and not _closes_fence(body[end].strip(), open_fence):
                end += 1
            if end >= len(body):
                raise InputError(f"card {number}: unclosed code block")
            prompt_has_content = True
            in_list = False
            trailing_options = 0
            blank = False
            i = end + 1
            continue
        if stripped.startswith("$$"):
            end = _scan_display_math(body, i, number)
            prompt_has_content = True
            in_list = False
            trailing_options = 0
            blank = False
            i = end + 1
            continue
        if not stripped:
            blank = True
            i += 1
            continue

        match = _CHOICE_LIST_ITEM.match(line.expandtabs(4))
        if match and in_list and len(match[1]) >= list_content_col:
            # Nested entries belong to their parent, including ordered parents.
            if trailing_options:
                option_has_children = True
            blank = False
            i += 1
            continue
        if match and len(match[1]) <= 3:
            marker = match[2][-1]  # Ordered lists are grouped by delimiter ('.' or ')').
            if in_list and marker != list_marker:
                prompt_has_content = True
                trailing_options = 0
            if not trailing_options:
                option_has_children = False
            in_list = True
            list_marker = marker
            padding = len(match[3])
            list_content_col = match.end(2) + (padding if padding <= 4 else 1)
            if marker in "-*+" and padding <= 4 and _CHECKBOX_REST.match(match[4]):
                trailing_options += 1
            else:
                prompt_has_content = True
                trailing_options = 0
            blank = False
            i += 1
            continue

        if in_list and not blank and not _PARAGRAPH_BREAK_BLOCK.match(line) and _details_opening(line) is None:
            # Lazy continuation line within the same list item's single paragraph.
            blank = False
            i += 1
            continue

        prompt_has_content = True
        in_list = False
        trailing_options = 0
        blank = False
        i += 1

    if trailing_options == 0:
        raise InputError(f"card {number}: choice block must end with a top-level option list (- [ ] / - [x])")
    if option_has_children:
        raise InputError(f"card {number}: a choice option cannot contain a nested list")
    if not prompt_has_content:
        raise InputError(f"card {number}: choice block must include a non-empty prompt before options")


def _validate_side(lines, number, references, *, choice_policy="allow", allows_details=True):
    """Validate one card side or nested block following WinkMarkdownSource block precedence."""
    paragraph = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # 1. Fenced code block
        open_fence = _fence_opening(stripped)
        if open_fence:
            _close_paragraph(paragraph, number)
            end = i + 1
            while end < len(lines) and not _closes_fence(lines[end].strip(), open_fence):
                end += 1
            if end >= len(lines):
                raise InputError(f"card {number}: unclosed code block")
            i = end + 1
            continue

        # 2. Choice block (outer scan respects only code fences, matching Swift WinkMarkdownSource)
        if choice_policy != "literal" and line.startswith(":::choice") and _choice_opening(line, number):
            if choice_policy == "forbid":
                raise InputError(f"card {number}: choice block is not allowed inside <details>")
            _close_paragraph(paragraph, number)
            collected = []
            explanation_start = None
            inner_fence = None
            end = i + 1
            closed = False
            while end < len(lines):
                inner = lines[end]
                inner_trimmed = inner.strip()
                if inner_fence:
                    if _closes_fence(inner_trimmed, inner_fence):
                        inner_fence = None
                else:
                    opened = _fence_opening(inner_trimmed)
                    if opened:
                        inner_fence = opened
                    elif inner.startswith(":::explanation") and inner_trimmed == ":::explanation" and explanation_start is None:
                        explanation_start = len(collected)
                        end += 1
                        continue
                    elif inner_trimmed == ":::":
                        closed = True
                        break
                collected.append(inner)
                end += 1
            if not closed:
                raise InputError(f"card {number}: unclosed choice block")
            body = collected[:explanation_start] if explanation_start is not None else collected
            explanation = collected[explanation_start:] if explanation_start is not None else None
            _validate_choice_body(body, number)
            _validate_side(body, number, references, choice_policy="literal", allows_details=False)
            if explanation is not None:
                _validate_side(explanation, number, references, choice_policy="literal", allows_details=False)
            i = end + 1
            continue

        # 3. Collapsible <details> block (case-insensitive column-0 tag, matching Swift)
        details_summary = _details_opening(line)
        if details_summary is not None:
            if not allows_details:
                raise InputError(f"card {number}: <details> is not allowed inside choice blocks")
            _close_paragraph(paragraph, number)
            if details_summary:
                summary_para = []
                _check_inline_line(details_summary, number, summary_para, references)
                _close_paragraph(summary_para, number)
            depth = 1
            inner_fence = None
            end = i + 1
            while end < len(lines):
                inner = lines[end]
                marker_stripped = _CONTAINER_MARKERS.sub("", inner.strip())
                if inner_fence:
                    if _closes_fence(marker_stripped, inner_fence):
                        inner_fence = None
                else:
                    opened = _fence_opening(marker_stripped)
                    if opened:
                        inner_fence = opened
                    elif _details_opening(inner) is not None:
                        depth += 1
                    elif _is_details_closing(inner):
                        depth -= 1
                        if depth == 0:
                            break
                end += 1
            if depth != 0:
                raise InputError(f"card {number}: unclosed <details> block")
            _validate_side(lines[i + 1:end], number, references, choice_policy="forbid", allows_details=True)
            i = end + 1
            continue

        # 4. Display formula block (`$$` … `$$`)
        if stripped.startswith("$$"):
            _close_paragraph(paragraph, number)
            end = _scan_display_math(lines, i, number)
            i = end + 1
            continue

        # 5. Ordinary inline content
        if not stripped:
            _close_paragraph(paragraph, number)
            i += 1
            continue
        if _SUMMARY_LINE.fullmatch(line):
            _close_paragraph(paragraph, number)
            _check_inline_line(line, number, paragraph, references)
            _close_paragraph(paragraph, number)
            i += 1
            continue
        is_quote = stripped.startswith(">")
        if (
            _LIST_ITEM_START.match(line)
            or _HEADING_OR_RULE.match(line)
            or (paragraph and is_quote != paragraph[-1].lstrip().startswith(">"))
        ):
            _close_paragraph(paragraph, number)
        _check_inline_line(line, number, paragraph, references)
        i += 1

    _close_paragraph(paragraph, number)


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

    # Split manuscript into per-card (front, back) chunks, matching WinkMarkdownFile.swift.
    protected = _protected_lines(lines)
    ambiguous_lines = protected ^ _protected_lines(lines, file_importer=True)
    chunks = [([], [])]
    misplaced_meta = set()
    on_back = False
    for index, line in enumerate(lines):
        stripped = line.strip()
        if index in ambiguous_lines and line.rstrip() in {"<!-- card -->", "<!-- back -->"}:
            raise InputError(f"line {index + 1}: ambiguous separator after backticks; use single backticks for inline code or a complete fenced block")
        top = index not in protected and not line.startswith((" ", "\t", ">", "- ", "* ", "+ "))
        if top and _starts_metadata(stripped):
            if on_back or any(prev.strip() for prev in chunks[-1][0]):
                misplaced_meta.add(len(chunks) - 1)
        if top and stripped == "<!-- card -->":
            chunks.append(([], []))
            on_back = False
            continue
        if top and stripped == "<!-- back -->":
            on_back = True
            continue
        if on_back:
            chunks[-1][1].append(line)
        else:
            chunks[-1][0].append(line)

    references = []
    nonempty = 0
    for idx, (front_lines, back_lines) in enumerate(chunks):
        number = idx + 1
        if idx in misplaced_meta:
            raise InputError(f"card {number}: meta belongs once at the start of the front")
        front = "\n".join(front_lines).strip()
        front = _take_metadata(front, number)
        back = "\n".join(back_lines)
        if front:
            _validate_side(front.split("\n"), number, references, choice_policy="allow", allows_details=True)
        if back.strip():
            _validate_side(back.split("\n"), number, references, choice_policy="allow", allows_details=True)
        if front or back.strip():
            nonempty += 1

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
