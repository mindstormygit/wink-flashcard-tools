#!/usr/bin/env python3
"""Validate mixed NoteLegacy/Choice .wink packs or cards from this skill."""

import argparse
import base64
import binascii
import json
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

from image_support import (
    ImageFormatError,
    MAX_IMAGE_BYTES,
    SUPPORTED_IMAGE_EXTENSIONS,
    validate_image_bytes,
)
from rich_image_support import (
    MAX_RICH_IMAGE_BYTES,
    RICH_IMAGE_EXTENSION,
    RichImageFormatError,
    validate_rich_image_bytes,
)

APP_DOCUMENT_VERSION = 6
NOTE_DOCUMENT_VERSION = 3
CHOICE_DOCUMENT_VERSION = 100
NOTE_DOCUMENT_TYPE = 0
CHOICE_DOCUMENT_TYPE = 2
MAX_CONTENT_JSON_BYTES = 64 * 1024 * 1024
PACK_REQUIRED_KEYS = {"name", "cards", "version"}
PACK_OPTIONAL_KEYS = {"tags"}
CARD_REQUIRED_KEYS = {
    "uuid",
    "sidea",
    "sideb",
    "flag",
    "rtf",
    "sideaAttIds",
    "sidebAttIds",
    "version",
}
CARD_OPTIONAL_KEYS = {"tag"}
TAG_KEYS = {"name", "lighthex"}
SPAN_KEYS = {"f", "l", "s", "c", "mc", "lk", "sc", "at", "aes"}
CHOICE_SPAN_REQUIRED_KEYS = {"f", "l", "ft", "st"}
CHOICE_SPAN_OPTIONAL_KEYS = {"c", "bc", "lk"}
CHOICE_DOCUMENT_KEYS = {
    "version",
    "question",
    "options",
    "note",
    "correctOptionIDSet",
    "shuffleOptions",
    "type",
}
BLOCK_NODE_KEYS = {"id", "content", "children", "createdAt"}
BLOCK_CONTENT_KEYS = {"type", "payload"}
HEX_COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")
UUID_PATTERN = re.compile(r"^[0-9a-f]{32}$")
ATTACHMENT_FILENAME_PATTERN = re.compile(
    r"^([0-9a-f]{32})\.(heic|png|jpeg|jpg|webp|tiff|rimg)$"
)
SUPPORTED_ATTACHMENT_EXTENSIONS = (
    SUPPORTED_IMAGE_EXTENSIONS | {RICH_IMAGE_EXTENSION}
)
STYLE_UNDERLINE = 1
STYLE_BOLD = 1 << 1
STYLE_STRIKETHROUGH = 1 << 2
STYLE_HIGHLIGHT = 1 << 3
STYLE_SUPERSUBSCRIPT = 1 << 4
STYLE_MASK = (
    STYLE_UNDERLINE
    | STYLE_BOLD
    | STYLE_STRIKETHROUGH
    | STYLE_HIGHLIGHT
    | STYLE_SUPERSUBSCRIPT
)
ATTACHMENT_CHARACTER = "\uFFFC"
MAX_ATTACHMENTS_PER_SIDE = 15
MAX_TOTAL_MEDIA_BYTES = 512 * 1024 * 1024
TAG_PATH_SEPARATOR = "/$-#-$/"
MAX_TAGS = 500
MAX_TAG_DEPTH = 32
MAX_TAG_NAME_LENGTH = 200
MAX_CHOICE_OPTIONS = 26
CARD_FLAG_OCCLUSION = 1 << 1


class ValidationError(ValueError):
    """Raised when a .wink package violates the minimal format."""


def _require(condition, message):
    if not condition:
        raise ValidationError(message)


def _validate_archive_entry(info):
    path = PurePosixPath(info.filename)
    _require(not path.is_absolute(), f"archive entry is absolute: {info.filename}")
    _require(".." not in path.parts, f"archive entry escapes root: {info.filename}")
    _require(not (info.flag_bits & 0x1), "archive must not be encrypted")


def _utf16_length(value):
    try:
        return len(value.encode("utf-16-le")) // 2
    except UnicodeEncodeError as error:
        raise ValidationError("content contains an invalid Unicode surrogate") from error


