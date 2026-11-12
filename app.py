"""Desktop UI for the Epic Seven gear evaluator."""

from __future__ import annotations

from pathlib import Path
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Callable

from evaluator import evaluate_gear, parse_gear
from ocr import recognize_image, recognize_image_bytes
from screen_monitor import ScreenCapture, fingerprint


class GearEvaluatorApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("E7 Gear Evaluator")
        self.geometry("760x620")
        self.minsize(620, 500)
        self._screen_capture = ScreenCapture()
        self._monitoring = False
        self._ocr_in_progress = False
        self._last_fingerprint: str | None = None
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._close)

    def _build_ui(self) -> None:
        toolbar = ttk.Frame(self, padding=12)
        toolbar.pack(fill="x")
        ttk.Button(toolbar, text="Load screenshot", command=self._load_image).pack(side="left")
        ttk.Button(toolbar, text="Capture screen", command=self._capture_screen).pack(
            side="left", padx=(8, 0)
        )
        self.monitor_button = ttk.Button(
            toolbar, text="Start live monitor", command=self._toggle_monitor
        )
        self.monitor_button.pack(side="left", padx=(8, 0))
        ttk.Button(toolbar, text="Analyze gear", command=self._analyze).pack(side="right")

        ttk.Label(self, text="OCR text (edit mistakes before analyzing):").pack(
            anchor="w", padx=12
        )
        self.ocr_text = tk.Text(self, height=14, wrap="word")
        self.ocr_text.pack(fill="both", expand=True, padx=12, pady=(4, 12))

        result = ttk.LabelFrame(self, text="Evaluation", padding=12)
        result.pack(fill="both", padx=12, pady=(0, 12))
        self.result_label = ttk.Label(result, text="Load or capture a gear screenshot.")
        self.result_label.pack(anchor="w")
        self.reasons_label = ttk.Label(result, text="", justify="left")
        self.reasons_label.pack(anchor="w", pady=(8, 0))
        self.monitor_status = ttk.Label(result, text="Live monitor is off.")
        self.monitor_status.pack(anchor="w", pady=(12, 0))

    def _load_image(self) -> None:
        path = filedialog.askopenfilename(
            title="Select gear screenshot",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp"), ("All files", "*.*")],
        )
        if path:
            self._run_ocr(lambda: recognize_image(Path(path)))

    def _capture_screen(self) -> None:
        self._run_ocr(
            lambda: recognize_image_bytes(_image_bytes(self._screen_capture.capture()))
        )

    def _toggle_monitor(self) -> None:
        self._monitoring = not self._monitoring
        self.monitor_button.configure(
            text="Stop live monitor" if self._monitoring else "Start live monitor"
        )
        self.monitor_status.configure(
            text="Watching the primary screen for changes..."
            if self._monitoring
            else "Live monitor is off."
        )
        if self._monitoring:
            self._last_fingerprint = None
            self.after(500, self._monitor_tick)

    def _monitor_tick(self) -> None:
        if not self._monitoring:
            return
        try:
            image = self._screen_capture.capture()
            current_fingerprint = fingerprint(image)
            changed = current_fingerprint != self._last_fingerprint
            self._last_fingerprint = current_fingerprint
            if changed and not self._ocr_in_progress:
                self._ocr_in_progress = True
                self.monitor_status.configure(text="Screen changed; reading gear...")
                threading.Thread(
                    target=self._recognize_captured_image,
                    args=(image,),
                    daemon=True,
                ).start()
        except Exception as error:
            self._monitoring = False
            self.monitor_button.configure(text="Start live monitor")
            self.monitor_status.configure(text=f"Monitor stopped: {error}")
        finally:
            if self._monitoring:
                self.after(500, self._monitor_tick)

    def _recognize_captured_image(self, image) -> None:
        try:
            text = recognize_image_bytes(_image_bytes(image))
        except Exception as error:
            self.after(0, lambda error=error: self._finish_monitor_error(error))
        else:
            self.after(0, lambda: self._finish_monitor_ocr(text))

    def _finish_monitor_ocr(self, text: str) -> None:
        self._ocr_in_progress = False
        self.ocr_text.delete("1.0", "end")
        self.ocr_text.insert("1.0", text)
        self._analyze()
        self.monitor_status.configure(text="Watching the primary screen for changes...")

    def _finish_monitor_error(self, error: Exception) -> None:
        self._ocr_in_progress = False
        self.monitor_status.configure(text=f"OCR failed: {error}")

    def _run_ocr(self, operation: Callable[[], str]) -> None:
        try:
            text = operation()
        except Exception as error:
            messagebox.showerror(
                "OCR failed",
                f"{error}\n\nInstall Tesseract OCR and ensure it is available on PATH.",
            )
            return
        self.ocr_text.delete("1.0", "end")
        self.ocr_text.insert("1.0", text)

    def _analyze(self) -> None:
        gear = parse_gear(self.ocr_text.get("1.0", "end"))
        evaluation = evaluate_gear(gear)
        self.result_label.configure(
            text=f"{evaluation.recommendation}  |  Score: {evaluation.score}/100"
        )
        self.reasons_label.configure(
            text="\n".join(f"- {reason}" for reason in evaluation.reasons)
        )

    def _close(self) -> None:
        self._monitoring = False
        self._screen_capture.close()
        self.destroy()


def _image_bytes(image) -> bytes:
    from io import BytesIO

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


if __name__ == "__main__":
    GearEvaluatorApp().mainloop()
