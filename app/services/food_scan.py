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
    "image_front_url,nutrition_data_per,states_tags,product_quantity_unit,"
    "data_quality_errors_tags,no_nutrition_data"
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
    def bounded(name: str, limit: float):
        value = _nonnegative(source.get(name))
        return value if value is not None and value <= limit else None

    sodium_g = bounded("sodium_100g", 40)
    salt_g = bounded("salt_100g", 100)
    # OFF normalizes sodium_100g in grams; UI displays milligrams.
    # Exclude impossible per-100g values rather than creating false scores.
    return {
        "calories_kcal": bounded("energy-kcal_100g", 1000),
        "protein_g": bounded("proteins_100g", 100),
        "carbs_g": bounded("carbohydrates_100g", 100),
        "fat_g": bounded("fat_100g", 100),
        "saturated_fat_g": bounded("saturated-fat_100g", 100),
        "sugars_g": bounded("sugars_100g", 100),
        "fiber_g": bounded("fiber_100g", 100),
        "sodium_mg": round(sodium_g * 1000, 2) if sodium_g is not None else
                     round(salt_g * 1000 / 2.5, 2) if salt_g is not None else None,
    }


# These are DISPLAY anchors for the established five Nutri-Score grades, not a
# separate nutrient-profiling algorithm. Five grades mean five index values;
# never imply that 90 and 91 are independently measured health-risk differences.
GRADE_INDEX = {"a": 90, "b": 70, "c": 50, "d": 30, "e": 10}
GRADE_REQUIRED = ("calories_kcal", "saturated_fat_g", "sugars_g", "sodium_mg")
GRADE_STANDARD_URL = (
    "https://www.santepubliquefrance.fr/en/nutrition-and-physical-activity/nutri-score"
)


def standard_grade_index(product: dict, nutrition: dict) -> dict:
    """Map a provider-reported Nutri-Score grade to a transparent 0–100 index.

    We do NOT calculate Nutri-Score ourselves: official grade derivation differs
    by product class (food, beverage, oil, nuts, etc.) and algorithm version.
    Score only when the provider gives a valid grade and essential per-100g/ml
    nutrition data pass our integrity checks. A source grade does not establish
    that the packaging contains all allergens or that the food suits a person.
    """
    raw = product.get("nutriscore_grade")
    grade = str(raw).strip().lower() if isinstance(raw, str) else None
    if grade not in GRADE_INDEX:
        grade = None

    missing = [name for name in GRADE_REQUIRED if nutrition.get(name) is None]
    errors = product.get("data_quality_errors_tags")
    flagged = bool(errors) if isinstance(errors, list) else False
    no_nutrition = product.get("no_nutrition_data") is True
    reasons = []
    if grade is None:
        reasons.append("Open Food Facts has no supported Nutri-Score grade for this product.")
    if missing:
        reasons.append("Required nutrition facts are missing or invalid: " +
                       ", ".join(name.replace("_", " ") for name in missing) + ".")
    if flagged:
        reasons.append("The product record has a provider data-quality error.")
    if no_nutrition:
        reasons.append("The provider reports that nutrition data are unavailable.")

    methodology = {
        "version": "1.0",
        "name": "Nutri-Score-derived display index",
        "basis": "Provider-reported Nutri-Score A–E based on food composition per 100 g or 100 ml.",
        "standard": "Nutri-Score",
        "standard_url": GRADE_STANDARD_URL,
        "mapping": dict(GRADE_INDEX),
        "formula": (
            "A=90, B=70, C=50, D=30, E=10. This is a display conversion of "
            "five existing grades, not a second independently validated food score."
        ),
        "limits": (
            "Nutri-Score describes nutritional composition, not individual health "
            "effects, additive safety, allergens, ingredient authenticity, organic "
            "quality, portion size, or athletic-goal suitability. The Open Food Facts "
            "record may use an older Nutri-Score algorithm; its version is not verified."
        ),
        "required": list(GRADE_REQUIRED),
    }
    return {
        "score": GRADE_INDEX[grade] if not reasons else None,
        "grade": grade,
        "missing": missing,
        "reasons": reasons,
        "methodology": methodology,
        "factors": [],
    }


def normalize_product(barcode: str, product: dict) -> dict:
    nutrition = _nutrition(product)
    indicator = standard_grade_index(product, nutrition)
    required_fields = ("calories_kcal", "protein_g", "carbs_g", "fat_g",
                       "saturated_fat_g", "sugars_g", "fiber_g", "sodium_mg")
    available = [field for field in required_fields if nutrition[field] is not None]
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
        "nutri_score_grade": indicator["grade"],
        "delphiafit_score_0_100": indicator["score"],
        "score_status": "standard-derived" if indicator["score"] is not None else "unrated",
        "score_note": (
            "0–100 index derived from the provider's Nutri-Score grade. Five grade bands, "
            "not a personalized health or food-safety rating."
            if indicator["score"] is not None else
            "Not rated. " + " ".join(indicator["reasons"])
        ),
        "score_factors": indicator["factors"],
        "score_methodology": indicator["methodology"],
        "missing_score_nutrients": indicator["missing"],
        "score_unrated_reasons": indicator["reasons"],
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
