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
    "image_front_url,nutrition_data_per,states_tags,product_quantity_unit"
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


def nutrition_indicator(nutrition: dict) -> dict:
    """Transparent experimental composition indicator per 100 g or 100 ml.

    It is NOT a validated health-risk assessment or a replacement for Nutri-Score.
    Undefined required nutrients produce an unrated product, never invented zeros.
    Thresholds and weights are published to the caller for review.
    """
    required = (
        "calories_kcal", "saturated_fat_g", "sugars_g",
        "sodium_mg", "protein_g", "fiber_g",
    )
    missing = [key for key in required if nutrition.get(key) is None]
    methodology = {
        "version": "beta-1",
        "basis": "per 100 g or 100 ml (based on product category)",
        "formula": "80 minus sugar, saturated-fat, sodium and excess-energy points; plus fiber and protein points; clamped to 0–100.",
        "limits": (
            "Experimental, not clinically validated. Does not measure food safety, "
            "processing, ingredient risk, portion size or personal suitability. "
            "Compare similar food categories only."
        ),
        "required": list(required),
    }
    if missing:
        return {"score": None, "missing": missing, "methodology": methodology,
                "factors": []}
    calories = nutrition["calories_kcal"]
    factors = [
        ("Sugar", -min(25.0, nutrition["sugars_g"] * 1.25)),
        ("Saturated fat", -min(20.0, nutrition["saturated_fat_g"] * 4.0)),
        ("Sodium", -min(20.0, nutrition["sodium_mg"] / 40.0)),
        ("Energy density", -min(15.0, max(0, calories - 200) * 0.06)),
        ("Fiber", min(10.0, nutrition["fiber_g"] * 2.0)),
        ("Protein", min(10.0, nutrition["protein_g"] * (2.0 / 3.0))),
    ]
    score = max(0, min(100, round(80 + sum(points for _, points in factors))))
    return {
        "score": score,
        "missing": [],
        "methodology": methodology,
        "factors": [{"label": name, "points": round(points, 1)} for name, points in factors],
    }


def normalize_product(barcode: str, product: dict) -> dict:
    nutrition = _nutrition(product)
    indicator = nutrition_indicator(nutrition)
    required_fields = ("calories_kcal", "protein_g", "carbs_g", "fat_g",
                       "saturated_fat_g", "sugars_g", "fiber_g", "sodium_mg")
    available = [field for field in required_fields if nutrition[field] is not None]
    grade = str(product.get("nutriscore_grade") or "").lower()
    if grade not in ("a", "b", "c", "d", "e"):
        grade = None
    unit = product.get("product_quantity_unit")
    nutrition_unit = unit if unit in ("g", "ml") else None
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
        "nutrition_unit": nutrition_unit,
        "nutri_score_grade": grade,
        "delphiafit_score_0_100": indicator["score"],
        "score_status": "experimental" if indicator["score"] is not None else "unrated",
        "score_note": (
            "Experimental nutrition composition indicator. Not a health or safety rating."
            if indicator["score"] is not None else
            "Not rated: required nutrition values are missing. No values were assumed."
        ),
        "score_factors": indicator["factors"],
        "score_methodology": indicator["methodology"],
        "missing_score_nutrients": indicator["missing"],
        "data_completeness_percent": round(len(available) / len(required_fields) * 100),
        "missing_nutrients": [key for key in required_fields if key not in available],
        "image_url": image,
        "source": {
            "name": "Open Food Facts",
            "url": f"{OFF_ROOT}/product/{barcode}",
            "license": "Open Database License (ODbL) 1.0",
            "image_license_note": "Product images may have separate attribution requirements; see source page.",
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
