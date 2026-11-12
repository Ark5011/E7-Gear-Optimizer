# E7 Gear Evaluator

A lightweight Windows desktop tool for deciding whether an Epic Seven gear
piece is worth rolling.

## MVP

- Load a gear screenshot or capture the primary screen.
- Monitor the screen and automatically react to visual changes.
- Run OCR and edit the recognized text before analysis.
- Extract gear level, main stat, and substats.
- Show a transparent score, recommendation, and reasons.

The current evaluator is a general-purpose heuristic, not a replacement for
hero-specific gear optimization. Its weights are kept in `evaluator.py` so they
can be tuned as the project grows.

## Setup

1. Install Python 3.10 or newer.
2. Install the Python dependencies:

   ```text
   python -m pip install -r requirements.txt
   ```

3. Install Tesseract OCR separately and make sure `tesseract.exe` is on PATH.
4. Start the desktop app with `python app.py`.

Use **Start live monitor** while the gear screen is visible in the **Epic
Seven** window. The app samples that window's client area every 500 ms, runs
OCR only after a detected change, and updates the recommendation automatically.
OCR text remains editable so recognition mistakes can be corrected manually.

The monitor captures only the Epic Seven window. It does not inject into the
game or read game memory. Keep the gear panel visible and stop monitoring when
you no longer want screen capture.
