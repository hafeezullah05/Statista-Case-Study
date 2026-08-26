# Edge Cases — Found, Fixed, and Verified

This documents the specific edge cases discovered and fixed during development, along with how
each was verified. No automated test suite was built (see README's "Known limitations" — out of
scope per the brief); verification was manual, run against the real JSON and hand-constructed
malformed inputs in a scratch script.

## 1. Normal input produces the expected slide count
**Case:** Well-formed JSON, prompt requesting a slide count that matches the data.
**Behavior:** `add_title_slide` + one `add_chart_slide` per category + `add_summary_slide`
produces exactly `len(key_insights) + 2` slides.
**Verified:** Ran full pipeline against `gen_z_purchase_behavior_analysis.json` with a
"5-slide" prompt (3 categories + title + summary = 5) — confirmed 5 slides generated.

## 2. `metrics` is `None` (or not a list at all)
**Case:** A `key_insights` entry has a missing or malformed `metrics` field.
**Behavior:** `add_chart_slide` checks `isinstance(metrics, list)` before iterating — if false,
the loop is skipped entirely, `labels`/`values` stay empty, and a "No chart data available"
placeholder textbox renders instead of a broken/empty chart.
**Verified:** Called `add_chart_slide(..., metrics=None, ...)` directly — no crash, placeholder
rendered, slide still saved successfully.

## 3. `metrics` contains a non-dict item
**Case:** A metrics list mixes valid dicts with a stray string/number.
**Behavior:** Each item is checked with `isinstance(m, dict)`; non-dict items are skipped via
`continue` rather than crashing on `m.get(...)`.
**Verified:** Called `add_chart_slide(..., metrics=['a string', 123, {'action': 'ok', 'percentage': 10}], ...)`
— confirmed only the valid dict became a bar, no exception raised.

## 4. `parse_prompt("5-slide...")` extracts the number correctly
**Case:** A prompt mentioning a slide count in the expected format.
**Behavior:** Regex `r'(\d+)[- ]slide'` (case-insensitive) matches and extracts the number.
**Verified:** `parse_prompt("Turn this into a 5-slide presentation for C-level colleagues")`
returned `{'slide_count': 5}`.

## 5. `parse_prompt("no number here")` returns `None`, not a crash
**Case:** A prompt that doesn't mention any slide count.
**Behavior:** `re.search` returns `None` when there's no match; `slide_count` stays `None`
rather than raising an error.
**Verified:** `parse_prompt("Just give me the standard deck")` returned `{'slide_count': None}`.

## 6. `slide_count` of `0` or `1` — two real bugs found and fixed
**Case:** A prompt requests fewer slides than the mandatory minimum (title + summary = 2).
**Bug found:** `max_charts = slide_count - 2` went negative (e.g. `-1` for `slide_count=1`),
and Python's negative list slicing (`list[:-1]`) silently returns *more* items than intended,
counting from the end — producing a larger deck than requested, backwards from expectations.
A second bug: `slide_count=0` is falsy in Python, so `if preferences['slide_count']:` treated
it identically to "no count found," silently falling back to the full deck instead of the
requested (impossible) zero.
**Fix:**
- `max_charts = max(0, slide_count - 2)` — clamps to never go negative.
- Changed the check to `if preferences['slide_count'] is not None:` — distinguishes "not found"
  (`None`) from "found, but zero" (`0`).
- Added a printed note when the request is below the achievable minimum, explaining the
  2-slide floor rather than silently ignoring or misinterpreting the request.
**Verified:** Tested `slide_count` values of `0`, `1`, `2`, `3`, `5`, `10` directly against a
mock 3-category list — confirmed each produces the correct, expected slide count with no
negative-slicing surprises.