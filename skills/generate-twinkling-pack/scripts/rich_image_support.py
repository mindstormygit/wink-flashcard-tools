"""Build and validate native WinkNotes RichImage (.rimg) occlusion attachments."""

import math
import plistlib
from pathlib import Path

from image_support import ImageFormatError, _detected_image_type, validate_image_file


RICH_IMAGE_EXTENSION = "rimg"
RICH_IMAGE_SCHEMA_VERSION = 2
RICH_IMAGE_CONTENT_VERSION = 1
MAX_MASKS_PER_RICH_IMAGE = 200
MAX_RICH_IMAGE_BYTES = 70 * 1024 * 1024


class RichImageFormatError(ValueError):
    """Raised when native RichImage input or serialized data is invalid."""


def _number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RichImageFormatError(f"{label} must be a number")
    result = float(value)
    if not math.isfinite(result):
        raise RichImageFormatError(f"{label} must be finite")
    return result


def _normalized_rect(value, label):
    if not isinstance(value, dict) or set(value) - {
        "x",
        "y",
        "width",
        "height",
        "color",
    }:
        raise RichImageFormatError(
            f"{label} must contain x, y, width, and height, plus optional color"
        )
    required = {"x", "y", "width", "height"}
    if not required.issubset(value):
        raise RichImageFormatError(
            f"{label} must contain x, y, width, and height"
        )

    x = _number(value["x"], f"{label}.x")
    y = _number(value["y"], f"{label}.y")
    width = _number(value["width"], f"{label}.width")
    height = _number(value["height"], f"{label}.height")
    epsilon = 1e-9
    if x < 0 or y < 0 or width <= 0 or height <= 0:
        raise RichImageFormatError(
            f"{label} must use non-negative x/y and positive width/height"
        )
    if x + width > 1 + epsilon or y + height > 1 + epsilon:
        raise RichImageFormatError(
            f"{label} must fit inside normalized image coordinates 0...1"
        )

    result = {
        "x": min(1.0, x),
        "y": min(1.0, y),
        "width": min(1.0 - x, width),
        "height": min(1.0 - y, height),
    }
    if "color" in value:
        color = value["color"]
        if (
            not isinstance(color, str)
            or len(color) != 7
            or not color.startswith("#")
            or any(character not in "0123456789abcdefABCDEF" for character in color[1:])
        ):
            raise RichImageFormatError(f"{label}.color must use #RRGGBB")
        result["color"] = color.upper()
    return result


def normalize_masks(value, label):
    if not isinstance(value, list) or not value:
        raise RichImageFormatError(f"{label} must be a non-empty array")
    if len(value) > MAX_MASKS_PER_RICH_IMAGE:
        raise RichImageFormatError(
            f"{label} exceeds the {MAX_MASKS_PER_RICH_IMAGE}-mask limit"
        )
    return [
        _normalized_rect(mask, f"{label}[{index}]")
        for index, mask in enumerate(value)
    ]


def build_rich_image(image_path, masks, attachment_id, label):
    resolved_path, _ = validate_image_file(Path(image_path), f"{label}.image")
    normalized_masks = normalize_masks(masks, f"{label}.masks")
    image_data = resolved_path.read_bytes()

    encoded_masks = []
    for mask in normalized_masks:
        item = {
            "layoutInfo": [
                [mask["x"], mask["y"]],
                [mask["width"], mask["height"]],
            ]
        }
        if "color" in mask:
            item["co"] = mask["color"]
        encoded_masks.append(item)

    payload = {
        "sv": RICH_IMAGE_SCHEMA_VERSION,
        "cv": RICH_IMAGE_CONTENT_VERSION,
        "oi": image_data,
        "m": encoded_masks,
        "u": attachment_id,
    }
    data = plistlib.dumps(payload, fmt=plistlib.FMT_BINARY, sort_keys=True)
    if len(data) > MAX_RICH_IMAGE_BYTES:
        raise RichImageFormatError(f"{label} exceeds the 70 MiB RichImage limit")
    return data, normalized_masks, resolved_path


def _decoded_rect(value, label):
    if (
        not isinstance(value, list)
        or len(value) != 2
        or not all(isinstance(component, list) and len(component) == 2 for component in value)
    ):
        raise RichImageFormatError(f"{label} is not a CGRect property-list value")
    origin, size = value
    return _normalized_rect(
        {
            "x": origin[0],
            "y": origin[1],
            "width": size[0],
            "height": size[1],
        },
        label,
    )


def validate_rich_image_bytes(data, expected_attachment_id, label):
    if not isinstance(data, bytes) or not data.startswith(b"bplist00"):
        raise RichImageFormatError(f"{label} must be an Apple binary property list")
    if len(data) > MAX_RICH_IMAGE_BYTES:
        raise RichImageFormatError(f"{label} exceeds the 70 MiB RichImage limit")
    try:
        payload = plistlib.loads(data)
    except plistlib.InvalidFileException as error:
        raise RichImageFormatError(f"{label} is not a valid property list") from error

    if not isinstance(payload, dict):
        raise RichImageFormatError(f"{label} root must be a dictionary")
    required = {"sv", "cv", "oi", "m", "u"}
    if set(payload) != required:
        raise RichImageFormatError(
            f"{label} must contain exactly {', '.join(sorted(required))}"
        )
    if payload["sv"] != RICH_IMAGE_SCHEMA_VERSION:
        raise RichImageFormatError(f"{label}.sv is unsupported")
    if payload["cv"] != RICH_IMAGE_CONTENT_VERSION:
        raise RichImageFormatError(f"{label}.cv is unsupported")
    if payload["u"] != expected_attachment_id:
        raise RichImageFormatError(f"{label}.u does not match its media filename")

    original = payload["oi"]
    if not isinstance(original, bytes) or _detected_image_type(original) is None:
        raise ImageFormatError(f"{label}.oi is not a recognized supported image")

    masks = payload["m"]
    if not isinstance(masks, list) or not masks:
        raise RichImageFormatError(f"{label}.m must be a non-empty array")
    if len(masks) > MAX_MASKS_PER_RICH_IMAGE:
        raise RichImageFormatError(
            f"{label}.m exceeds the {MAX_MASKS_PER_RICH_IMAGE}-mask limit"
        )
    for index, mask in enumerate(masks):
        mask_label = f"{label}.m[{index}]"
        if (
            not isinstance(mask, dict)
            or "layoutInfo" not in mask
            or set(mask) - {"layoutInfo", "co"}
        ):
            raise RichImageFormatError(
                f"{mask_label} must contain layoutInfo and optional co"
            )
        _decoded_rect(mask["layoutInfo"], f"{mask_label}.layoutInfo")
        if "co" in mask:
            _normalized_rect(
                {
                    "x": 0,
                    "y": 0,
                    "width": 1,
                    "height": 1,
                    "color": mask["co"],
                },
                mask_label,
            )
    return {
        "mask_count": len(masks),
        "embedded_image_type": _detected_image_type(original),
    }
