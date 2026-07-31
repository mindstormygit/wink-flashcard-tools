#!/usr/bin/env python3
"""Build a mixed NoteLegacy/Choice WinkNotes pack or card as a .wink."""

import argparse
import base64
import json
import re
import sys
import uuid
import zipfile
from pathlib import Path
from urllib.parse import urlsplit

from image_support import ImageFormatError, validate_image_file
from rich_image_support import (
    RICH_IMAGE_EXTENSION,
    RichImageFormatError,
    build_rich_image,
)
from validate_wink import ValidationError, validate_wink


APP_DOCUMENT_VERSION = 6
NOTE_DOCUMENT_VERSION = 3
CHOICE_DOCUMENT_VERSION = 100
NOTE_DOCUMENT_TYPE = 0
CHOICE_DOCUMENT_TYPE = 2
ROOT_KEYS = {"name", "cards", "tags"}
PRODUCT_CHOICES = ("auto", "pack", "card")
NOTE_CARD_KEYS = {"type", "front", "back", "tag"}
CHOICE_CARD_KEYS = {"type", "question", "options", "note", "tag"}
CHOICE_OPTION_KEYS = {"content", "correct"}
TAG_REQUIRED_KEYS = {"id", "name"}
TAG_OPTIONAL_KEYS = {"parent", "color"}
TEXT_SEGMENT_KEYS = {
    "text",
    "bold",
    "highlight",
    "textColor",
    "underline",
    "strikethrough",
    "script",
    "link",
}
IMAGE_SEGMENT_KEYS = {"image"}
RICH_IMAGE_SEGMENT_KEYS = {"richImage"}
RICH_IMAGE_PAYLOAD_KEYS = {"image", "masks"}
HEX_COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")
TAG_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
STYLE_UNDERLINE = 1
STYLE_BOLD = 1 << 1
STYLE_STRIKETHROUGH = 1 << 2
STYLE_HIGHLIGHT = 1 << 3
STYLE_SUPERSUBSCRIPT = 1 << 4
ATTACHMENT_CHARACTER = "\uFFFC"
MAX_ATTACHMENTS_PER_SIDE = 15
DEFAULT_TAG_COLOR = "#29B6F6"
TAG_PATH_SEPARATOR = "/$-#-$/"
MAX_TAGS = 500
MAX_TAG_DEPTH = 32
MAX_TAG_NAME_LENGTH = 200
MAX_CHOICE_OPTIONS = 26
DEFAULT_HIGHLIGHT_COLOR = "#FFF176"
CARD_FLAG_OCCLUSION = 1 << 1


class InputError(ValueError):
    """Raised when the agent-facing cards JSON is invalid."""


def _nonempty_text(value, label, allow_attachment_character=False):
    if not isinstance(value, str):
        raise InputError(f"{label} must be a string")
    if not value.strip():
        raise InputError(f"{label} must not be empty")
    if "\x00" in value:
        raise InputError(f"{label} must not contain NUL characters")
    if not allow_attachment_character and ATTACHMENT_CHARACTER in value:
        raise InputError(
            f"{label} must not contain the reserved U+FFFC attachment character"
        )
    return value


def _bool_field(segment, key, label):
    value = segment.get(key, False)
    if not isinstance(value, bool):
        raise InputError(f"{label}.{key} must be true or false")
    return value


def _hex_color(value, label):
    if not isinstance(value, str) or not HEX_COLOR_PATTERN.fullmatch(value):
        raise InputError(f"{label} must use #RRGGBB")
    return value.upper()


def _http_url(value, label):
    if not isinstance(value, str):
        raise InputError(f"{label} must be a string")
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise InputError(f"{label} must be an absolute HTTP or HTTPS URL")
    return value


def _tag_id(value, label):
    if not isinstance(value, str) or not TAG_ID_PATTERN.fullmatch(value):
        raise InputError(
            f"{label} must be 1-64 ASCII letters, digits, hyphens, or "
            "underscores, starting with a letter or digit"
        )
    return value


