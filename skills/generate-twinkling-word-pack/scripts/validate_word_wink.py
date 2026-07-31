#!/usr/bin/env python3
"""Strictly validate native WordDocument .wink packs or cards."""

import argparse
import base64
import binascii
import json
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath


APP_DOCUMENT_VERSION = 6
WORD_DOCUMENT_VERSION = 100
WORD_DOCUMENT_TYPE = 3
SUPPORTED_LANG_CODES = {"en", "ja", "ko", "de", "fr", "es", "pt", "it"}
PACK_REQUIRED_KEYS = {"name", "cards", "version", "userInfo"}
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
WORD_DOCUMENT_KEYS = {
    "version",
    "type",
    "word",
    "phonetic",
    "definition",
    "examples",
    "langCode",
    "extras",
}
EXAMPLE_KEYS = {"id", "sentence", "translation"}
EXTRA_REQUIRED_KEYS = {"id", "label", "content"}
EXTRA_OPTIONAL_KEYS = {"templateKey"}
TAG_KEYS = {"name", "lighthex"}
UUID_PATTERN = re.compile(r"^[0-9a-f]{32}$")
HEX_COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")
TAG_PATH_SEPARATOR = "/$-#-$/"
MAX_CONTENT_JSON_BYTES = 64 * 1024 * 1024
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


class ValidationError(ValueError):
    """Raised when a .wink vocabulary pack is invalid."""


def _require(condition, message):
    if not condition:
        raise ValidationError(message)


def _validate_text(
    value, label, *, max_length, allow_empty=False, single_line=False
):
    _require(isinstance(value, str), f"{label} must be a string")
    _require(value == value.strip(), f"{label} must be trimmed")
    if not allow_empty:
        _require(bool(value), f"{label} must not be empty")
    _require(
        len(value) <= max_length,
        f"{label} exceeds the {max_length}-character limit",
    )
    _require(
        "\x00" not in value and "\uFFFC" not in value,
        f"{label} contains a reserved character",
    )
    if single_line:
        _require(
            "\n" not in value and "\r" not in value,
            f"{label} must be a single line",
        )
    return value


def _validate_tag(value, label):
    _require(isinstance(value, dict) and set(value) == TAG_KEYS, f"{label} invalid")
    path = _validate_text(
        value["name"], f"{label}.name", max_length=10000, single_line=True
    )
    components = path.split(TAG_PATH_SEPARATOR)
    _require(
        len(components) <= MAX_TAG_DEPTH,
        f"{label}.name exceeds the {MAX_TAG_DEPTH}-level limit",
    )
    for index, component in enumerate(components):
        _require(component, f"{label}.name component {index} is empty")
        _require(
            len(component) <= MAX_TAG_NAME_LENGTH,
            f"{label}.name component {index} is too long",
        )
    _require(
        isinstance(value["lighthex"], str)
        and HEX_COLOR_PATTERN.fullmatch(value["lighthex"]),
        f"{label}.lighthex must use #RRGGBB",
    )
    return path, components


def _validate_tags(value):
    _require(isinstance(value, list) and value, "tags must be a non-empty array")
    _require(len(value) <= MAX_TAGS, f"tags exceeds the {MAX_TAGS}-tag limit")
    definitions = {}
    components_by_path = {}
    for index, tag in enumerate(value):
        path, components = _validate_tag(tag, f"tags[{index}]")
        _require(path not in definitions, f"tags[{index}].name is duplicated")
        definitions[path] = tag
        components_by_path[path] = components
    for path, components in components_by_path.items():
        if len(components) > 1:
            parent = TAG_PATH_SEPARATOR.join(components[:-1])
            _require(
                parent in definitions,
                f"tag {path!r} is missing parent definition {parent!r}",
            )
    return definitions


