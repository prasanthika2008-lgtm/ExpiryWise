"""OCR-based expiry date extraction (Phase 2)."""
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