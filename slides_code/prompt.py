import re


def parse_prompt(prompt):
    slide_count = None
    match = re.search(r'(\d+)[- ]slide', prompt, re.IGNORECASE)
    if match:
        slide_count = int(match.group(1))

    return {
        'slide_count': slide_count,
    }