def _decode_base64_json(value, label):
    _require(isinstance(value, str) and value, f"{label} must be Base64")
    try:
        raw = base64.b64decode(value, validate=True)
        return json.loads(raw.decode("utf-8"))
    except (binascii.Error, UnicodeError, json.JSONDecodeError) as error:
        raise ValidationError(f"{label} is not valid Base64 JSON") from error


def _validate_user_info(value):
    info = _decode_base64_json(value, "userInfo")
    _require(
        isinstance(info, dict)
        and set(info) == {"wordPackInfo", "wordPackLanguageCode"},
        "userInfo has invalid fields",
    )
    _require(info["wordPackInfo"] is True, "userInfo.wordPackInfo must be true")
    lang_code = info["wordPackLanguageCode"]
    _require(
        isinstance(lang_code, str) and lang_code in SUPPORTED_LANG_CODES,
        "userInfo.wordPackLanguageCode is unsupported",
    )
    return lang_code


def _validate_examples(value, label, seen_ids):
    _require(isinstance(value, list), f"{label} must be an array")
    _require(
        len(value) <= MAX_EXAMPLES,
        f"{label} exceeds the {MAX_EXAMPLES}-example limit",
    )
    seen_content = set()
    for index, item in enumerate(value):
        item_label = f"{label}[{index}]"
        _require(
            isinstance(item, dict) and set(item) == EXAMPLE_KEYS,
            f"{item_label} has invalid fields",
        )
        item_id = item["id"]
        _require(
            isinstance(item_id, str) and UUID_PATTERN.fullmatch(item_id),
            f"{item_label}.id is invalid",
        )
        _require(item_id not in seen_ids, f"{item_label}.id is duplicated")
        seen_ids.add(item_id)
        sentence = _validate_text(
            item["sentence"], f"{item_label}.sentence", max_length=2000
        )
        translation = _validate_text(
            item["translation"],
            f"{item_label}.translation",
            max_length=2000,
            allow_empty=True,
        )
        signature = (sentence.casefold(), translation.casefold())
        _require(
            signature not in seen_content,
            f"{item_label} duplicates an earlier example",
        )
        seen_content.add(signature)
    return len(value)


def _validate_extras(value, label, lang_code, seen_ids):
    _require(isinstance(value, list), f"{label} must be an array")
    _require(
        len(value) <= MAX_EXTRAS,
        f"{label} exceeds the {MAX_EXTRAS}-field limit",
    )
    seen_labels = set()
    seen_template_keys = set()
    for index, item in enumerate(value):
        item_label = f"{label}[{index}]"
        _require(
            isinstance(item, dict)
            and EXTRA_REQUIRED_KEYS.issubset(item)
            and set(item).issubset(
                EXTRA_REQUIRED_KEYS | EXTRA_OPTIONAL_KEYS
            ),
            f"{item_label} has invalid fields",
        )
        item_id = item["id"]
        _require(
            isinstance(item_id, str) and UUID_PATTERN.fullmatch(item_id),
            f"{item_label}.id is invalid",
        )
        _require(item_id not in seen_ids, f"{item_label}.id is duplicated")
        seen_ids.add(item_id)
        field_label = _validate_text(
            item["label"],
            f"{item_label}.label",
            max_length=100,
            single_line=True,
        )
        label_key = field_label.casefold()
        _require(
            label_key not in seen_labels,
            f"{item_label}.label duplicates an earlier field",
        )
        seen_labels.add(label_key)
        _validate_text(
            item["content"], f"{item_label}.content", max_length=2000
        )
        if "templateKey" in item:
            template_key = _validate_text(
                item["templateKey"],
                f"{item_label}.templateKey",
                max_length=100,
                single_line=True,
            )
            _require(
                template_key in TEMPLATE_KEYS_BY_LANGUAGE[lang_code],
                f"{item_label}.templateKey is invalid for {lang_code}",
            )
            _require(
                template_key not in seen_template_keys,
                f"{item_label}.templateKey is duplicated",
            )
            seen_template_keys.add(template_key)
    return len(value)


