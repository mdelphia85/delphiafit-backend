"""Barcode product lookup, normalized nutrition facts, and bounded OFF cache.

No user data is sent to Open Food Facts; only the barcode is requested. Nutrient
grades are *provider-reported*, never invented by this service. Public product
metadata remains subject to Open Food Facts ODbL and image licensing.
"""
from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
import json
import re
from threading import Lock
from time import monotonic
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

VALID_BARCODE = re.compile(r"^[0-9]{8,14}$")
OFF_ROOT = "https://world.openfoodfacts.org"
LOOKUP_FIELDS = (
    "code,product_name,brands,ingredients_text,allergens_tags,traces_tags,"
    "additives_tags,nutriments,serving_size,quantity,nutriscore_grade,"
    "image_front_url,nutrition_data_per,states_tags"
)
TTL_SECONDS = 6 * 60 * 60
NOT_FOUND_TTL_SECONDS = 15 * 60
CACHE_MAX_ITEMS = 800
# OFF documents 15 GET product requests per minute per IP. Leave headroom.
MAX_PROVIDER_CALLS_PER_MINUTE = 12
_CACHE: dict[str, tuple[float, dict | None]] = {}
_REQUESTS = deque()
_LOCK = Lock()


class ScanProviderUnavailable(Exception):
    pass


class ScanRateLimited(Exception):
    pass


def valid_barcode(value: str) -> bool:
    return bool(VALID_BARCODE.fullmatch(value))


def _nonnegative(value):
    try:
        if value is None or isinstance(value, bool):
            return None
        number = float(value)
        if not (0 <= number <= 100_000):
            return None
        return round(number, 2)
    except (ValueError, TypeError, OverflowError):
        return None


def _safe_tags(values):
    if not isinstance(values, list):
        return []
    return [str(value).split(":", 1)[-1].replace("-", " ").strip()
            for value in values[:40] if isinstance(value, str)][:30]


def _fetch_provider(barcode: str) -> dict | None:
    params = urlencode({"fields": LOOKUP_FIELDS, "lc": "en", "product_type": "food"})
    url = f"{OFF_ROOT}/api/v3/product/{quote(barcode)}?{params}"
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "DelphiaFit/1.0 (https://delphiafit.com)",
        },
    )
    try:
        with urlopen(request, timeout=6) as response:
            raw = response.read(256 * 1024 + 1)
            if len(raw) > 256 * 1024:
                raise ScanProviderUnavailable("Product response exceeded size limit.")
            result = json.loads(raw)
    except HTTPError as exc:
        if exc.code == 404:
            return None
        raise ScanProviderUnavailable("Food information provider temporarily unavailable.") from None
    except (URLError, TimeoutError, ValueError, OSError) as exc:
        raise ScanProviderUnavailable("Food information provider temporarily unavailable.") from exc
    if not isinstance(result, dict) or not isinstance(result.get("product"), dict):
        return None
    if result.get("status") == "failure":
        return None
    return result["product"]


def _nutrition(product: dict) -> dict:
    source = product.get("nutriments")
    if not isinstance(source, dict):
        source = {}
    sodium_g = _nonnegative(source.get("sodium_100g"))
    salt_g = _nonnegative(source.get("salt_100g"))
    # OFF normalizes sodium_100g in grams; UI displays milligrams.
    return {
        "calories_kcal": _nonnegative(source.get("energy-kcal_100g")),
        "protein_g": _nonnegative(source.get("proteins_100g")),
        "carbs_g": _nonnegative(source.get("carbohydrates_100g")),
        "fat_g": _nonnegative(source.get("fat_100g")),
        "saturated_fat_g": _nonnegative(source.get("saturated-fat_100g")),
        "sugars_g": _nonnegative(source.get("sugars_100g")),
        "fiber_g": _nonnegative(source.get("fiber_100g")),
        "sodium_mg": round(sodium_g * 1000, 2) if sodium_g is not None else
                     round(salt_g * 1000 / 2.5, 2) if salt_g is not None else None,
    }


def normalize_product(barcode: str, product: dict) -> dict:
    nutrition = _nutrition(product)
    required_fields = ("calories_kcal", "protein_g", "carbs_g", "fat_g",
                       "saturated_fat_g", "sugars_g", "fiber_g", "sodium_mg")
    available = [field for field in required_fields if nutrition[field] is not None]
    grade = str(product.get("nutriscore_grade") or "").lower()
    if grade not in ("a", "b", "c", "d", "e"):
        grade = None
    image = product.get("image_front_url")
    if not isinstance(image, str) or not image.startswith("https://images.openfoodfacts.org/"):
        image = None
    return {
        "barcode": barcode,
        "product_name": str(product.get("product_name") or "").strip()[:180] or "Unnamed product",
        "brands": str(product.get("brands") or "").strip()[:180],
        "serving_size": str(product.get("serving_size") or "").strip()[:60],
        "quantity": str(product.get("quantity") or "").strip()[:60],
        "ingredients_text": str(product.get("ingredients_text") or "").strip()[:2500],
        "allergens": _safe_tags(product.get("allergens_tags")),
        "traces": _safe_tags(product.get("traces_tags")),
        "additives": _safe_tags(product.get("additives_tags")),
        "nutrition_per_100g_or_100ml": nutrition,
        "nutri_score_grade": grade,
        "delphiafit_score_0_100": None,
        "score_note": "DelphiaFit's own 0–100 nutrition scoring is not yet validated; no score is fabricated.",
        "data_completeness_percent": round(len(available) / len(required_fields) * 100),
        "missing_nutrients": [key for key in required_fields if key not in available],
        "image_url": image,
        "source": {
            "name": "Open Food Facts",
            "url": f"{OFF_ROOT}/product/{barcode}",
            "license": "Open Database License (ODbL) 1.0",
            "disclaimer": "Community-submitted data may be incomplete or incorrect. Verify the package label and allergen statement."
        },
    }


def get_product(barcode: str) -> dict | None:
    if not valid_barcode(barcode):
        raise ValueError("Barcode must contain 8 to 14 digits.")
    now = monotonic()
    with _LOCK:
        cached = _CACHE.get(barcode)
        if cached and cached[0] > now:
            return cached[1]
        while _REQUESTS and _REQUESTS[0] <= now - 60:
            _REQUESTS.popleft()
        if len(_REQUESTS) >= MAX_PROVIDER_CALLS_PER_MINUTE:
            raise ScanRateLimited("Product service is busy. Try again shortly.")
        _REQUESTS.append(now)
    product = _fetch_provider(barcode)
    normalized = normalize_product(barcode, product) if product else None
    with _LOCK:
        if len(_CACHE) >= CACHE_MAX_ITEMS:
            expired = [key for key, (expiry, _) in _CACHE.items() if expiry < now]
            for key in expired:
                _CACHE.pop(key, None)
            if len(_CACHE) >= CACHE_MAX_ITEMS:
                _CACHE.pop(next(iter(_CACHE)), None)
        _CACHE[barcode] = (now + (TTL_SECONDS if product else NOT_FOUND_TTL_SECONDS), normalized)
    return normalized
