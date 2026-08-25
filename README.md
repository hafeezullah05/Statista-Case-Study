# Statista Chat-to-Slides Generator

## Setup

### 1. Python environment
This project was built and tested using a conda environment (Python 3.11), but any virtual
environment manager works the same way — venv, conda, or similar.

Using conda:
```bash
conda create -n statista-slides python=3.11
conda activate statista-slides
pip install -r requirements.txt
```

Or using venv:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Then launch the notebook:
```bash
jupyter notebook main.ipynb
```

### 2. LibreOffice (required for PDF export)
python-pptx can only write `.pptx` files — it has no built-in PDF export. PDF generation works by
converting the finished `.pptx` through LibreOffice's headless command-line mode.

Install LibreOffice via Homebrew:
```bash
brew install --cask libreoffice
```

Verify the install:
```bash
/Applications/LibreOffice.app/Contents/MacOS/soffice --version
```

Manual conversion test (confirms the mechanism works before it's wired into Python):
```bash
/Applications/LibreOffice.app/Contents/MacOS/soffice --headless --convert-to pdf --outdir output output/deck.pptx
```
This should produce `output/deck.pdf`.

## What it does
Takes a structured JSON file (the output of a Statista AI chat query — see
`Task Requirment/gen_z_purchase_behavior_analysis.json` for the example used) and generates a
PowerPoint presentation summarizing it: a title slide, one chart slide per insight category
(bar chart + one-line insight + source citation), and a closing summary slide (key takeaways
as bullets, plus a caveat note about data quality where relevant). The finished `.pptx` is then
optionally converted to `.pdf` via LibreOffice.

## How to run it
1. Set up the Python environment (see Setup above) and install dependencies.
2. Make sure LibreOffice is installed if you want the PDF output (see Setup above).
3. Open `main.ipynb` in Jupyter and run all cells top to bottom. It will:
   - Load `Task Requirment/gen_z_purchase_behavior_analysis.json`
   - Build the deck via the `DeckBuilder` class in `slides_code/builder.py`
   - Save it to `output/deck.pptx`
   - Convert it to `output/deck.pdf`

## Libraries used and why
- **python-pptx** — the core library for building `.pptx` files: slides, textboxes, native
  editable charts. Chosen because it's the standard, actively maintained Python library for
  generating PowerPoint files, and it produces real editable charts rather than static images.
- **LibreOffice (external application, not a pip package)** — used in headless mode via
  `subprocess` to convert the finished `.pptx` to `.pdf`. python-pptx has no PDF export of its
  own; LibreOffice's headless CLI is the standard free way to do Office-format-to-PDF conversion
  without needing a Microsoft Office license.
- **json, subprocess, textwrap** (Python standard library) — parsing the input JSON, shelling
  out to LibreOffice, and (earlier, since removed) trimming label text.
- **Jupyter / ipykernel** — for `main.ipynb` itself, so the pipeline can be run and inspected
  interactively rather than only as a black-box script.

## Known limitations / what I'd improve with more time
- **PDF export is macOS-only as written.** The LibreOffice conversion step in `main.ipynb` shells
  out via `subprocess` to a hardcoded path: `/Applications/LibreOffice.app/Contents/MacOS/soffice`.
  This only exists on macOS — running the notebook on Windows or Linux would fail at that step
  even with LibreOffice installed, since the binary lives at a different path on those platforms.
  With more time, I'd detect the OS (`platform.system()`) and pick the correct default `soffice`
  path per platform, and add a clearer error message (checking the path exists before calling it)
  instead of letting the `subprocess` call fail with a raw/unclear error.
- **PDF export requires LibreOffice as a separate application install**, not a pip package.
  python-pptx has no built-in PDF export, so this is an unavoidable external dependency for
  anyone who wants to regenerate the PDF — documented in Setup above, but worth restating as a
  real constraint on portability.
- **Chart data handled defensively, but not the rest of the JSON.** `add_chart_slide` guards
  against `metrics` being missing, empty, or containing non-dict items — falling back to a
  "No chart data available" placeholder rather than crashing. Other top-level fields aren't
  guarded the same way: a missing `title`, an empty `key_insights` list, or an empty
  `summary_text` would either render oddly (e.g. a summary slide with a title and no bullets)
  or raise an unhandled exception, rather than failing gracefully. I prioritized the most likely
  failure point (chart data) given the time available, rather than defending every possible
  malformed shape.
- **Chart color palette is fixed at 10 colors and wraps around.** The Brand Preferences slide
  has exactly 10 bars — right at the edge of the palette. A category with more than 10 data
  points would start repeating colors rather than erroring, which could look like two unrelated
  bars are meant to be grouped when they aren't.
- **No automated tests.** Verification so far has been manual — running the pipeline against the
  real JSON and a few hand-constructed malformed inputs, then visually checking the output.
  With more time I'd add a few `pytest` cases covering the edge cases above.