def _validate_color(value, label):
    _require(
        isinstance(value, str) and HEX_COLOR_PATTERN.fullmatch(value),
        f"{label} must use #RRGGBB",
    )


def _validate_link(value, label):
    _require(isinstance(value, str), f"{label} must be a string")
    parsed = urlsplit(value)
    _require(
        parsed.scheme in {"http", "https"} and parsed.netloc,
        f"{label} must be an absolute HTTP or HTTPS URL",
    )


def _utf16_slice(value, location, length):
    encoded = value.encode("utf-16-le")
    return encoded[location * 2 : (location + length) * 2].decode("utf-16-le")


def _validate_spans(spans, content, label):
    _require(isinstance(spans, list) and spans, f"{label} must be a non-empty array")
    content_length = _utf16_length(content)
    previous_end = 0
    attachment_filenames = []
    for index, span in enumerate(spans):
        span_label = f"{label}[{index}]"
        _require(isinstance(span, dict), f"{span_label} must be an object")
        _require(
            {"f", "l"}.issubset(span) and set(span).issubset(SPAN_KEYS),
            f"{span_label} has invalid fields",
        )
        location = span["f"]
        length = span["l"]
        _require(
            type(location) is int and location >= 0,
            f"{span_label}.f must be a non-negative integer",
        )
        _require(
            type(length) is int and length > 0,
            f"{span_label}.l must be a positive integer",
        )
        _require(
            location >= previous_end,
            f"{span_label} overlaps or is out of order",
        )
        _require(
            location + length <= content_length,
            f"{span_label} exceeds the UTF-16 content length",
        )
        previous_end = location + length

        has_attachment = "at" in span or "aes" in span
        if has_attachment:
            _require(
                set(span) == {"f", "l", "at", "aes"},
                f"{span_label} attachment has invalid fields",
            )
            attachment_id = span["at"]
            extension = span["aes"]
            _require(
                isinstance(attachment_id, str)
                and UUID_PATTERN.fullmatch(attachment_id),
                f"{span_label}.at is invalid",
            )
            _require(
                isinstance(extension, str)
                and extension in SUPPORTED_ATTACHMENT_EXTENSIONS,
                f"{span_label}.aes is unsupported",
            )
            _require(length == 1, f"{span_label} attachment length must be 1")
            _require(
                _utf16_slice(content, location, length) == ATTACHMENT_CHARACTER,
                f"{span_label} does not cover an attachment character",
            )
            attachment_filenames.append(f"{attachment_id}.{extension}")
            continue

        style = span.get("s", 0)
        _require(
            type(style) is int and 0 <= style <= STYLE_MASK,
            f"{span_label}.s has unsupported style bits",
        )
        if "s" in span:
            _require(style != 0, f"{span_label}.s must be omitted when empty")
        if "c" in span:
            _validate_color(span["c"], f"{span_label}.c")
        if "mc" in span:
            _validate_color(span["mc"], f"{span_label}.mc")
            _require(
                bool(style & STYLE_HIGHLIGHT),
                f"{span_label}.mc requires the highlight style",
            )
        if "lk" in span:
            _validate_link(span["lk"], f"{span_label}.lk")
        if "sc" in span:
            _require(
                type(span["sc"]) is int and span["sc"] in {-1, 1},
                f"{span_label}.sc must be 1 or -1",
            )
            _require(
                bool(style & STYLE_SUPERSUBSCRIPT),
                f"{span_label}.sc requires the supersubscript style",
            )
        if style & STYLE_SUPERSUBSCRIPT:
            _require(
                "sc" in span,
                f"{span_label} supersubscript style requires sc",
            )
        _require(
            set(span) != {"f", "l"},
            f"{span_label} has no effective formatting",
        )
    return len(spans), attachment_filenames