def _tag_name(value, label):
    name = _nonempty_text(value, label).strip()
    if len(name) > MAX_TAG_NAME_LENGTH:
        raise InputError(
            f"{label} exceeds the {MAX_TAG_NAME_LENGTH}-character limit"
        )
    if "\n" in name or "\r" in name:
        raise InputError(f"{label} must be a single line")
    if TAG_PATH_SEPARATOR in name:
        raise InputError(f"{label} contains WinkNotes' reserved tag separator")
    return name


def _normalize_tags(value):
    if not isinstance(value, list) or not value:
        raise InputError("tags must be a non-empty array when provided")
    if len(value) > MAX_TAGS:
        raise InputError(f"tags exceeds the {MAX_TAGS}-tag limit")

    normalized = []
    by_id = {}
    allowed_keys = TAG_REQUIRED_KEYS | TAG_OPTIONAL_KEYS
    for index, item in enumerate(value):
        label = f"tags[{index}]"
        if not isinstance(item, dict):
            raise InputError(f"{label} must be an object")
        if not TAG_REQUIRED_KEYS.issubset(item) or not set(item).issubset(
            allowed_keys
        ):
            raise InputError(
                f"{label} must contain id and name, plus only optional "
                "parent and color"
            )

        tag_id = _tag_id(item["id"], f"{label}.id")
        if tag_id in by_id:
            raise InputError(f"{label}.id duplicates {tag_id!r}")
        name = _tag_name(item["name"], f"{label}.name")
        parent = None
        if "parent" in item:
            parent = _tag_id(item["parent"], f"{label}.parent")
        color = _hex_color(
            item.get("color", DEFAULT_TAG_COLOR), f"{label}.color"
        )
        tag = {
            "id": tag_id,
            "name": name,
            "parent": parent,
            "color": color,
        }
        normalized.append(tag)
        by_id[tag_id] = tag

    for tag in normalized:
        parent = tag["parent"]
        if parent is not None and parent not in by_id:
            raise InputError(
                f"tag {tag['id']!r} references undefined parent {parent!r}"
            )

    visit_state = {}

    def resolve_path(tag_id):
        state = visit_state.get(tag_id, 0)
        if state == 1:
            raise InputError(f"tags contain a parent cycle involving {tag_id!r}")
        if state == 2:
            tag = by_id[tag_id]
            return tag["path"], tag["depth"]

        visit_state[tag_id] = 1
        tag = by_id[tag_id]
        if tag["parent"] is None:
            path = tag["name"]
            depth = 1
        else:
            parent_path, parent_depth = resolve_path(tag["parent"])
            path = f"{parent_path}{TAG_PATH_SEPARATOR}{tag['name']}"
            depth = parent_depth + 1
        if depth > MAX_TAG_DEPTH:
            raise InputError(
                f"tag {tag_id!r} exceeds the {MAX_TAG_DEPTH}-level limit"
            )
        tag["path"] = path
        tag["depth"] = depth
        tag["vo"] = {"name": path, "lighthex": tag["color"]}
        visit_state[tag_id] = 2
        return path, depth

    seen_paths = set()
    for tag in normalized:
        path, _ = resolve_path(tag["id"])
        if path in seen_paths:
            raise InputError(f"duplicate tag path: {path!r}")
        seen_paths.add(path)

    return normalized, by_id


def _utf16_length(value):
    try:
        return len(value.encode("utf-16-le")) // 2
    except UnicodeEncodeError as error:
        raise InputError("text contains an invalid Unicode surrogate") from error


def _same_span_style(lhs, rhs):
    lhs_style = {key: value for key, value in lhs.items() if key not in {"f", "l"}}
    rhs_style = {key: value for key, value in rhs.items() if key not in {"f", "l"}}
    return lhs_style == rhs_style


def _append_span(spans, span):
    if (
        spans
        and spans[-1]["f"] + spans[-1]["l"] == span["f"]
        and _same_span_style(spans[-1], span)
    ):
        spans[-1]["l"] += span["l"]
    else:
        spans.append(span)


