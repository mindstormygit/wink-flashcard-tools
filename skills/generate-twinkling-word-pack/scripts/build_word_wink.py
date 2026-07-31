#!/usr/bin/env python3
"""Build an unencrypted WinkNotes WordDocument .wink pack or card."""

import argparse
import base64
import json
import re
import sys
import uuid
import zipfile
from pathlib import Path

from validate_word_wink import ValidationError, validate_word_wink


APP_DOCUMENT_VERSION = 6
WORD_DOCUMENT_VERSION = 100
WORD_DOCUMENT_TYPE = 3
SUPPORTED_LANG_CODES = {"en", "ja", "ko", "de", "fr", "es", "pt", "it"}
ROOT_KEYS = {"name", "langCode", "words", "tags"}
PRODUCT_CHOICES = ("auto", "pack", "card")
WORD_REQUIRED_KEYS = {"word", "definition"}
WORD_OPTIONAL_KEYS = {"phonetic", "examples", "extras", "tag"}
EXAMPLE_KEYS = {"sentence", "translation"}
EXTRA_REQUIRED_KEYS = {"label", "content"}
EXTRA_OPTIONAL_KEYS = {"templateKey"}
TAG_REQUIRED_KEYS = {"id", "name"}
TAG_OPTIONAL_KEYS = {"parent", "color"}
TAG_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
HEX_COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")
TAG_PATH_SEPARATOR = "/$-#-$/"
DEFAULT_TAG_COLOR = "#29B6F6"
MAX_WORDS = 5000
MAX_EXAMPLES = 5
MAX_EXTRAS = 20
MAX_TAGS = 500
MAX_TAG_DEPTH = 32
MAX_TAG_NAME_LENGTH = 200
TEMPLATE_KEYS_BY_LANGUAGE = {
    "en": {"en.syllable"},
    "ja": {"ja.kana", "ja.romaji", "ja.accent"},
    "ko": {"ko.romanization"},
    "de": {"de.article", "de.plural_form"},
    "fr": {"fr.article", "fr.plural_form"},
    "es": {"es.article", "es.plural_form"},
    "pt": {"pt.article", "pt.plural_form"},
    "it": {"it.article", "it.plural_form"},
}


class InputError(ValueError):
    """Raised when the agent-facing words JSON is invalid."""


def _text(value, label, *, max_length, allow_empty=False, single_line=False):
    if not isinstance(value, str):
        raise InputError(f"{label} must be a string")
    value = value.strip()
    if not allow_empty and not value:
        raise InputError(f"{label} must not be empty")
    if len(value) > max_length:
        raise InputError(f"{label} exceeds the {max_length}-character limit")
    if "\x00" in value or "\uFFFC" in value:
        raise InputError(f"{label} contains a reserved character")
    if single_line and ("\n" in value or "\r" in value):
        raise InputError(f"{label} must be a single line")
    return value


def _color(value, label):
    if not isinstance(value, str) or not HEX_COLOR_PATTERN.fullmatch(value):
        raise InputError(f"{label} must use #RRGGBB")
    return value.upper()


def _tag_id(value, label):
    if not isinstance(value, str) or not TAG_ID_PATTERN.fullmatch(value):
        raise InputError(
            f"{label} must be 1-64 ASCII letters, digits, hyphens, or "
            "underscores, starting with a letter or digit"
        )
    return value