def _validate_note_document(card, index, note):
    _require(isinstance(note, dict), f"cards[{index}].rtf root must be an object")
    _require(
        set(note) == {"v", "sa", "sb"},
        f"cards[{index}].rtf must contain only v, sa, and sb",
    )
    _require(
        note["v"] == NOTE_DOCUMENT_VERSION,
        f"cards[{index}].rtf has unsupported NoteLegacy version",
    )

    span_count = 0
    attachments_by_side = {}
    for side_key, card_key in (("sa", "sidea"), ("sb", "sideb")):
        side = note[side_key]
        _require(
            isinstance(side, dict)
            and "c" in side
            and set(side).issubset({"c", "a"}),
            f"cards[{index}].rtf.{side_key} has invalid fields",
        )
        _require(
            isinstance(side["c"], str) and side["c"].strip(),
            f"cards[{index}].rtf.{side_key}.c must not be empty",
        )
        _require(
            side["c"] == card[card_key],
            f"cards[{index}].rtf.{side_key}.c does not match {card_key}",
        )
        side_attachments = []
        if "a" in side:
            side_span_count, side_attachments = _validate_spans(
                side["a"], side["c"], f"cards[{index}].rtf.{side_key}.a"
            )
            span_count += side_span_count
        _require(
            side["c"].count(ATTACHMENT_CHARACTER) == len(side_attachments),
            f"cards[{index}].rtf.{side_key} has an unmatched attachment character",
        )
        attachments_by_side[card_key] = side_attachments
    return {
        "document_type": "note",
        "span_count": span_count,
        "attachments_by_side": attachments_by_side,
        "expected_flag": 0,
        "option_count": 0,
        "multiple_choice": False,
    }


def _validate_choice_spans(spans, content, label):
    _require(isinstance(spans, list) and spans, f"{label} must be a non-empty array")
    content_length = _utf16_length(content)
    previous_end = 0
    has_occlusion = False
    for index, span in enumerate(spans):
        span_label = f"{label}[{index}]"
        _require(isinstance(span, dict), f"{span_label} must be an object")
        _require(
            CHOICE_SPAN_REQUIRED_KEYS.issubset(span)
            and set(span).issubset(
                CHOICE_SPAN_REQUIRED_KEYS | CHOICE_SPAN_OPTIONAL_KEYS
            ),
            f"{span_label} has invalid fields",
        )
        location = span["f"]
        length = span["l"]
        _require(
            type(location) is int and location >= 0,
            f"{span_label}.f must be a non-negative integer",
        )
        _require(
            type(length) is int and length > 0,
            f"{span_label}.l must be a positive integer",
        )
        _require(
            location >= previous_end,
            f"{span_label} overlaps or is out of order",
        )
        _require(
            location + length <= content_length,
            f"{span_label} exceeds the UTF-16 content length",
        )
        previous_end = location + length
        _require(
            type(span["ft"]) is int and span["ft"] in {0, 1},
            f"{span_label}.ft must be 0 or 1",
        )
        _require(
            isinstance(span["st"], bool),
            f"{span_label}.st must be true or false",
        )
        if "c" in span:
            _validate_color(span["c"], f"{span_label}.c")
        if "bc" in span:
            _validate_color(span["bc"], f"{span_label}.bc")
            has_occlusion = True
        if "lk" in span:
            _validate_link(span["lk"], f"{span_label}.lk")
        _require(
            span["ft"] != 0
            or span["st"]
            or any(key in span for key in CHOICE_SPAN_OPTIONAL_KEYS),
            f"{span_label} has no effective formatting",
        )
    return len(spans), has_occlusion


def _validate_choice_payload(value, label):
    _require(isinstance(value, dict), f"{label} must be an object")
    _require(
        "c" in value and set(value).issubset({"c", "s"}),
        f"{label} has invalid fields",
    )
    content = value["c"]
    _require(
        isinstance(content, str) and content.strip(),
        f"{label}.c must not be empty",
    )
    span_count = 0
    has_occlusion = False
    if "s" in value:
        span_count, has_occlusion = _validate_choice_spans(
            value["s"], content, f"{label}.s"
        )
    return content, span_count, has_occlusion