def _styled_side(value, label, input_directory):
    if isinstance(value, str):
        return {"content": _nonempty_text(value, label), "spans": [], "images": []}
    if not isinstance(value, list) or not value:
        raise InputError(f"{label} must be a non-empty string or segment array")

    parts = []
    spans = []
    images = []
    offset = 0
    for index, segment in enumerate(value):
        segment_label = f"{label}[{index}]"
        if not isinstance(segment, dict):
            raise InputError(f"{segment_label} must be an object")

        has_text = "text" in segment
        has_image = "image" in segment
        has_rich_image = "richImage" in segment
        if sum((has_text, has_image, has_rich_image)) != 1:
            raise InputError(
                f"{segment_label} must contain exactly one of text, image, "
                "or richImage"
            )

        if has_image:
            unknown_keys = set(segment) - IMAGE_SEGMENT_KEYS
            if unknown_keys:
                raise InputError(
                    f"{segment_label} image segment has unsupported fields: "
                    + ", ".join(sorted(unknown_keys))
                )
            image_value = _nonempty_text(
                segment["image"], f"{segment_label}.image"
            )
            source_path = Path(image_value)
            if not source_path.is_absolute():
                source_path = input_directory / source_path
            resolved_path, extension = validate_image_file(
                source_path, f"{segment_label}.image"
            )
            attachment_id = uuid.uuid4().hex
            filename = f"{attachment_id}.{extension}"
            span = {
                "f": offset,
                "l": 1,
                "at": attachment_id,
                "aes": extension,
            }
            spans.append(span)
            images.append({"source": resolved_path, "filename": filename})
            parts.append(ATTACHMENT_CHARACTER)
            offset += 1
            continue

        if has_rich_image:
            unknown_keys = set(segment) - RICH_IMAGE_SEGMENT_KEYS
            if unknown_keys:
                raise InputError(
                    f"{segment_label} richImage segment has unsupported fields: "
                    + ", ".join(sorted(unknown_keys))
                )
            payload = segment["richImage"]
            if (
                not isinstance(payload, dict)
                or set(payload) != RICH_IMAGE_PAYLOAD_KEYS
            ):
                raise InputError(
                    f"{segment_label}.richImage must contain exactly image and masks"
                )
            image_value = _nonempty_text(
                payload["image"], f"{segment_label}.richImage.image"
            )
            source_path = Path(image_value)
            if not source_path.is_absolute():
                source_path = input_directory / source_path
            attachment_id = uuid.uuid4().hex
            rich_image_data, normalized_masks, resolved_path = build_rich_image(
                source_path,
                payload["masks"],
                attachment_id,
                f"{segment_label}.richImage",
            )
            filename = f"{attachment_id}.{RICH_IMAGE_EXTENSION}"
            span = {
                "f": offset,
                "l": 1,
                "at": attachment_id,
                "aes": RICH_IMAGE_EXTENSION,
            }
            spans.append(span)
            images.append(
                {
                    "source": resolved_path,
                    "data": rich_image_data,
                    "filename": filename,
                    "masks": normalized_masks,
                }
            )
            parts.append(ATTACHMENT_CHARACTER)
            offset += 1
            continue

        unknown_keys = set(segment) - TEXT_SEGMENT_KEYS
        if unknown_keys:
            raise InputError(
                f"{segment_label} has unsupported fields: "
                + ", ".join(sorted(unknown_keys))
            )

        text = _nonempty_text(segment.get("text"), f"{segment_label}.text")
        length = _utf16_length(text)
        style = 0
        span = {"f": offset, "l": length}

        if _bool_field(segment, "underline", segment_label):
            style |= STYLE_UNDERLINE
        if _bool_field(segment, "bold", segment_label):
            style |= STYLE_BOLD
        if _bool_field(segment, "strikethrough", segment_label):
            style |= STYLE_STRIKETHROUGH

        highlight = segment.get("highlight", False)
        if isinstance(highlight, bool):
            if highlight:
                style |= STYLE_HIGHLIGHT
        elif isinstance(highlight, str):
            style |= STYLE_HIGHLIGHT
            span["mc"] = _hex_color(highlight, f"{segment_label}.highlight")
        else:
            raise InputError(
                f"{segment_label}.highlight must be true, false, or #RRGGBB"
            )

        script = segment.get("script")
        if script is not None:
            if script == "superscript":
                span["sc"] = 1
            elif script == "subscript":
                span["sc"] = -1
            else:
                raise InputError(
                    f"{segment_label}.script must be superscript or subscript"
                )
            style |= STYLE_SUPERSUBSCRIPT

        if "textColor" in segment:
            span["c"] = _hex_color(
                segment["textColor"], f"{segment_label}.textColor"
            )
        if "link" in segment:
            span["lk"] = _http_url(segment["link"], f"{segment_label}.link")
        if style:
            span["s"] = style

        if len(span) > 2:
            _append_span(spans, span)
        parts.append(text)
        offset += length

    content = "".join(parts)
    _nonempty_text(content, label, allow_attachment_character=True)
    if len(images) > MAX_ATTACHMENTS_PER_SIDE:
        raise InputError(
            f"{label} has {len(images)} images; maximum is "
            f"{MAX_ATTACHMENTS_PER_SIDE}"
        )
    return {"content": content, "spans": spans, "images": images}