def _normalize_tags(value):
    if not isinstance(value, list) or not value:
        raise InputError("tags must be a non-empty array when provided")
    if len(value) > MAX_TAGS:
        raise InputError(f"tags exceeds the {MAX_TAGS}-tag limit")

    tags = []
    by_id = {}
    allowed_keys = TAG_REQUIRED_KEYS | TAG_OPTIONAL_KEYS
    for index, item in enumerate(value):
        label = f"tags[{index}]"
        if (
            not isinstance(item, dict)
            or not TAG_REQUIRED_KEYS.issubset(item)
            or not set(item).issubset(allowed_keys)
        ):
            raise InputError(
                f"{label} must contain id and name, plus only optional "
                "parent and color"
            )
        tag_id = _tag_id(item["id"], f"{label}.id")
        if tag_id in by_id:
            raise InputError(f"{label}.id duplicates {tag_id!r}")
        name = _text(
            item["name"],
            f"{label}.name",
            max_length=MAX_TAG_NAME_LENGTH,
            single_line=True,
        )
        if TAG_PATH_SEPARATOR in name:
            raise InputError(f"{label}.name contains WinkNotes' reserved separator")
        parent = (
            _tag_id(item["parent"], f"{label}.parent")
            if "parent" in item
            else None
        )
        tag = {
            "id": tag_id,
            "name": name,
            "parent": parent,
            "color": _color(
                item.get("color", DEFAULT_TAG_COLOR), f"{label}.color"
            ),
        }
        tags.append(tag)
        by_id[tag_id] = tag

    for tag in tags:
        if tag["parent"] is not None and tag["parent"] not in by_id:
            raise InputError(
                f"tag {tag['id']!r} references undefined parent "
                f"{tag['parent']!r}"
            )

    state = {}

    def resolve(tag_id):
        if state.get(tag_id) == 1:
            raise InputError(f"tags contain a cycle involving {tag_id!r}")
        if state.get(tag_id) == 2:
            return by_id[tag_id]["path"], by_id[tag_id]["depth"]
        state[tag_id] = 1
        tag = by_id[tag_id]
        if tag["parent"] is None:
            path, depth = tag["name"], 1
        else:
            parent_path, parent_depth = resolve(tag["parent"])
            path = f"{parent_path}{TAG_PATH_SEPARATOR}{tag['name']}"
            depth = parent_depth + 1
        if depth > MAX_TAG_DEPTH:
            raise InputError(
                f"tag {tag_id!r} exceeds the {MAX_TAG_DEPTH}-level limit"
            )
        tag["path"] = path
        tag["depth"] = depth
        tag["vo"] = {"name": path, "lighthex": tag["color"]}
        state[tag_id] = 2
        return path, depth

    seen_paths = set()
    for tag in tags:
        path, _ = resolve(tag["id"])
        if path in seen_paths:
            raise InputError(f"duplicate tag path: {path!r}")
        seen_paths.add(path)
    return tags, by_id


def _normalize_examples(value, label):
    if value is None:
        return []
    if not isinstance(value, list):
        raise InputError(f"{label} must be an array")
    if len(value) > MAX_EXAMPLES:
        raise InputError(f"{label} exceeds the {MAX_EXAMPLES}-example limit")
    result = []
    seen = set()
    for index, item in enumerate(value):
        item_label = f"{label}[{index}]"
        if not isinstance(item, dict) or set(item) != EXAMPLE_KEYS:
            raise InputError(
                f"{item_label} must contain exactly sentence and translation"
            )
        sentence = _text(
            item["sentence"], f"{item_label}.sentence", max_length=2000
        )
        translation = _text(
            item["translation"],
            f"{item_label}.translation",
            max_length=2000,
            allow_empty=True,
        )
        signature = (sentence.casefold(), translation.casefold())
        if signature in seen:
            raise InputError(f"{item_label} duplicates an earlier example")
        seen.add(signature)
        result.append(
            {
                "id": uuid.uuid4().hex,
                "sentence": sentence,
                "translation": translation,
            }
        )
    return result