def _validate_choice_block(value, label, seen_block_ids):
    _require(isinstance(value, dict), f"{label} must be an object")
    _require(set(value) == BLOCK_NODE_KEYS, f"{label} has invalid fields")
    block_id = value["id"]
    _require(
        isinstance(block_id, str) and UUID_PATTERN.fullmatch(block_id),
        f"{label}.id is invalid",
    )
    _require(block_id not in seen_block_ids, f"{label}.id is duplicated")
    seen_block_ids.add(block_id)
    _require(value["children"] == [], f"{label}.children must be empty")
    _require(
        type(value["createdAt"]) in {int, float}
        and value["createdAt"] == 0,
        f"{label}.createdAt must be 0",
    )
    block_content = value["content"]
    _require(
        isinstance(block_content, dict)
        and set(block_content) == BLOCK_CONTENT_KEYS,
        f"{label}.content has invalid fields",
    )
    _require(
        block_content["type"] == 0,
        f"{label}.content.type must be a text body",
    )
    content, span_count, has_occlusion = _validate_choice_payload(
        block_content["payload"], f"{label}.content.payload"
    )
    return {
        "id": block_id,
        "content": content,
        "span_count": span_count,
        "has_occlusion": has_occlusion,
    }


def _validate_choice_document(card, index, document):
    label = f"cards[{index}].rtf"
    _require(isinstance(document, dict), f"{label} root must be an object")
    _require(set(document) == CHOICE_DOCUMENT_KEYS, f"{label} has invalid fields")
    _require(
        document["version"] == CHOICE_DOCUMENT_VERSION,
        f"{label} has unsupported ChoiceDocument version",
    )
    _require(document["type"] == CHOICE_DOCUMENT_TYPE, f"{label}.type must be 2")
    _require(
        document["shuffleOptions"] is False,
        f"{label}.shuffleOptions must be false",
    )
    _require(
        isinstance(document["question"], list)
        and len(document["question"]) == 1,
        f"{label}.question must contain exactly one text block",
    )
    _require(
        isinstance(document["options"], list)
        and 2 <= len(document["options"]) <= MAX_CHOICE_OPTIONS,
        f"{label}.options must contain 2-{MAX_CHOICE_OPTIONS} text blocks",
    )
    _require(
        isinstance(document["note"], list)
        and len(document["note"]) <= 1,
        f"{label}.note must contain zero or one text block",
    )

    seen_block_ids = set()
    question = _validate_choice_block(
        document["question"][0], f"{label}.question[0]", seen_block_ids
    )
    options = [
        _validate_choice_block(
            block, f"{label}.options[{option_index}]", seen_block_ids
        )
        for option_index, block in enumerate(document["options"])
    ]
    notes = [
        _validate_choice_block(
            block, f"{label}.note[{note_index}]", seen_block_ids
        )
        for note_index, block in enumerate(document["note"])
    ]
    option_contents = [option["content"] for option in options]
    _require(
        len(set(option_contents)) == len(option_contents),
        f"{label}.options contains duplicate content",
    )

    correct_ids = document["correctOptionIDSet"]
    _require(
        isinstance(correct_ids, list) and correct_ids,
        f"{label}.correctOptionIDSet must be a non-empty array",
    )
    _require(
        all(isinstance(item, str) for item in correct_ids)
        and len(set(correct_ids)) == len(correct_ids),
        f"{label}.correctOptionIDSet contains invalid or duplicate IDs",
    )
    option_ids = {option["id"] for option in options}
    _require(
        set(correct_ids).issubset(option_ids),
        f"{label}.correctOptionIDSet references a non-option block",
    )
    _require(
        card["sidea"] == question["content"],
        f"{label}.question does not match sidea",
    )
    _require(
        card["sideb"] == "\n".join(option_contents),
        f"{label}.options do not match sideb",
    )
    span_count = sum(
        block["span_count"] for block in [question] + options + notes
    )
    has_occlusion = any(
        block["has_occlusion"] for block in [question] + options + notes
    )
    return {
        "document_type": "choice",
        "span_count": span_count,
        "attachments_by_side": {"sidea": [], "sideb": []},
        "expected_flag": CARD_FLAG_OCCLUSION if has_occlusion else 0,
        "option_count": len(options),
        "multiple_choice": len(correct_ids) > 1,
    }