def _choice_text_payload(value, label):
    if isinstance(value, str):
        return {"content": _nonempty_text(value, label), "spans": []}
    if not isinstance(value, list) or not value:
        raise InputError(f"{label} must be a non-empty string or text segment array")

    parts = []
    spans = []
    offset = 0
    for index, segment in enumerate(value):
        segment_label = f"{label}[{index}]"
        if not isinstance(segment, dict):
            raise InputError(f"{segment_label} must be an object")
        if "text" not in segment:
            raise InputError(
                f"{segment_label} must be a text segment; choice-card images "
                "are not supported yet"
            )
        unknown_keys = set(segment) - TEXT_SEGMENT_KEYS
        if unknown_keys:
            raise InputError(
                f"{segment_label} has unsupported fields: "
                + ", ".join(sorted(unknown_keys))
            )
        if _bool_field(segment, "underline", segment_label):
            raise InputError(
                f"{segment_label}.underline is not supported by ChoiceDocument"
            )
        if segment.get("script") is not None:
            raise InputError(
                f"{segment_label}.script is not supported by ChoiceDocument"
            )

        text = _nonempty_text(segment["text"], f"{segment_label}.text")
        length = _utf16_length(text)
        span = {
            "f": offset,
            "l": length,
            "ft": 1 if _bool_field(segment, "bold", segment_label) else 0,
            "st": _bool_field(segment, "strikethrough", segment_label),
        }
        highlight = segment.get("highlight", False)
        if isinstance(highlight, bool):
            if highlight:
                span["bc"] = DEFAULT_HIGHLIGHT_COLOR
        elif isinstance(highlight, str):
            span["bc"] = _hex_color(
                highlight, f"{segment_label}.highlight"
            )
        else:
            raise InputError(
                f"{segment_label}.highlight must be true, false, or #RRGGBB"
            )
        if "textColor" in segment:
            span["c"] = _hex_color(
                segment["textColor"], f"{segment_label}.textColor"
            )
        if "link" in segment:
            span["lk"] = _http_url(segment["link"], f"{segment_label}.link")

        if span["ft"] or span["st"] or any(
            key in span for key in ("bc", "c", "lk")
        ):
            _append_span(spans, span)
        parts.append(text)
        offset += length

    content = "".join(parts)
    _nonempty_text(content, label)
    return {"content": content, "spans": spans}


def _card_tag(card, label, tags_by_id):
    if "tag" not in card:
        return None
    tag_id = _tag_id(card["tag"], f"{label}.tag")
    if tag_id not in tags_by_id:
        raise InputError(f"{label}.tag references undefined tag {tag_id!r}")
    return tags_by_id[tag_id]["vo"]


