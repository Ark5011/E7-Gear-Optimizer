"""Windows screen capture and lightweight change detection."""

from __future__ import annotations

import hashlib
import ctypes
from ctypes import wintypes

from mss import mss
from PIL import Image


GAME_WINDOW_TITLE = "Epic Seven"


def _game_window_region() -> dict[str, int]:
    if not hasattr(ctypes, "windll"):
        raise RuntimeError("Game-window capture is only supported on Windows.")

    user32 = ctypes.windll.user32
    window_handle = user32.FindWindowW(None, GAME_WINDOW_TITLE)
    if not window_handle:
        raise RuntimeError(f'Could not find a window titled "{GAME_WINDOW_TITLE}".')

    client_rect = wintypes.RECT()
    if not user32.GetClientRect(window_handle, ctypes.byref(client_rect)):
        raise RuntimeError(f'Could not read the "{GAME_WINDOW_TITLE}" window bounds.')

    top_left = wintypes.POINT(client_rect.left, client_rect.top)
    if not user32.ClientToScreen(window_handle, ctypes.byref(top_left)):
        raise RuntimeError(f'Could not locate the "{GAME_WINDOW_TITLE}" window.')

    width = client_rect.right - client_rect.left
    height = client_rect.bottom - client_rect.top
    if width <= 0 or height <= 0:
        raise RuntimeError(f'The "{GAME_WINDOW_TITLE}" window has no visible client area.')

    return {
        "left": top_left.x,
        "top": top_left.y,
        "width": width,
        "height": height,
    }


class ScreenCapture:
    """Capture the Epic Seven client area without saving screenshots to disk."""

    def __init__(self) -> None:
        self._capture = mss()

    def capture(self) -> Image.Image:
        screenshot = self._capture.grab(_game_window_region())
        return Image.frombytes("RGB", screenshot.size, screenshot.rgb)

    def close(self) -> None:
        self._capture.close()


def fingerprint(image: Image.Image) -> str:
    """Create a stable, low-cost fingerprint for meaningful screen changes."""
    sample = image.convert("L")
    sample.thumbnail((160, 100))
    return hashlib.sha256(sample.tobytes()).hexdigest()
