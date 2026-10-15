"""
ocr.py
OCR-based expiry date extraction (Phase 2).

Flow:
  photo -> extract_text() -> raw text -> parse_expiry_date() -> "YYYY-MM-DD"

Needs Tesseract installed on the computer plus the pytesseract and Pillow
Python packages. If pytesseract is missing the app still runs, and
extract_text() raises a RuntimeError that app.py turns into a 503 response.
"""
import calendar
import os
import re
from datetime import date, datetime

from PIL import Image, ImageOps

try:
    import pytesseract
except ImportError:  # app still runs without OCR installed
    pytesseract = None

# On Windows, point pytesseract at the default install location (if it exists).
WINDOWS_TESSERACT = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if pytesseract and os.path.exists(WINDOWS_TESSERACT):
    pytesseract.pytesseract.tesseract_cmd = WINDOWS_TESSERACT

# Date shapes commonly printed on packaging
DATE_PATTERN = re.compile(
    r"""
    \b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b        # 15/03/2027, 15-03-27
    | \b\d{1,2}\s?[A-Za-z]{3,9}\.?\s?\d{2,4}\b # 15 JAN 2027, 15JAN27
    | \b[A-Za-z]{3,9}\.?\s?\d{4}\b             # JAN 2027
    | \b\d{1,2}[./-]\d{4}\b                    # 03/2027
    """,
    re.VERBOSE,
)

# Formats with a day, tried first.
FULL_FORMATS = [
    "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y",
    "%d/%m/%y", "%d-%m-%y", "%d.%m.%y",
    "%d %b %Y", "%d%b%Y", "%d %b %y", "%d%b%y",
    "%d %B %Y", "%d %B %y",
]
# Formats with only a month and year, tried if no full format matches.
MONTH_ONLY_FORMATS = ["%m/%Y", "%m-%Y", "%m.%Y", "%b %Y", "%b%Y", "%B %Y"]


def _parse_one(text):
    """Parse one date string. Month-only dates become the last day of that month.

    Args:
        text: A date-like string such as "15/03/2027" or "JAN 2027".

    Returns:
        datetime.date or None: The parsed date, or None if no format matches.
    """
    text = text.strip()
    # Dots are removed from month-name dates ("JAN.") and turned into slashes
    # in numeric dates ("15.03.2027") so both match the formats above.
    text = text.replace(".", "") if re.search(r"[A-Za-z]", text) else text.replace(".", "/")
    for fmt in FULL_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    for fmt in MONTH_ONLY_FORMATS:
        try:
            parsed = datetime.strptime(text, fmt)
            # "Best before JAN 2027" is valid until the end of that month.
            last_day = calendar.monthrange(parsed.year, parsed.month)[1]
            return date(parsed.year, parsed.month, last_day)
        except ValueError:
            pass
    return None


def parse_expiry_date(text):
    """Return the most likely expiry date (ISO string) found in OCR text, or None.

    Packaging often shows both a manufacture and an expiry date, so when
    several dates are found the latest one is chosen.

    Args:
        text: Raw text returned by OCR (may be None or empty).

    Returns:
        str or None: The date as "YYYY-MM-DD", or None if no valid date is found.
    """
    candidates = []
    for match in DATE_PATTERN.findall(text or ""):
        parsed = _parse_one(match)
        # Ignore impossible years, which are usually OCR mistakes.
        if parsed and 2000 <= parsed.year <= 2100:
            candidates.append(parsed)
    return max(candidates).isoformat() if candidates else None


def extract_text(image_file):
    """Run OCR on an image (path or file object) and return the raw text.

    The image is cleaned first to improve accuracy: rotation fixed,
    converted to grayscale, small photos enlarged, contrast increased.

    Args:
        image_file: A file path or an open file object.

    Returns:
        str: The text Tesseract found in the image.

    Raises:
        RuntimeError: If pytesseract is not installed.
    """
    if pytesseract is None:
        raise RuntimeError("pytesseract is not installed")
    image = Image.open(image_file)
    image = ImageOps.exif_transpose(image).convert("L")      # fix rotation, grayscale
    if image.width < 1000:                                    # upscale small photos
        scale = 1000 / image.width
        image = image.resize((1000, int(image.height * scale)))
    image = ImageOps.autocontrast(image)
    return pytesseract.image_to_string(image, config="--psm 6")


def extract_expiry_date(image_file):
    """Read an image and return its expiry date together with the raw text.

    Args:
        image_file: A file path or an open file object.

    Returns:
        tuple: (expiry_date, raw_text). expiry_date is "YYYY-MM-DD" or None.
    """
    text = extract_text(image_file)
    return parse_expiry_date(text), text