def _note_card_signature(front, back):
    return (
        "note",
        front["content"],
        tuple(
            (
                str(image["source"]),
                tuple(
                    tuple(sorted(mask.items()))
                    for mask in image.get("masks", [])
                ),
            )
            for image in front["images"]
        ),
        back["content"],
        tuple(
            (
                str(image["source"]),
                tuple(
                    tuple(sorted(mask.items()))
                    for mask in image.get("masks", [])
                ),
            )
            for image in back["images"]
        ),
    )


def _normalize_note_card(card, label, input_directory, tags_by_id):
    unknown_keys = set(card) - NOTE_CARD_KEYS
    if unknown_keys:
        raise InputError(
            f"{label} note card has unsupported fields: "
            + ", ".join(sorted(unknown_keys))
        )
    front = _styled_side(
        card.get("front"), f"{label}.front", input_directory
    )
    back = _styled_side(card.get("back"), f"{label}.back", input_directory)
    return {
        "type": "note",
        "front": front,
        "back": back,
        "tag": _card_tag(card, label, tags_by_id),
        "signature": _note_card_signature(front, back),
    }


def _normalize_choice_card(card, label, tags_by_id):
    unknown_keys = set(card) - CHOICE_CARD_KEYS
    if unknown_keys:
        raise InputError(
            f"{label} choice card has unsupported fields: "
            + ", ".join(sorted(unknown_keys))
        )
    question = _choice_text_payload(card.get("question"), f"{label}.question")
    options_value = card.get("options")
    if not isinstance(options_value, list):
        raise InputError(f"{label}.options must be an array")
    if not 2 <= len(options_value) <= MAX_CHOICE_OPTIONS:
        raise InputError(
            f"{label}.options must contain 2-{MAX_CHOICE_OPTIONS} options"
        )

    options = []
    seen_option_content = set()
    for index, item in enumerate(options_value):
        option_label = f"{label}.options[{index}]"
        if not isinstance(item, dict) or set(item) != CHOICE_OPTION_KEYS:
            raise InputError(
                f"{option_label} must contain exactly content and correct"
            )
        if not isinstance(item["correct"], bool):
            raise InputError(f"{option_label}.correct must be true or false")
        payload = _choice_text_payload(
            item["content"], f"{option_label}.content"
        )
        if payload["content"] in seen_option_content:
            raise InputError(f"{option_label}.content duplicates an earlier option")
        seen_option_content.add(payload["content"])
        options.append(
            {
                "id": uuid.uuid4().hex,
                "payload": payload,
                "correct": item["correct"],
            }
        )
    if not any(option["correct"] for option in options):
        raise InputError(f"{label}.options must mark at least one correct option")

    note = None
    if "note" in card:
        note = _choice_text_payload(card["note"], f"{label}.note")
    signature = (
        "choice",
        question["content"],
        tuple(
            (option["payload"]["content"], option["correct"])
            for option in options
        ),
        note["content"] if note is not None else "",
    )
    return {
        "type": "choice",
        "question": question,
        "options": options,
        "note": note,
        "tag": _card_tag(card, label, tags_by_id),
        "signature": signature,
    }