def _decode_document(card, index):
    encoded = card["rtf"]
    _require(isinstance(encoded, str) and encoded, f"cards[{index}].rtf is invalid")
    try:
        raw_document = base64.b64decode(encoded, validate=True)
        document = json.loads(raw_document.decode("utf-8"))
    except (binascii.Error, UnicodeError, json.JSONDecodeError) as error:
        raise ValidationError(f"cards[{index}].rtf is not valid Base64 JSON") from error

    _require(
        isinstance(document, dict),
        f"cards[{index}].rtf root must be an object",
    )
    document_type = document.get("type", NOTE_DOCUMENT_TYPE)
    if document_type == NOTE_DOCUMENT_TYPE:
        return _validate_note_document(card, index, document)
    if document_type == CHOICE_DOCUMENT_TYPE:
        return _validate_choice_document(card, index, document)
    raise ValidationError(f"cards[{index}].rtf has unsupported document type")


def _validate_attachment_list(value, label):
    _require(isinstance(value, list), f"{label} must be an array")
    _require(
        len(value) <= MAX_ATTACHMENTS_PER_SIDE,
        f"{label} exceeds the {MAX_ATTACHMENTS_PER_SIDE}-image limit",
    )
    _require(len(set(value)) == len(value), f"{label} contains duplicates")
    for index, filename in enumerate(value):
        _require(
            isinstance(filename, str)
            and ATTACHMENT_FILENAME_PATTERN.fullmatch(filename),
            f"{label}[{index}] is invalid",
        )
    return value


def _validate_tag_vo(value, label):
    _require(isinstance(value, dict), f"{label} must be an object")
    _require(set(value) == TAG_KEYS, f"{label} has unexpected fields")
    path = value["name"]
    _require(
        isinstance(path, str) and path.strip(),
        f"{label}.name must not be empty",
    )
    components = path.split(TAG_PATH_SEPARATOR)
    _require(
        len(components) <= MAX_TAG_DEPTH,
        f"{label}.name exceeds the {MAX_TAG_DEPTH}-level limit",
    )
    for index, component in enumerate(components):
        _require(
            component.strip() == component and component,
            f"{label}.name component {index} is empty or untrimmed",
        )
        _require(
            len(component) <= MAX_TAG_NAME_LENGTH,
            f"{label}.name component {index} exceeds "
            f"{MAX_TAG_NAME_LENGTH} characters",
        )
        _require(
            "\x00" not in component
            and "\n" not in component
            and "\r" not in component
            and ATTACHMENT_CHARACTER not in component,
            f"{label}.name component {index} contains a reserved character",
        )
    _validate_color(value["lighthex"], f"{label}.lighthex")
    return path, components


def _validate_tags(value):
    _require(isinstance(value, list) and value, "tags must be a non-empty array")
    _require(len(value) <= MAX_TAGS, f"tags exceeds the {MAX_TAGS}-tag limit")
    definitions = {}
    components_by_path = {}
    for index, tag in enumerate(value):
        label = f"tags[{index}]"
        path, components = _validate_tag_vo(tag, label)
        _require(path not in definitions, f"{label}.name is duplicated")
        definitions[path] = tag
        components_by_path[path] = components

    for path, components in components_by_path.items():
        if len(components) == 1:
            continue
        parent_path = TAG_PATH_SEPARATOR.join(components[:-1])
        _require(
            parent_path in definitions,
            f"tag {path!r} is missing parent definition {parent_path!r}",
        )
    return definitions


