"""Shared validation for ordinary image attachments supported by WinkNotes."""

from pathlib import Path


SUPPORTED_IMAGE_EXTENSIONS = {"heic", "png", "jpeg", "jpg", "webp", "tiff"}
MAX_IMAGE_BYTES = 64 * 1024 * 1024
HEIC_BRANDS = {b"heic", b"heix", b"hevc", b"hevx"}


class ImageFormatError(ValueError):
    """Raised when an image attachment cannot be safely packaged."""


def _detected_image_type(data):
    if (
        len(data) >= 24
        and data.startswith(b"\x89PNG\r\n\x1a\n")
        and data[12:16] == b"IHDR"
    ):
        return "png"
    if len(data) >= 4 and data.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    if len(data) >= 8 and data[:4] in {b"II*\x00", b"MM\x00*"}:
        return "tiff"
    if len(data) >= 16 and data[4:8] == b"ftyp":
        brands = {data[index : index + 4] for index in range(8, min(len(data), 40), 4)}
        if brands & HEIC_BRANDS:
            return "heic"
    return None


def validate_image_bytes(data, expected_extension, label):
    extension = expected_extension.lower()
    if extension not in SUPPORTED_IMAGE_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_IMAGE_EXTENSIONS))
        raise ImageFormatError(f"{label} uses an unsupported extension; use {supported}")
    if not data:
        raise ImageFormatError(f"{label} is empty")
    if len(data) > MAX_IMAGE_BYTES:
        raise ImageFormatError(f"{label} exceeds the 64 MiB limit")

    detected = _detected_image_type(data)
    if detected is None:
        raise ImageFormatError(f"{label} is not a recognized supported image")
    matches = detected == extension or (
        detected == "jpeg" and extension in {"jpg", "jpeg"}
    )
    if not matches:
        raise ImageFormatError(
            f"{label} content is {detected}, not .{expected_extension.lower()}"
        )
    return extension


def validate_image_file(path, label):
    try:
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise ImageFormatError(f"{label} cannot be resolved: {error}") from error
    if not resolved.is_file():
        raise ImageFormatError(f"{label} is not a regular file")
    extension = resolved.suffix.removeprefix(".").lower()
    try:
        data = resolved.read_bytes()
    except OSError as error:
        raise ImageFormatError(f"{label} cannot be read: {error}") from error
    validate_image_bytes(data, extension, label)
    return resolved, extension
