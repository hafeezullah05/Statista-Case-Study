"""
Statista Chat-to-Slides Generator

Loads a structured Statista AI chat JSON response, optionally takes a free-text
user preference prompt, and generates a PowerPoint deck (plus a PDF export via
LibreOffice) summarizing the analysis.

Run from the command line:
    python main.py
"""

import json
import os
import subprocess

from slides_code.builder import DeckBuilder
from slides_code.prompt import parse_prompt


JSON_PATH = 'Task Requirment/gen_z_purchase_behavior_analysis.json'
OUTPUT_DIR = 'example_output'
PPTX_PATH = os.path.join(OUTPUT_DIR, 'statista_ppt.pptx')
PDF_PATH = os.path.join(OUTPUT_DIR, 'statista_pdf.pdf')
SOFFICE_PATH = "/Applications/LibreOffice.app/Contents/MacOS/soffice"


def load_data(path):
    with open(path, 'r') as file:
        return json.load(file)


def get_user_prompt():
    user_prompt = input(
        "Enter your presentation request (e.g. \"Turn this into a 5-slide presentation\"). "
        "Only slide count is currently understood — press Enter for the default: "
    ).strip()

    if not user_prompt:
        user_prompt = "Turn this into a 5-slide presentation for C-level colleagues"

    return user_prompt


def build_deck(analysis, preferences, output_path):
    db = DeckBuilder()

    region = analysis['data_sources']['primary_region']
    subtitle = f"Prepared from Statista AI Chat Data — {region}, 2025"
    db.add_title_slide(analysis['title'], subtitle)

    insights_to_build = analysis['key_insights']

    max_charts = None
    if preferences['slide_count'] is not None:
        if preferences['slide_count'] < 2:
            print(f"Note: minimum possible deck size is 2 slides (title + summary) — "
                  f"requested {preferences['slide_count']}, generating 2 instead.")
        max_charts = max(0, preferences['slide_count'] - 2)  # minus title, minus summary

    if max_charts is not None and max_charts > len(insights_to_build):
        print(f"Note: only {len(insights_to_build)} insight categories available in the "
              f"data — requested {preferences['slide_count']} slides, generating "
              f"{len(insights_to_build) + 2} instead.")

    if max_charts is not None:
        insights_to_build = insights_to_build[:max_charts]

    for insight in insights_to_build:
        db.add_chart_slide(
            insight['category'],
            insight['insight'],
            insight['metrics'],
            insight['source']
        )

    db.add_summary_slide(analysis['summary'], analysis['data_sources'].get('caveat'))
    db.save(output_path)


def convert_to_pdf(pptx_path, output_dir):
    if not os.path.exists(SOFFICE_PATH):
        print(f"LibreOffice not found at {SOFFICE_PATH} — skipping PDF export. "
              f"pptx was still generated successfully.")
        return False

    result = subprocess.run(
        [SOFFICE_PATH, "--headless", "--convert-to", "pdf", "--outdir", output_dir, pptx_path],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    print("Return code:", result.returncode)

    if result.returncode != 0:
        return False

    # LibreOffice always names its output after the input file's basename
    # (e.g. statista_ppt.pptx -> statista_ppt.pdf) -- it has no option to set
    # an arbitrary output filename, only an output directory. Rename it to
    # match our intended naming convention.
    input_basename = os.path.splitext(os.path.basename(pptx_path))[0]
    libreoffice_output = os.path.join(output_dir, f"{input_basename}.pdf")
    if libreoffice_output != PDF_PATH and os.path.exists(libreoffice_output):
        os.replace(libreoffice_output, PDF_PATH)

    return True


def verify_output(paths):
    for f in paths:
        if os.path.exists(f):
            size_kb = os.path.getsize(f) / 1024
            print(f"OK  {f}  ({size_kb:.1f} KB)")
        else:
            print(f"MISSING  {f}")


def main():
    data = load_data(JSON_PATH)
    analysis = data['analysis']

    user_prompt = get_user_prompt()
    preferences = parse_prompt(user_prompt)
    print(preferences)

    build_deck(analysis, preferences, PPTX_PATH)
    convert_to_pdf(PPTX_PATH, OUTPUT_DIR)
    verify_output([PPTX_PATH, PDF_PATH])


if __name__ == '__main__':
    main()