def _validate_pack_content(content):
    _require(isinstance(content, dict), "content.json root must be an object")
    _require(
        PACK_REQUIRED_KEYS.issubset(content)
        and set(content).issubset(PACK_REQUIRED_KEYS | PACK_OPTIONAL_KEYS),
        "content.json has missing or unexpected pack fields",
    )
    _require(
        isinstance(content["name"], str) and content["name"].strip(),
        "pack name must not be empty",
    )
    _require(
        content["version"] == APP_DOCUMENT_VERSION,
        "unsupported CardPackVO version",
    )
    cards = content["cards"]
    _require(isinstance(cards, list) and cards, "cards must be a non-empty array")
    tag_definitions = (
        _validate_tags(content["tags"]) if "tags" in content else {}
    )

    seen_uuids = set()
    seen_pairs = set()
    span_count = 0
    attachment_count = 0
    tagged_card_count = 0
    note_card_count = 0
    choice_card_count = 0
    choice_option_count = 0
    single_choice_count = 0
    multiple_choice_count = 0
    media_filenames = set()
    for index, card in enumerate(cards):
        _require(isinstance(card, dict), f"cards[{index}] must be an object")
        _require(
            CARD_REQUIRED_KEYS.issubset(card)
            and set(card).issubset(CARD_REQUIRED_KEYS | CARD_OPTIONAL_KEYS),
            f"cards[{index}] has missing or unexpected fields",
        )
        _require(
            isinstance(card["uuid"], str) and UUID_PATTERN.fullmatch(card["uuid"]),
            f"cards[{index}].uuid is invalid",
        )
        _require(card["uuid"] not in seen_uuids, f"cards[{index}].uuid is duplicated")
        seen_uuids.add(card["uuid"])

        for field in ("sidea", "sideb"):
            _require(
                isinstance(card[field], str) and card[field].strip(),
                f"cards[{index}].{field} must not be empty",
            )
        _require(type(card["flag"]) is int, f"cards[{index}].flag must be an integer")
        sidea_attachments = _validate_attachment_list(
            card["sideaAttIds"], f"cards[{index}].sideaAttIds"
        )
        sideb_attachments = _validate_attachment_list(
            card["sidebAttIds"], f"cards[{index}].sidebAttIds"
        )
        pair = (
            card["sidea"],
            tuple(sidea_attachments),
            card["sideb"],
            tuple(sideb_attachments),
        )
        _require(pair not in seen_pairs, f"cards[{index}] duplicates an earlier card")
        seen_pairs.add(pair)
        _require(
            card["version"] == APP_DOCUMENT_VERSION,
            f"cards[{index}] has unsupported CardVO version",
        )
        if "tag" in card:
            tag_path, _ = _validate_tag_vo(card["tag"], f"cards[{index}].tag")
            _require(
                tag_path in tag_definitions,
                f"cards[{index}].tag is not defined by pack tags",
            )
            _require(
                card["tag"] == tag_definitions[tag_path],
                f"cards[{index}].tag does not match its pack definition",
            )
            tagged_card_count += 1
        document = _decode_document(card, index)
        span_count += document["span_count"]
        _require(
            card["flag"] == document["expected_flag"],
            f"cards[{index}].flag does not match its document content",
        )
        attachments_by_side = document["attachments_by_side"]
        _require(
            sidea_attachments == attachments_by_side["sidea"],
            f"cards[{index}] side A media list does not match its spans",
        )
        _require(
            sideb_attachments == attachments_by_side["sideb"],
            f"cards[{index}] side B media list does not match its spans",
        )
        if document["document_type"] == "choice":
            choice_card_count += 1
            choice_option_count += document["option_count"]
            if document["multiple_choice"]:
                multiple_choice_count += 1
            else:
                single_choice_count += 1
        else:
            note_card_count += 1
        for filename in sidea_attachments + sideb_attachments:
            _require(
                filename not in media_filenames,
                f"attachment filename is reused: {filename}",
            )
            media_filenames.add(filename)
            attachment_count += 1

    summary = {
        "name": content["name"],
        "card_count": len(cards),
        "note_card_count": note_card_count,
        "choice_card_count": choice_card_count,
        "choice_option_count": choice_option_count,
        "single_choice_count": single_choice_count,
        "multiple_choice_count": multiple_choice_count,
        "span_count": span_count,
        "attachment_count": attachment_count,
        "rich_image_count": 0,
        "image_occlusion_count": 0,
        "tag_count": len(tag_definitions),
        "tagged_card_count": tagged_card_count,
    }
    return summary, media_filenames


def _validate_content(content):
    _require(isinstance(content, dict), "content.json root must be an object")
    if CARD_REQUIRED_KEYS.issubset(content):
        _require(
            set(content) == CARD_REQUIRED_KEYS,
            "standalone card has missing or unexpected fields",
        )
        summary, media_filenames = _validate_pack_content(
            {
                "name": "Standalone card",
                "cards": [content],
                "version": APP_DOCUMENT_VERSION,
            }
        )
        summary["name"] = None
        summary["product"] = "card"
        return summary, media_filenames

    summary, media_filenames = _validate_pack_content(content)
    summary["product"] = "pack"
    return summary, media_filenames


