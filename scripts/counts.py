"""Parse YouTube's localized compact counts without treating 1K as 1."""
import math
import re
from decimal import Decimal, InvalidOperation

_MULTIPLIERS = {
    "k": 1000, "thousand": 1000, "אלף": 1000, "אלפים": 1000,
    "m": 1000000, "million": 1000000, "מיליון": 1000000, "מיל׳": 1000000,
    "b": 1000000000, "billion": 1000000000, "מיליארד": 1000000000,
}
_PATTERN = re.compile(
    r"([0-9][0-9.,\s\u00a0\u202f]*)"
    r"(thousand|million|billion|מיליארד|מיליון|מיל׳|אלפים|אלף|[kmb])?",
    re.IGNORECASE,
)

def parse_count(value):
    if value is None or isinstance(value, bool):
        return 0
    if isinstance(value, (int, float)):
        return max(int(value), 0) if math.isfinite(value) else 0
    text = re.sub(r"[\u200e\u200f\u202a-\u202e\u2066-\u2069]", "", str(value)).strip().lower()
    if text.startswith("-"):
        return 0
    match = _PATTERN.search(text)
    if not match:
        return 0
    number = re.sub(r"\s+", "", match.group(1))
    suffix = match.group(2)
    multiplier = _MULTIPLIERS.get(suffix, 1)
    if not suffix and re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", number):
        number = number.replace(",", "").replace(".", "")
    elif "." in number or "," in number:
        index = max(number.rfind("."), number.rfind(","))
        number = re.sub(r"[.,]", "", number[:index]) + "." + number[index + 1:]
    try:
        return max(int(Decimal(number) * multiplier), 0)
    except (InvalidOperation, ValueError, OverflowError):
        return 0
