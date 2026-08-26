import re


def parse_prompt(prompt):
    """Extract structured preferences from a free-text presentation request.

    Currently only detects a requested slide count (e.g. "5-slide" or
    "5 slides", case-insensitive); tone/branding/focus-area preferences named
    in the brief are not yet parsed -- see README's "Known limitations".

    Args:
        prompt: a free-text string, e.g. "Turn this into a 5-slide
            presentation for C-level colleagues".

    Returns:
        dict with key 'slide_count': an int if a number was found before the
        word "slide", otherwise None.
    """
    slide_count = None
    match = re.search(r'(\d+)[- ]slide', prompt, re.IGNORECASE)
    if match:
        slide_count = int(match.group(1))

    return {
        'slide_count': slide_count,
    }