def validate_wink(path):
    _require(path.suffix.lower() == ".wink", "filename must end in .wink")
    _require(path.is_file(), f"file not found: {path}")
    _require(zipfile.is_zipfile(path), "file is not a ZIP archive")

    with zipfile.ZipFile(path, mode="r") as archive:
        infos = archive.infolist()
        for info in infos:
            _validate_archive_entry(info)
        _require(infos, "archive is empty")
        _require(
            infos[0].filename == "content.json",
            "content.json must be the first root-level entry",
        )
        info = infos[0]
        _require(
            info.file_size <= MAX_CONTENT_JSON_BYTES,
            "content.json exceeds the safety limit",
        )
        try:
            raw_content = archive.read(info)
        except RuntimeError as error:
            raise ValidationError(f"cannot read content.json: {error}") from error
        try:
            content = json.loads(raw_content.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as error:
            raise ValidationError("content.json must be valid UTF-8 JSON") from error
        summary, referenced_media = _validate_content(content)

        media_infos = infos[1:]
        archive_media = set()
        total_media_bytes = 0
        for media_info in media_infos:
            _require(
                media_info.filename.startswith("media/")
                and media_info.filename.count("/") == 1,
                f"unexpected archive entry: {media_info.filename}",
            )
            filename = media_info.filename.removeprefix("media/")
            match = ATTACHMENT_FILENAME_PATTERN.fullmatch(filename)
            _require(match is not None, f"invalid media filename: {filename}")
            _require(filename not in archive_media, f"duplicate media file: {filename}")
            archive_media.add(filename)
            _require(
                media_info.file_size
                <= max(MAX_IMAGE_BYTES, MAX_RICH_IMAGE_BYTES),
                f"media/{filename} exceeds the media size limit",
            )
            total_media_bytes += media_info.file_size
            _require(
                total_media_bytes <= MAX_TOTAL_MEDIA_BYTES,
                "total media size exceeds the 512 MiB limit",
            )
            data = archive.read(media_info)
            extension = match.group(2)
            if extension == RICH_IMAGE_EXTENSION:
                rich_image = validate_rich_image_bytes(
                    data,
                    match.group(1),
                    f"media/{filename}",
                )
                summary["rich_image_count"] += 1
                summary["image_occlusion_count"] += rich_image["mask_count"]
            else:
                validate_image_bytes(data, extension, f"media/{filename}")

        _require(
            archive_media == referenced_media,
            "media files do not exactly match card attachment references",
        )
    return summary


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description=(
            "Validate a mixed NoteLegacy/Choice WinkNotes .wink pack "
            "or standalone card."
        )
    )
    parser.add_argument("wink", type=Path, help=".wink file to validate")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        summary = validate_wink(args.wink)
    except (
        ImageFormatError,
        RichImageFormatError,
        ValidationError,
        OSError,
        zipfile.BadZipFile,
    ) as error:
        print(f"INVALID: {error}", file=sys.stderr)
        return 1
    if summary["product"] == "card":
        print(
            "VALID: standalone "
            f"{'choice' if summary['choice_card_count'] else 'note'} card, "
            f"{summary['span_count']} spans, "
            f"{summary['choice_option_count']} choice options, "
            f"{summary['attachment_count']} image attachments "
            f"({summary['rich_image_count']} native RichImages, "
            f"{summary['image_occlusion_count']} occlusions)"
        )
    else:
        print(
            f"VALID: pack {summary['name']!r}, {summary['card_count']} cards "
            f"({summary['note_card_count']} note, "
            f"{summary['choice_card_count']} choice), "
            f"{summary['span_count']} spans, "
            f"{summary['choice_option_count']} choice options "
            f"({summary['single_choice_count']} single, "
            f"{summary['multiple_choice_count']} multiple), "
            f"{summary['attachment_count']} image attachments "
            f"({summary['rich_image_count']} native RichImages, "
            f"{summary['image_occlusion_count']} occlusions), "
            f"{summary['tag_count']} tags, "
            f"{summary['tagged_card_count']} tagged cards"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
