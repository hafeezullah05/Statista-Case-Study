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


  ## User preferences / prompt feature

- **Why it matters**: without this, the tool always produces the identical deck regardless of
  who's asking or why. The brief explicitly names free-text user preferences as an input
  ("Turn this into a 5-slide presentation...") — this is what makes the tool responsive rather
  than a static report generator.

- **Kept minimal on purpose**: only `slide_count` extraction via regex (`slides_code/prompt.py`)
  — not focus/tone. RAG/NLP would be overkill for extracting a number from a sentence; a fixed
  keyword/regex parser is simple, explainable, and sufficient for this scope.

- **Design**: parsing (turn text → structured data) is a separate step from applying
  (use that data to change what gets built) — kept `parse_prompt()` independent of `DeckBuilder`
  so interpretation and rendering don't get tangled together.

- **Default behavior is unchanged when nothing's specified** — if `slide_count` isn't found in
  the prompt, `max_charts` stays `None`, and the full, untouched deck (all categories) is built.
  The feature only kicks in when the prompt actually requests something.
  
- **Edge case: what if the user asks for more slides than there's data for?**
  (e.g. "10-slide" but only 3 categories exist) — `list[:n]` in Python never errors even when
  `n` exceeds the list length, it just returns everything available. So this doesn't crash, but
  it *would* silently under-deliver (5 slides instead of the requested 10) without saying so.
  Fixed by adding an explicit check that prints a note when the request exceeds what's
  available, so the shortfall is visible instead of silent.

- **Edge case: what if the user asks for FEWER slides than the mandatory minimum?** (title +
  summary = 2 slides, always present). `slide_count - 2` can go negative (e.g. `-1` for a
  request of `1`), and Python's negative list slicing (`list[:-1]`) silently returns *more*
  items than intended, counting from the end — the opposite of what "fewer slides" should mean.
  A second, separate bug: `slide_count=0` is falsy in Python, so a plain `if
  preferences['slide_count']:` check treated an explicit zero identically to "no count found,"
  silently defaulting to the full deck. Fixed both: `max(0, slide_count - 2)` clamps to never
  go negative, and the check became `is not None` to distinguish "not found" from "found, but
  zero." See `EDGE_CASE.md` #6 for the full verification.

## Layout/positioning gotchas (found by actually rendering and looking)

- **Subtitle overlapped a wrapped 2-line title** — fixing the earlier `word_wrap` overflow bug
  meant a long title could now wrap to 2 lines, but the subtitle box below it had a fixed `top`
  position that assumed a 1-line title. Fixed by moving the subtitle's vertical position down
  (`Inches(3.2)` → `Inches(3.9)`) to leave room. A patch, not a robust fix — a 3-line title
  would hit the same problem again; a proper fix would calculate position dynamically based on
  how many lines the title actually wrapped to, which python-pptx doesn't make easy.

- **Chart's numeric axis had no unit indicator** — the percentage values (0-60) had no "%"
  label anywhere near them, just the chart's title text doing that job informally. Fixed by
  setting `value_axis.has_title = True` and an explicit "Percentage (%)" axis title.
  `add_chart()` returns a `GraphicFrame`, not the `Chart` object itself — need `.chart` to reach
  `.value_axis`/`.category_axis` at all.

## Post-PEP8 additions (main.py, docstrings, output consolidation)

- **Converted the notebook pipeline into `main.py`** (a plain CLI script) alongside
  `main.ipynb`, per the brief's own note that "a script you run from the command line works
  just fine." Both import the same `slides_code` modules — zero logic duplicated, just two
  entry points into the same pipeline.

- **Removed `! pip install python-pptx` from the notebook** (a friend's suggestion, and correct
  practice) — dependency declaration belongs solely in `requirements.txt`, not scattered into
  notebook cells that only cover one package and could silently install into the wrong
  environment.

- **Collapsed `output/` (gitignored scratch) and `example_output/` (committed example) into
  just `example_output/`** — this is a "run once and show us the output" submission, not an
  ongoing pipeline, so the run's output and the submitted example are the same thing. Simpler
  than maintaining two folders for no real benefit at this scale.

- **LibreOffice ignores any output filename you'd set — always names the PDF after the input's
  basename.** Found via actual testing, initially masked by a stale leftover file with the
  correct name from an earlier manual run (a false-positive "OK" in `verify_output`). Fixed by
  renaming the file LibreOffice actually produces to the intended name right after conversion.
  See `EDGE_CASE.md` #9.

- **Summary slide didn't match a trimmed deck's actual content** — always used the full JSON
  narrative regardless of how many categories were actually charted, so a partial deck's
  summary referenced dropped content. Fixed by scoping the summary to just the included
  categories' `insight` lines when the deck is a genuine subset, keeping the full narrative
  when nothing was dropped. This introduced a follow-on bug: 0 categories included → empty
  string → blank summary slide. Fixed with an `insights_to_build and` guard so 0 categories
  falls back to the full narrative instead of nothing. See `EDGE_CASE.md` #7 and #8.

- **Added docstrings throughout** (`DeckBuilder` + all methods, `parse_prompt`, every function
  in `main.py`) — PEP 257-style, documenting purpose/args/returns, distinct from the inline `#`
  comments explaining *why* a specific line exists.

## Documented-but-not-built (see README's "Known limitations" for full detail)
- Tone/branding/focus-area parsing (slide count only was implemented) — estimated ~2.5-3.5h to
  build to the same quality bar, itemized in the README.
- The slide-count parser fails silently on input outside its exact expected pattern (e.g. a
  bare "4" with no word "slide" attached) — found via actual use, not just theorizing.
- Summary content is static/selected between two fixed texts, not genuinely summarized or
  contextualized to a specific user — proposed a small-LLM-based fix, scoped deliberately to
  just the summary text (not chart data/citations, where accuracy matters most).
- Which categories get included in a trimmed deck is decided by position in the JSON, not user
  interest — proposed either keyword-matching in the prompt, or an explicit numbered-selection
  menu for the CLI.