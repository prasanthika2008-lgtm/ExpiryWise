"""OCR-based expiry date extraction (Phase 2)."""
import calendar
import re
from datetime import date, datetime

from PIL import Image, ImageOps

try:
    import pytesseract
except ImportError:  # app still runs without OCR installed
    pytesseract = None
if pytesseract:
       pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
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

FULL_FORMATS = [
    "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y",
    "%d/%m/%y", "%d-%m-%y", "%d.%m.%y",
    "%d %b %Y", "%d%b%Y", "%d %b %y", "%d%b%y",
    "%d %B %Y", "%d %B %y",
]
MONTH_ONLY_FORMATS = ["%m/%Y", "%m-%Y", "%m.%Y", "%b %Y", "%b%Y", "%B %Y"]


def _parse_one(text):
    """Parse one date string. Month-only dates become the last day of that month."""
    text = text.strip()
    text = text.replace(".", "") if re.search(r"[A-Za-z]", text) else text.replace(".", "/")
    for fmt in FULL_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    for fmt in MONTH_ONLY_FORMATS:
        try:
            parsed = datetime.strptime(text, fmt)
            last_day = calendar.monthrange(parsed.year, parsed.month)[1]
            return date(parsed.year, parsed.month, last_day)
        except ValueError:
            pass
    return None


def parse_expiry_date(text):
    """Return the most likely expiry date (ISO string) found in OCR text, or None.

    Packaging often shows both a manufacture and an expiry date, so when
    several dates are found the latest one is chosen.
    """
    candidates = []
    for match in DATE_PATTERN.findall(text or ""):
        parsed = _parse_one(match)
        if parsed and 2000 <= parsed.year <= 2100:
            candidates.append(parsed)
    return max(candidates).isoformat() if candidates else None


def extract_text(image_file):
    """Run OCR on an image (path or file object) and return the raw text."""
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
    text = extract_text(image_file)
    return parse_expiry_date(text), text