def load_source(path, product="auto"):
    try:
        source = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise InputError(f"cannot read input: {error}") from error
    except (UnicodeError, json.JSONDecodeError) as error:
        raise InputError(f"input must be valid UTF-8 JSON: {error}") from error

    if not isinstance(source, dict):
        raise InputError("input root must be an object")
    if product not in PRODUCT_CHOICES:
        raise InputError(
            "product must be one of " + ", ".join(PRODUCT_CHOICES)
        )
    unknown_root_keys = set(source) - ROOT_KEYS
    if unknown_root_keys:
        raise InputError(
            "unsupported root fields: " + ", ".join(sorted(unknown_root_keys))
        )

    cards = source.get("cards")
    if not isinstance(cards, list) or not cards:
        raise InputError("cards must be a non-empty array")
    resolved_product = (
        "card" if product == "auto" and len(cards) == 1 else product
    )
    if resolved_product == "auto":
        resolved_product = "pack"
    if resolved_product == "card" and len(cards) != 1:
        raise InputError("standalone card output requires exactly one card")

    if resolved_product == "card":
        unsupported = {"name", "tags"} & set(source)
        if unsupported:
            raise InputError(
                "standalone card input does not support root fields: "
                + ", ".join(sorted(unsupported))
            )
        name = None
        normalized_tags, tags_by_id = [], {}
    else:
        name = _nonempty_text(source.get("name"), "name")
        if "tags" in source:
            normalized_tags, tags_by_id = _normalize_tags(source["tags"])
        else:
            normalized_tags, tags_by_id = [], {}
    input_directory = path.parent.resolve()
    normalized_cards = []
    seen_pairs = set()
    for index, card in enumerate(cards):
        label = f"cards[{index}]"
        if not isinstance(card, dict):
            raise InputError(f"{label} must be an object")
        if resolved_product == "card" and "tag" in card:
            raise InputError("standalone cards do not carry pack tags")
        card_type = card.get("type", "note")
        if card_type == "note":
            normalized = _normalize_note_card(
                card, label, input_directory, tags_by_id
            )
        elif card_type == "choice":
            normalized = _normalize_choice_card(card, label, tags_by_id)
        else:
            raise InputError(f"{label}.type must be note or choice")

        if normalized["signature"] in seen_pairs:
            raise InputError(f"{label} duplicates an earlier card")
        seen_pairs.add(normalized["signature"])
        del normalized["signature"]
        normalized_cards.append(normalized)

    return {
        "name": name,
        "cards": normalized_cards,
        "tags": [tag["vo"] for tag in normalized_tags],
        "product": resolved_product,
    }


def _note_content(side):
    result = {"c": side["content"]}
    if side["spans"]:
        result["a"] = side["spans"]
    return result


def _note_document(front, back):
    return {
        "v": NOTE_DOCUMENT_VERSION,
        "sa": _note_content(front),
        "sb": _note_content(back),
    }


def _block_node(payload, block_id):
    content = {"type": 0, "payload": {"c": payload["content"]}}
    if payload["spans"]:
        content["payload"]["s"] = payload["spans"]
    return {
        "id": block_id,
        "content": content,
        "children": [],
        "createdAt": 0,
    }


def _choice_document(card):
    option_blocks = [
        _block_node(option["payload"], option["id"])
        for option in card["options"]
    ]
    note_blocks = (
        [_block_node(card["note"], uuid.uuid4().hex)]
        if card["note"] is not None
        else []
    )
    return {
        "version": CHOICE_DOCUMENT_VERSION,
        "question": [_block_node(card["question"], uuid.uuid4().hex)],
        "options": option_blocks,
        "note": note_blocks,
        "correctOptionIDSet": [
            option["id"] for option in card["options"] if option["correct"]
        ],
        "shuffleOptions": False,
        "type": CHOICE_DOCUMENT_TYPE,
    }


