# Project Log — Statista Chat-to-Slides Generator

A record of what was built, in what order, and what's left — for picking this project back up
later.

## What exists today

```
main.ipynb                     — orchestration notebook: load JSON → parse prompt → build deck →
                                  export PDF → verify output
slides_code/
  builder.py                   — DeckBuilder class: add_title_slide, add_chart_slide,
                                  add_summary_slide, save
  prompt.py                    — parse_prompt(): regex-based slide-count extraction from a
                                  free-text prompt
  EDGE_CASE.md                 — specific edge cases found, fixed, and how each was verified
README.md                      — setup, what it does, how to run, libraries + why, limitations
NOTES.md                       — personal reference of gotchas/decisions (interview prep)
requirements.txt                — python-pptx, jupyter, ipykernel
.gitignore                      — excludes venv/, output/, __pycache__/, etc.
example_output/                 — one committed, reviewable example: statista_ppt.pptx,
                                  statista_pdf.pdf
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
2. Cross-platform LibreOffice path detection.
3. A small `pytest` suite covering the cases in `EDGE_CASE.md`.
4. Guard the remaining unguarded top-level fields (missing `title`, empty `key_insights`, empty
   `summary_text`) the same way `metrics` is guarded today.
5. `staging` → `main` git branch workflow (in progress as of this log).
