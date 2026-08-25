## python-pptx gotchas

- **slide_layouts[6] = "Blank"** — not a Python rule, just where the blank layout happens to
  sit in python-pptx's default template. A custom template could order layouts differently.

- **word_wrap=False + auto_size=SHAPE_TO_FIT_TEXT by default** — a textbox grows *sideways*
  instead of wrapping, which overflowed the slide edge on a long title. Fixed with
  `text_frame.word_wrap = True` on every textbox.

- **add_chart() returns a GraphicFrame, not the Chart itself** — need `.chart` to reach
  `.value_axis` / `.category_axis` / `.plots[0]`.

- **A fresh text_frame already has one empty paragraph** — for multi-paragraph text (bullets),
  reuse `paragraphs[0]` for the first item, only call `.add_paragraph()` from the second on.
  Otherwise you get a stray blank line above your first bullet.

## Data-handling decisions

- **Inconsistent JSON keys** — metrics use `action`/`statement`/`brand` depending on category,
  no single consistent label field. Handled with a `.get()` fallback chain instead of hardcoding
  one key.

- **Missing `percentage` defaults to 0** — a judgment call; could visually misread as "really
  was zero" vs "data missing." Would reconsider with more time (skip vs. flag instead of fake 0).

- **Sentence-splitting heuristic** (`split('. ')`) failed on a colon+paragraph-break in the
  source text — fixed by splitting on `\n\n` first, then sentences within each paragraph.
  Still a crude heuristic (misfires on abbreviations/decimals) — good enough for prototype scope.

- **Edge-case guards added deliberately, not everywhere** — `metrics` being None/wrong-type/
  containing non-dicts is guarded (falls back to placeholder). Missing `title` or empty
  `key_insights` is NOT guarded — a scoped decision, documented in README, not an oversight.

## Chart rendering

- **Truncating chart labels loses real information** — first fix (textwrap.shorten) silently
  cut survey statement text. Correct fix: smaller axis font + full text, no truncation.

- **Default chart colors are viewer-dependent** — PowerPoint/Keynote/LibreOffice each apply
  their own default theme to a chart with no explicit colors, so the same file looked different
  across viewers. Fixed by setting explicit RGB per bar (`point.format.fill`), baking the
  palette into the file itself.

- **Palette is fixed at 10 colors, wraps via modulo** — Brand Preferences slide has exactly 10
  bars, right at the edge. More than 10 would repeat colors.

## PDF export

- **python-pptx has no PDF export** — PDF comes from converting the already-built pptx through
  LibreOffice's headless CLI (`soffice --headless --convert-to pdf`), via Python `subprocess`.
  Not two independent implementations — one file, converted, not rebuilt.

- **macOS quarantine flag broke the first attempt** — `xattr -cr /Applications/LibreOffice.app`
  fixed "source file could not be loaded." A Gatekeeper thing, not a code bug.

- **Hardcoded macOS-only path** — `subprocess` call won't work on Windows/Linux as-is. Known
  limitation, documented in README, not fixed (would need `platform.system()` branching).

- **Considered building PDF independently via reportlab** — rejected: real duplicate
  implementation for the same data, and PDF was never actually a hard requirement (brief says
  "PDF/PowerPoint," not "PDF and PowerPoint").

## Process / scope

- **RAG is irrelevant here** — this is a deterministic transform (known JSON → known slide
  format), not retrieval over unknown documents. Reaching for RAG would signal not understanding
  the actual problem.

- **User-preference / prompt feature deliberately deferred to last** — sequencing choice, not
  an oversight; build the working pipeline first, then decide what's actually configurable.
  
- **No fine-grained git history** — iterated by testing against real output, not committing
  every step. Not a grading criterion for this exercise; explain the process verbally using
  these notes rather than relying on commit log.