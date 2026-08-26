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

Then run it from the command line:
```bash
python main.py
```
It will prompt you interactively for an optional presentation request (press Enter for the
default). A notebook version with identical logic is also available if you'd rather run/inspect
it interactively cell by cell:
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
/Applications/LibreOffice.app/Contents/MacOS/soffice --headless --convert-to pdf --outdir example_output example_output/statista_ppt.pptx
```
This should produce `example_output/statista_ppt.pdf` (renamed to `statista_pdf.pdf` by the
actual pipeline — see "Known limitations" for why the rename step exists).

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
3. From the project root, run:
   ```bash
   python main.py
   ```
   It will:
   - Load `Task Requirment/gen_z_purchase_behavior_analysis.json`
   - Ask for an optional free-text presentation request (e.g. `"Turn this into a 5-slide
     presentation"`) — press Enter to use the default
   - Build the deck via the `DeckBuilder` class in `slides_code/builder.py`
   - Save it to `example_output/statista_ppt.pptx`
   - Convert it to `example_output/statista_pdf.pdf`

   Example session:
   ```
   $ python main.py
   Enter your presentation request (e.g. "Turn this into a 5-slide presentation"). Only slide
   count is currently understood — press Enter for the default:
   {'slide_count': 5}
   OK  example_output/statista_ppt.pptx  (52.2 KB)
   OK  example_output/statista_pdf.pdf  (56.6 KB)
   ```

`main.ipynb` runs the identical pipeline for interactive/exploratory use (`jupyter notebook
main.ipynb`, run all cells) — both entry points import the same `slides_code` modules, so no
logic is duplicated between the script and the notebook.

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

- **User-preference parsing only handles slide count, not tone or focus area.** The brief names
  tone, branding, and focus areas as possible preferences alongside slide count; I scoped this
  down to slide count only, given time constraints. It's implemented as a small, deliberately
  simple regex parser (`slides_code/prompt.py`) rather than an LLM/NLP approach — extracting a
  number from a sentence doesn't need that complexity, and keeping parsing separate from
  rendering (`DeckBuilder` never sees the raw prompt) kept the two concerns decoupled.

  Honestly, this needs more time than I had left to do well — my estimate is roughly
  2.5-3.5 hours for a version with the same quality bar as the slide-count feature (tested,
  documented, edge cases considered), broken down as: keyword-matching focus areas against
  category names (~45-60 min, plus deciding whether a match should filter or just reorder
  `key_insights`), tone keywords adjusting summary bullet count (~45-60 min, touching
  `add_summary_slide`'s logic), working out how slide count/focus/tone should interact when
  more than one is present in the same prompt (~30-45 min — the fiddliest part), and testing
  plus doc updates (~30-45 min). Mostly localized to `prompt.py` and the build loop in
  `main.py`/`main.ipynb`; `DeckBuilder` itself likely wouldn't need to change.

- **Requesting more slides than there's data for doesn't crash, but does under-deliver by
  design.** If a prompt asks for more slides than there are insight categories (e.g. "10-slide"
  with only 3 categories available), the tool prints a note explaining the shortfall and
  generates as many slides as the data actually supports, rather than fabricating content or
  erroring out.
- **The slide-count parser fails silently on input outside its exact expected pattern.**
  `parse_prompt` only matches a number immediately followed by the word "slide" (e.g.
  "4-slide", "4 slides") via `r'(\d+)[- ]slide'`. Typing a bare number alone (e.g. just "4",
  with no "slide" after it) doesn't match, so `slide_count` silently stays `None` and the
  default full deck is generated — with no indication to the user that their input wasn't
  understood. Found this from an actual test run: entered "4", got the default 5-slide deck
  with no explanation. With more time, I'd fix this two ways: (1) accept a bare number as a
  fallback (e.g. `if user_prompt.strip().isdigit(): slide_count = int(...)`) so a plain "4"
  works too, and (2) when the regex finds no match on non-empty input, print a message like
  "Couldn't find a slide count in your request — using the default" instead of silently
  falling back, so the user always knows what actually happened rather than being surprised by
  the output.
- **LibreOffice's `--convert-to pdf` ignores any output filename you'd want — it always names
  the PDF after the input file's basename** (there's no CLI flag to set an arbitrary output
  name, only an output *directory*). Found this by actually testing: the first version of the
  PDF export silently produced a wrongly-named file, masked by a stale leftover file with the
  intended name from an earlier manual run. Fixed by explicitly renaming the file LibreOffice
  produces to the intended name (`os.replace(...)`) right after conversion.
- **Summary content is static/selected, not genuinely summarized or contextualized to the
  user.** When the deck is a smaller subset, the summary slide picks between two pre-written
  texts — the full JSON narrative, or a naive concatenation of the included categories'
  one-line `insight` fields — based on a simple length check. Neither is real summarization:
  no actual compression or rewriting happens. This shows up concretely at the low end: a
  2-slide request (0 charts included) falls back to the full 8-bullet narrative rather than a
  genuinely condensed 2-3 sentence takeaway, because there's nothing to build a scoped summary
  from and no mechanism to *generate* one. The deck also has no concept of who's viewing it —
  every user gets the same static content selection regardless of role or context, beyond the
  one slide-count knob.

  With more time, I'd replace this static selection with a small LLM call that generates an
  actually-contextualized summary: tailored to the requested slide count/compression level, the
  specific categories included, and ideally a lightweight user profile (e.g. "executive" vs
  "analyst") feeding into tone and depth — closer to genuine contextual summarization than
  picking between two fixed strings. I'd deliberately keep this scoped to the summary slide
  only, not the chart data or citations, since those need to stay exact/verifiable — an LLM
  rewriting statistics or source attribution risks introducing inaccuracies in the one place
  precision matters most. Honestly, I'd treat this as a real scope increase, not a quick add:
  it introduces a new dependency (API call or local model), non-determinism (harder to test and
  verify than the current deterministic logic), latency/cost, and a new failure mode (API
  unavailable, hallucinated content) — worth doing for a real product, but correctly out of
  scope for this prototype.