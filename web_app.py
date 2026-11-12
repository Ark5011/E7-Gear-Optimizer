"""Flask web UI for the Epic Seven gear evaluator."""

from __future__ import annotations

from flask import Flask, render_template, request

from evaluator import Evaluation, evaluate_gear, parse_gear
from ocr import recognize_image_bytes


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024


def _evaluate(text: str) -> Evaluation | None:
    if not text.strip():
        return None
    return evaluate_gear(parse_gear(text))


@app.route("/", methods=["GET", "POST"])
def index():
    ocr_text = ""
    evaluation = None
    error = None

    if request.method == "POST":
        ocr_text = request.form.get("ocr_text", "")
        upload = request.files.get("screenshot")
        action = request.form.get("action")

        if action == "ocr":
            if upload is None or not upload.filename:
                error = "Choose a screenshot before running OCR."
            else:
                try:
                    ocr_text = recognize_image_bytes(upload.read())
                except Exception as exc:
                    error = f"OCR failed: {exc}"
        elif action == "analyze":
            evaluation = _evaluate(ocr_text)
            if evaluation is None:
                error = "Enter or recognize gear text before analyzing."

    return render_template(
        "index.html",
        ocr_text=ocr_text,
        evaluation=evaluation,
        error=error,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