def _normalize_extras(value, label, lang_code):
    if value is None:
        return []
    if not isinstance(value, list):
        raise InputError(f"{label} must be an array")
    if len(value) > MAX_EXTRAS:
        raise InputError(f"{label} exceeds the {MAX_EXTRAS}-field limit")
    result = []
    seen_labels = set()
    seen_template_keys = set()
    allowed_keys = EXTRA_REQUIRED_KEYS | EXTRA_OPTIONAL_KEYS
    allowed_template_keys = TEMPLATE_KEYS_BY_LANGUAGE[lang_code]
    for index, item in enumerate(value):
        item_label = f"{label}[{index}]"
        if (
            not isinstance(item, dict)
            or not EXTRA_REQUIRED_KEYS.issubset(item)
            or not set(item).issubset(allowed_keys)
        ):
            raise InputError(
                f"{item_label} must contain label and content, plus only "
                "optional templateKey"
            )
        field_label = _text(
            item["label"],
            f"{item_label}.label",
            max_length=100,
            single_line=True,
        )
        label_key = field_label.casefold()
        if label_key in seen_labels:
            raise InputError(f"{item_label}.label duplicates an earlier field")
        seen_labels.add(label_key)
        extra = {
            "id": uuid.uuid4().hex,
            "label": field_label,
            "content": _text(
                item["content"], f"{item_label}.content", max_length=2000
            ),
        }
        if "templateKey" in item:
            template_key = _text(
                item["templateKey"],
                f"{item_label}.templateKey",
                max_length=100,
                single_line=True,
            )
            if template_key not in allowed_template_keys:
                raise InputError(
                    f"{item_label}.templateKey is not valid for {lang_code}"
                )
            if template_key in seen_template_keys:
                raise InputError(
                    f"{item_label}.templateKey duplicates an earlier field"
                )
            seen_template_keys.add(template_key)
            extra["templateKey"] = template_key
        result.append(extra)
    return result


def _normalize_word(item, index, lang_code, tags_by_id):
    label = f"words[{index}]"
    allowed_keys = WORD_REQUIRED_KEYS | WORD_OPTIONAL_KEYS
    if (
        not isinstance(item, dict)
        or not WORD_REQUIRED_KEYS.issubset(item)
        or not set(item).issubset(allowed_keys)
    ):
        raise InputError(
            f"{label} must contain word and definition plus only supported "
            "optional fields"
        )
    word = _text(
        item["word"], f"{label}.word", max_length=200, single_line=True
    )
    definition = _text(
        item["definition"], f"{label}.definition", max_length=10000
    )
    phonetic = _text(
        item.get("phonetic", ""),
        f"{label}.phonetic",
        max_length=500,
        allow_empty=True,
        single_line=True,
    )
    tag = None
    if "tag" in item:
        tag_id = _tag_id(item["tag"], f"{label}.tag")
        if tag_id not in tags_by_id:
            raise InputError(f"{label}.tag references undefined tag {tag_id!r}")
        tag = tags_by_id[tag_id]["vo"]
    return {
        "word": word,
        "phonetic": phonetic,
        "definition": definition,
        "examples": _normalize_examples(
            item.get("examples"), f"{label}.examples"
        ),
        "extras": _normalize_extras(
            item.get("extras"), f"{label}.extras", lang_code
        ),
        "tag": tag,
    }


def load_source(path, product="auto"):
    try:
        source = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise InputError(f"cannot read input: {error}") from error
    except (UnicodeError, json.JSONDecodeError) as error:
        raise InputError(f"input must be valid UTF-8 JSON: {error}") from error

    if not isinstance(source, dict) or set(source) - ROOT_KEYS:
        raise InputError("input root has unsupported fields or is not an object")
    if product not in PRODUCT_CHOICES:
        raise InputError(
            "product must be one of " + ", ".join(PRODUCT_CHOICES)
        )
    words_value = source.get("words")
    if not isinstance(words_value, list) or not words_value:
        raise InputError("words must be a non-empty array")
    resolved_product = (
        "card" if product == "auto" and len(words_value) == 1 else product
    )
    if resolved_product == "auto":
        resolved_product = "pack"
    if resolved_product == "card" and len(words_value) != 1:
        raise InputError("standalone card output requires exactly one word")

    if resolved_product == "card":
        unsupported = {"name", "tags"} & set(source)
        if unsupported:
            raise InputError(
                "standalone card input does not support root fields: "
                + ", ".join(sorted(unsupported))
            )
        name = None
    else:
        name = _text(source.get("name"), "name", max_length=500)
    lang_code = _text(
        source.get("langCode"),
        "langCode",
        max_length=10,
        single_line=True,
    ).lower()
    if lang_code not in SUPPORTED_LANG_CODES:
        raise InputError(
            "langCode must be one of " + ", ".join(sorted(SUPPORTED_LANG_CODES))
        )
    if resolved_product == "pack" and "tags" in source:
        tags, tags_by_id = _normalize_tags(source["tags"])
    else:
        tags, tags_by_id = [], {}
    if len(words_value) > MAX_WORDS:
        raise InputError(f"words exceeds the {MAX_WORDS}-entry limit")
    words = []
    seen_words = set()
    for index, item in enumerate(words_value):
        if (
            resolved_product == "card"
            and isinstance(item, dict)
            and "tag" in item
        ):
            raise InputError("standalone cards do not carry pack tags")
        word = _normalize_word(item, index, lang_code, tags_by_id)
        signature = word["word"].casefold()
        if signature in seen_words:
            raise InputError(f"words[{index}].word duplicates an earlier word")
        seen_words.add(signature)
        words.append(word)
    return {
        "name": name,
        "langCode": lang_code,
        "words": words,
        "tags": [tag["vo"] for tag in tags],
        "product": resolved_product,
    }


