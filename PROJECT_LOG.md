# Project Log — Statista Chat-to-Slides Generator

A record of what was built, in what order, and what's left — for picking this project back up
later.

## What exists today

```
main.py                        — CLI entry point: load JSON → interactive prompt → build deck →
                                  export PDF → verify output. `python main.py` to run.
main.ipynb                     — identical pipeline, interactive/exploratory notebook form.
                                  Both entry points import the same slides_code modules.
slides_code/
  builder.py                   — DeckBuilder class (fully docstringed): add_title_slide,
                                  add_chart_slide, add_summary_slide, save
  prompt.py                    — parse_prompt(): regex-based slide-count extraction from a
                                  free-text prompt (fully docstringed)
  EDGE_CASE.md                 — 9 specific edge cases found, fixed, and how each was verified
README.md                      — setup, what it does, how to run, libraries + why, and a
                                  thorough "known limitations" section (7 entries, several with
                                  proposed solutions and time estimates)
NOTES.md                       — personal reference of gotchas/decisions (interview prep)
requirements.txt               — python-pptx, jupyter, ipykernel
.gitignore                     — excludes venv/, __pycache__/, .ipynb_checkpoints/, .DS_Store
example_output/                — the single output destination: statista_ppt.pptx,
                                  statista_pdf.pdf. Both the working output folder and the
                                  committed submission example (same thing, deliberately —
                                  this is a "run once and show us" submission, not an ongoing
                                  pipeline)
Task Requirment/                — the original briefing PDF and sample input JSON (given, not
                                  generated)
```

## Build order (roughly chronological)

1. Read the briefing PDF and sample JSON — understood the task as a deterministic JSON→slides
   transform, not a retrieval/RAG problem.
2. Set up git repo, connected to GitHub remote.
3. Designed `DeckBuilder` class — one method per slide type, shared `Presentation` state via
   `self.prs`.
4. Built `add_title_slide`, then `add_chart_slide` (native pptx charts, not images) — found and
   fixed the `word_wrap`/`auto_size` default that caused text to overflow slide edges.
5. Handled the JSON's inconsistent metric label keys (`action`/`statement`/`brand`) with a
   `.get()` fallback chain.
6. Built `add_summary_slide` — sentence-splitting into bullets, fixed an embedded-newline bug
   that merged two unrelated sentences into one bullet.
7. Added defensive guards for malformed `metrics` (wrong type, non-dict items, empty) with a
   placeholder fallback instead of crashing.
8. Added PDF export via LibreOffice headless `subprocess` call, wired into the notebook.
9. Fixed chart color consistency (explicit per-bar RGB colors, since default theme colors
   diverged between PowerPoint/Keynote/LibreOffice).
10. Built the user-preferences feature (`prompt.py`) — slide-count parsing only, deliberately
    scoped down from the full tone/branding/focus-area brief.
11. Found and fixed two real bugs in the slide-count logic: negative list slicing on low
    requests, and Python's `0`-is-falsy gotcha silently ignoring an explicit zero request.
12. Made the prompt interactive (`input()`) with a safe default fallback.
13. Formatted all code to PEP8 (verified with `pycodestyle`/`nbqa`, not just autopep8'd blindly).
14. Documented edge cases, wrote the README, committed a permanent example output.
15. Found and fixed a subtitle/title overlap (the `word_wrap` fix from step 4 let long titles
    wrap to 2 lines, which then collided with a fixed-position subtitle below it) and a missing
    "%" unit on the chart's numeric axis.
16. Added `main.py` — the same pipeline as a plain CLI script, per the brief's note that a
    script works fine too. Removed the `! pip install` cell from the notebook (dependencies
    belong solely in `requirements.txt`).
17. Collapsed the separate `output/` (scratch) and `example_output/` (committed) folders into
    just `example_output/` — this submission's output *is* the example, no need for two.
18. Found and fixed a real bug: LibreOffice's `--convert-to pdf` always names its output after
    the input file's basename, ignoring any intended output filename — was initially masked by
    a stale leftover file with the correct name. Fixed with an explicit rename after conversion.
19. Found and fixed an inconsistency: the summary slide always used the full JSON narrative
    regardless of how many categories were actually charted in a trimmed deck. Scoped the
    summary to match what's shown; this introduced (and then required fixing) a follow-on bug
    where 0 charted categories produced a blank summary slide.
20. Added docstrings throughout (`DeckBuilder`, `parse_prompt`, all of `main.py`'s functions).
21. Documented 3 more limitations, each with a proposed solution: the slide-count parser's
    silent failure on unexpected input formats, the summary's static/non-contextual content
    (with a scoped proposal for a small-LLM-based fix), and category selection being
    position-based rather than user-driven.
22. Brought `NOTES.md`, `PROJECT_LOG.md`, and `EDGE_CASE.md` up to date with everything above —
    all three had fallen behind the actual state of the code partway through the session.

## What's deliberately NOT built (and why)

- **Tone / branding / focus-area parsing** — brief names these alongside slide count; only slide
  count was implemented given time constraints. The parser is structured so extending it (more
  regex/keyword matching in `prompt.py`) wouldn't require touching `DeckBuilder`.
- **Cross-platform PDF export** — `main.ipynb` hardcodes the macOS LibreOffice path. Would need
  `platform.system()` branching to support Windows/Linux.
- **Automated test suite** — verified manually against real and hand-constructed malformed
  inputs (see `EDGE_CASE.md`), no `pytest` suite. Explicitly out of scope per the brief.
- **Independent PDF renderer (reportlab)** — considered, rejected: would duplicate the slide-
  building logic in a second library with no shared object model, for a format that was never a
  hard requirement (brief says "PDF/PowerPoint," not "and").

## Ideas for future work, roughly prioritized

1. Extend `parse_prompt()` to match focus-area keywords against category names (reorder/filter
   `key_insights`) and a small set of tone keywords (e.g. "C-level" → fewer summary bullets).
   Estimated ~2.5-3.5h for a version at the same quality bar as slide-count — see README for
   the itemized breakdown.
2. Let the user choose *which* categories get charted, not just *how many* — either via the
   same prompt-keyword-matching as focus areas, or an explicit numbered-selection menu for the
   CLI. Currently a trimmed deck always keeps the first N categories in JSON order.
3. Replace the summary slide's static text-selection (full narrative vs. concatenated
   one-liners) with a small LLM call that genuinely summarizes/contextualizes to the requested
   scope and, ideally, a lightweight user profile — scoped deliberately to just the summary
   text, not chart data or citations, to keep accuracy where it matters most.
4. Fix the slide-count parser's silent failure on a bare number with no "slide" word attached
   (e.g. typing just "4") — accept a bare-number fallback, and print a message when nothing is
   understood instead of silently defaulting.
5. Cross-platform LibreOffice path detection (`platform.system()` branching) instead of the
   current hardcoded macOS path.
6. A small `pytest` suite covering the cases in `EDGE_CASE.md`.
7. Guard the remaining unguarded top-level fields (missing `title`, empty `key_insights`, empty
   `summary_text`) the same way `metrics` is guarded today.
8. `staging` → `main` git branch workflow.