def _note_card_vo(card):
    front = card["front"]
    back = card["back"]
    note_data = json.dumps(
        _note_document(front, back),
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    result = {
        "uuid": uuid.uuid4().hex,
        "sidea": front["content"],
        "sideb": back["content"],
        "flag": 0,
        "rtf": base64.b64encode(note_data).decode("ascii"),
        "sideaAttIds": [image["filename"] for image in front["images"]],
        "sidebAttIds": [image["filename"] for image in back["images"]],
        "version": APP_DOCUMENT_VERSION,
    }
    if card["tag"] is not None:
        result["tag"] = card["tag"]
    return result


def _choice_card_vo(card):
    document = _choice_document(card)
    document_data = json.dumps(
        document,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    has_occlusion = any(
        "bc" in span
        for payload in (
            [card["question"]]
            + [option["payload"] for option in card["options"]]
            + ([card["note"]] if card["note"] is not None else [])
        )
        for span in payload["spans"]
    )
    result = {
        "uuid": uuid.uuid4().hex,
        "sidea": card["question"]["content"],
        "sideb": "\n".join(
            option["payload"]["content"] for option in card["options"]
        ),
        "flag": CARD_FLAG_OCCLUSION if has_occlusion else 0,
        "rtf": base64.b64encode(document_data).decode("ascii"),
        "sideaAttIds": [],
        "sidebAttIds": [],
        "version": APP_DOCUMENT_VERSION,
    }
    if card["tag"] is not None:
        result["tag"] = card["tag"]
    return result


def build_pack(source):
    card_vos = []
    images = []
    for card in source["cards"]:
        if card["type"] == "choice":
            card_vos.append(_choice_card_vo(card))
        else:
            card_vos.append(_note_card_vo(card))
            images.extend(card["front"]["images"])
            images.extend(card["back"]["images"])
    pack = {
        "name": source["name"],
        "cards": card_vos,
        "version": APP_DOCUMENT_VERSION,
    }
    if source["tags"]:
        pack["tags"] = source["tags"]
    return pack, images


def build_card(source):
    card = source["cards"][0]
    if card["type"] == "choice":
        return _choice_card_vo(card), []
    return (
        _note_card_vo(card),
        card["front"]["images"] + card["back"]["images"],
    )


def build_artifact(source, product):
    if product == "card":
        return build_card(source)
    return build_pack(source)


def write_wink(content_root, images, output_path):
    if output_path.suffix.lower() != ".wink":
        raise InputError("output filename must end in .wink")
    if output_path.exists():
        raise FileExistsError(f"output already exists: {output_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(
        content_root,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    archive = zipfile.ZipFile(
        output_path,
        mode="x",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    )
    try:
        with archive:
            archive.writestr("content.json", content)
            for image in images:
                archive.writestr(
                    f"media/{image['filename']}",
                    (
                        image["data"]
                        if "data" in image
                        else image["source"].read_bytes()
                    ),
                )
    except Exception:
        output_path.unlink(missing_ok=True)
        raise


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description=(
            "Build an unencrypted mixed NoteLegacy/Choice WinkNotes "
            ".wink pack or standalone card."
        )
    )
    parser.add_argument("input", type=Path, help="UTF-8 cards JSON")
    parser.add_argument("output", type=Path, help="new .wink output path")
    parser.add_argument(
        "--product",
        choices=PRODUCT_CHOICES,
        default="auto",
        help="artifact root type (default: auto by final card count)",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    output_created = False
    try:
        source = load_source(args.input, args.product)
        content_root, images = build_artifact(source, source["product"])
        write_wink(content_root, images, args.output)
        output_created = True
        summary = validate_wink(args.output)
    except (
        InputError,
        ImageFormatError,
        RichImageFormatError,
        ValidationError,
        FileExistsError,
        OSError,
        UnicodeError,
        zipfile.BadZipFile,
    ) as error:
        if output_created:
            try:
                args.output.unlink(missing_ok=True)
            except OSError:
                pass
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if summary["product"] == "card":
        print(
            f"Created {args.output} — standalone "
            f"{'choice' if summary['choice_card_count'] else 'note'} card, "
            f"{summary['span_count']} spans, "
            f"{summary['choice_option_count']} choice options, "
            f"{summary['attachment_count']} image attachments "
            f"({summary['rich_image_count']} native RichImages, "
            f"{summary['image_occlusion_count']} occlusions)"
        )
    else:
        print(
            f"Created {args.output} — pack {summary['name']!r}, "
            f"{summary['card_count']} cards "
            f"({summary['note_card_count']} note, "
            f"{summary['choice_card_count']} choice), "
            f"{summary['span_count']} spans, "
            f"{summary['choice_option_count']} choice options, "
            f"{summary['attachment_count']} image attachments "
            f"({summary['rich_image_count']} native RichImages, "
            f"{summary['image_occlusion_count']} occlusions), "
            f"{summary['tag_count']} tags, "
            f"{summary['tagged_card_count']} tagged cards"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