def _word_document(word, lang_code):
    return {
        "version": WORD_DOCUMENT_VERSION,
        "type": WORD_DOCUMENT_TYPE,
        "word": word["word"],
        "phonetic": word["phonetic"],
        "definition": word["definition"],
        "examples": word["examples"],
        "langCode": lang_code,
        "extras": word["extras"],
    }


def _word_card_vo(word, lang_code):
    document = _word_document(word, lang_code)
    raw_document = json.dumps(
        document, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    card = {
        "uuid": uuid.uuid4().hex,
        "sidea": word["word"],
        "sideb": word["definition"],
        "flag": 0,
        "rtf": base64.b64encode(raw_document).decode("ascii"),
        "sideaAttIds": [],
        "sidebAttIds": [],
        "version": APP_DOCUMENT_VERSION,
    }
    if word["tag"] is not None:
        card["tag"] = word["tag"]
    return card


def build_pack(source):
    cards = [
        _word_card_vo(word, source["langCode"]) for word in source["words"]
    ]

    user_info = json.dumps(
        {
            "wordPackInfo": True,
            "wordPackLanguageCode": source["langCode"],
        },
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    pack = {
        "name": source["name"],
        "cards": cards,
        "version": APP_DOCUMENT_VERSION,
        "userInfo": base64.b64encode(user_info).decode("ascii"),
    }
    if source["tags"]:
        pack["tags"] = source["tags"]
    return pack


def build_card(source):
    return _word_card_vo(source["words"][0], source["langCode"])


def build_artifact(source, product):
    if product == "card":
        return build_card(source)
    return build_pack(source)


def write_wink(content_root, output_path):
    if output_path.suffix.lower() != ".wink":
        raise InputError("output filename must end in .wink")
    if output_path.exists():
        raise FileExistsError(f"output already exists: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(
        content_root, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    try:
        with zipfile.ZipFile(
            output_path,
            mode="x",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        ) as archive:
            archive.writestr("content.json", content)
    except Exception:
        output_path.unlink(missing_ok=True)
        raise


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description=(
            "Build an AI-authored native WordDocument .wink pack or "
            "standalone card."
        )
    )
    parser.add_argument("input", type=Path, help="UTF-8 words JSON")
    parser.add_argument("output", type=Path, help="new .wink output path")
    parser.add_argument(
        "--product",
        choices=PRODUCT_CHOICES,
        default="auto",
        help="artifact root type (default: auto by final word count)",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    output_created = False
    try:
        source = load_source(args.input, args.product)
        write_wink(build_artifact(source, source["product"]), args.output)
        output_created = True
        summary = validate_word_wink(args.output)
    except (
        InputError,
        ValidationError,
        FileExistsError,
        OSError,
        UnicodeError,
        zipfile.BadZipFile,
    ) as error:
        if output_created:
            args.output.unlink(missing_ok=True)
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    if summary["product"] == "card":
        print(
            f"Created {args.output} — standalone word card "
            f"{summary['word']!r}, language {summary['lang_code']}, "
            f"{summary['example_count']} examples, "
            f"{summary['extra_count']} extra fields"
        )
    else:
        print(
            f"Created {args.output} — pack {summary['name']!r}, "
            f"language {summary['lang_code']}, "
            f"{summary['word_count']} AI-authored words, "
            f"{summary['example_count']} examples, "
            f"{summary['extra_count']} extra fields, "
            f"{summary['tag_count']} tags, "
            f"{summary['tagged_card_count']} tagged cards"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