def _validate_document(card, index, lang_code):
    document = _decode_base64_json(card["rtf"], f"cards[{index}].rtf")
    label = f"cards[{index}].rtf"
    _require(
        isinstance(document, dict) and set(document) == WORD_DOCUMENT_KEYS,
        f"{label} has invalid WordDocument fields",
    )
    _require(
        document["version"] == WORD_DOCUMENT_VERSION,
        f"{label}.version is unsupported",
    )
    _require(document["type"] == WORD_DOCUMENT_TYPE, f"{label}.type must be 3")
    _require(document["langCode"] == lang_code, f"{label}.langCode mismatches pack")
    word = _validate_text(
        document["word"], f"{label}.word", max_length=200, single_line=True
    )
    phonetic = _validate_text(
        document["phonetic"],
        f"{label}.phonetic",
        max_length=500,
        allow_empty=True,
        single_line=True,
    )
    definition = _validate_text(
        document["definition"], f"{label}.definition", max_length=10000
    )
    _require(card["sidea"] == word, f"{label}.word does not match sidea")
    _require(
        card["sideb"] == definition,
        f"{label}.definition does not match sideb",
    )
    seen_ids = set()
    example_count = _validate_examples(
        document["examples"], f"{label}.examples", seen_ids
    )
    extra_count = _validate_extras(
        document["extras"], f"{label}.extras", lang_code, seen_ids
    )
    return {
        "word": word,
        "phonetic": phonetic,
        "example_count": example_count,
        "extra_count": extra_count,
    }


def _validate_pack_content(content):
    _require(isinstance(content, dict), "content.json root must be an object")
    _require(
        PACK_REQUIRED_KEYS.issubset(content)
        and set(content).issubset(PACK_REQUIRED_KEYS | PACK_OPTIONAL_KEYS),
        "content.json has missing or unexpected fields",
    )
    name = _validate_text(content["name"], "name", max_length=500)
    _require(
        content["version"] == APP_DOCUMENT_VERSION,
        "unsupported CardPackVO version",
    )
    lang_code = _validate_user_info(content["userInfo"])
    tag_definitions = (
        _validate_tags(content["tags"]) if "tags" in content else {}
    )
    cards = content["cards"]
    _require(isinstance(cards, list) and cards, "cards must be a non-empty array")
    _require(len(cards) <= MAX_WORDS, f"cards exceeds the {MAX_WORDS}-card limit")

    seen_card_ids = set()
    seen_words = set()
    example_count = 0
    extra_count = 0
    tagged_card_count = 0
    for index, card in enumerate(cards):
        label = f"cards[{index}]"
        _require(
            isinstance(card, dict)
            and CARD_REQUIRED_KEYS.issubset(card)
            and set(card).issubset(CARD_REQUIRED_KEYS | CARD_OPTIONAL_KEYS),
            f"{label} has invalid fields",
        )
        card_id = card["uuid"]
        _require(
            isinstance(card_id, str) and UUID_PATTERN.fullmatch(card_id),
            f"{label}.uuid is invalid",
        )
        _require(card_id not in seen_card_ids, f"{label}.uuid is duplicated")
        seen_card_ids.add(card_id)
        _require(
            type(card["flag"]) is int and card["flag"] == 0,
            f"{label}.flag must be integer 0",
        )
        _require(card["sideaAttIds"] == [], f"{label}.sideaAttIds must be empty")
        _require(card["sidebAttIds"] == [], f"{label}.sidebAttIds must be empty")
        _require(
            card["version"] == APP_DOCUMENT_VERSION,
            f"{label}.version is unsupported",
        )
        if "tag" in card:
            path, _ = _validate_tag(card["tag"], f"{label}.tag")
            _require(path in tag_definitions, f"{label}.tag is not defined")
            _require(
                card["tag"] == tag_definitions[path],
                f"{label}.tag does not match its pack definition",
            )
            tagged_card_count += 1
        document = _validate_document(card, index, lang_code)
        word_key = document["word"].casefold()
        _require(word_key not in seen_words, f"{label} duplicates an earlier word")
        seen_words.add(word_key)
        example_count += document["example_count"]
        extra_count += document["extra_count"]
    return {
        "name": name,
        "lang_code": lang_code,
        "word_count": len(cards),
        "example_count": example_count,
        "extra_count": extra_count,
        "tag_count": len(tag_definitions),
        "tagged_card_count": tagged_card_count,
    }


