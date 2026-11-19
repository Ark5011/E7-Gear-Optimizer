"""OCR and screenshot helpers."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageGrab, ImageOps
import pytesseract


def recognize_image(path: str | Path) -> str:
    """Recognize text from an image file and surface OCR errors to the caller."""
    return _recognize(Image.open(path))


def recognize_screen() -> str:
    """Capture the full primary screen and recognize its text."""
    return _recognize(ImageGrab.grab())


def recognize_image_bytes(data: bytes) -> str:
    """Recognize text from uploaded image data."""
    return _recognize(Image.open(BytesIO(data)))


def _recognize(image: Image.Image) -> str:
    prepared = ImageOps.grayscale(image)
    prepared = prepared.point(lambda pixel: 255 if pixel > 150 else 0)
    return pytesseract.image_to_string(prepared, config="--psm 6").strip()