def _validate_content(content):
    _require(isinstance(content, dict), "content.json root must be an object")
    if CARD_REQUIRED_KEYS.issubset(content):
        _require(
            set(content) == CARD_REQUIRED_KEYS,
            "standalone word card has missing or unexpected fields",
        )
        document = _decode_base64_json(content["rtf"], "rtf")
        _require(
            isinstance(document, dict),
            "rtf must contain a WordDocument object",
        )
        lang_code = document.get("langCode")
        _require(
            isinstance(lang_code, str) and lang_code in SUPPORTED_LANG_CODES,
            "rtf.langCode is unsupported",
        )
        user_info = json.dumps(
            {
                "wordPackInfo": True,
                "wordPackLanguageCode": lang_code,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        summary = _validate_pack_content(
            {
                "name": "Standalone word card",
                "cards": [content],
                "version": APP_DOCUMENT_VERSION,
                "userInfo": base64.b64encode(user_info).decode("ascii"),
            }
        )
        summary["name"] = None
        summary["product"] = "card"
        summary["word"] = content["sidea"]
        return summary

    summary = _validate_pack_content(content)
    summary["product"] = "pack"
    return summary


def validate_word_wink(path):
    _require(path.suffix.lower() == ".wink", "filename must end in .wink")
    _require(path.is_file(), f"file not found: {path}")
    _require(zipfile.is_zipfile(path), "file is not a ZIP archive")
    with zipfile.ZipFile(path, mode="r") as archive:
        infos = archive.infolist()
        _require(infos, "archive is empty")
        _require(
            infos[0].filename == "content.json",
            "content.json must be the first archive entry",
        )
        _require(
            len(infos) == 1 and infos[0].filename == "content.json",
            "word artifacts must contain only content.json",
        )
        info = infos[0]
        path_in_archive = PurePosixPath(info.filename)
        _require(not path_in_archive.is_absolute(), "archive path is absolute")
        _require(".." not in path_in_archive.parts, "archive path escapes root")
        _require(not (info.flag_bits & 0x1), "archive must not be encrypted")
        _require(
            info.file_size <= MAX_CONTENT_JSON_BYTES,
            "content.json exceeds the size limit",
        )
        try:
            content = json.loads(archive.read(info).decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as error:
            raise ValidationError("content.json is not valid UTF-8 JSON") from error
    return _validate_content(content)


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description=(
            "Validate a native WordDocument WinkNotes .wink pack or "
            "standalone card."
        )
    )
    parser.add_argument("wink", type=Path, help=".wink file to validate")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        summary = validate_word_wink(args.wink)
    except (ValidationError, OSError, zipfile.BadZipFile) as error:
        print(f"INVALID: {error}", file=sys.stderr)
        return 1
    if summary["product"] == "card":
        print(
            f"VALID: standalone word card {summary['word']!r}, "
            f"language {summary['lang_code']}, "
            f"{summary['example_count']} examples, "
            f"{summary['extra_count']} extra fields"
        )
    else:
        print(
            f"VALID: pack {summary['name']!r}, language {summary['lang_code']}, "
            f"{summary['word_count']} AI-authored words, "
            f"{summary['example_count']} examples, "
            f"{summary['extra_count']} extra fields, "
            f"{summary['tag_count']} tags, "
            f"{summary['tagged_card_count']} tagged cards"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
