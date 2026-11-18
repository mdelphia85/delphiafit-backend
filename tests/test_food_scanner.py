"""Offline unit tests: nutrition scoring, missing data, and private scanner lookup cache."""
import unittest
from unittest.mock import patch

from app.services import food_scan


def sample_product():
    return {
        "product_name": "Plain test yogurt",
        "brands": "Example",
        "product_quantity_unit": "g",
        "quantity": "500 g",
        "serving_size": "125 g",
        "nutriscore_grade": "a",
        "allergens_tags": ["en:milk"],
        "nutriments": {
            "energy-kcal_100g": 70,
            "proteins_100g": 7,
            "carbohydrates_100g": 6,
            "fat_100g": 2,
            "saturated-fat_100g": 1,
            "sugars_100g": 5,
            "fiber_100g": 1,
            "sodium_100g": 0.05,
        },
    }


class FoodScannerTests(unittest.TestCase):
    def setUp(self):
        with food_scan._LOCK:
            food_scan._CACHE.clear()
            food_scan._REQUESTS.clear()

    def test_gtin_strings_keep_leading_zeros_and_reject_bad_input(self):
        self.assertTrue(food_scan.valid_barcode("00012345678905"))
        self.assertTrue(food_scan.valid_barcode("12345678"))
        self.assertFalse(food_scan.valid_barcode("123"))
        self.assertFalse(food_scan.valid_barcode("1234abc567"))
        self.assertFalse(food_scan.valid_barcode("1/../../env"))

    def test_normalizes_and_scores_complete_information(self):
        result = food_scan.normalize_product("00012345678905", sample_product())
        self.assertEqual(result["nutrition_unit"], "g")
        self.assertEqual(result["nutrition_per_100g_or_100ml"]["sodium_mg"], 50)
        self.assertEqual(result["allergens"], ["milk"])
        self.assertEqual(result["nutri_score_grade"], "a")
        self.assertGreaterEqual(result["delphiafit_score_0_100"], 0)
        self.assertLessEqual(result["delphiafit_score_0_100"], 100)
        self.assertEqual(result["score_status"], "standard-derived")
        self.assertEqual(result["delphiafit_score_0_100"], 90)
        self.assertIn("not a second independently validated", result["score_methodology"]["formula"])
        self.assertEqual(result["score_methodology"]["mapping"]["a"], 90)
        self.assertIn("ODbL", result["source"]["license"])

    def test_never_invents_missing_nutrition_facts_or_scores(self):
        product = sample_product()
        product["nutriments"].pop("sugars_100g")
        result = food_scan.normalize_product("12345678", product)
        self.assertIsNone(result["nutrition_per_100g_or_100ml"]["sugars_g"])
        self.assertIsNone(result["delphiafit_score_0_100"])
        self.assertEqual(result["score_status"], "unrated")
        self.assertIn("sugars_g", result["missing_score_nutrients"])

    def test_impossible_values_are_unrated_and_invalid_images_excluded(self):
        product = sample_product()
        product["nutriments"]["saturated-fat_100g"] = 900
        product["image_front_url"] = "https://example.org/tracker.png"
        result = food_scan.normalize_product("12345678", product)
        self.assertIsNone(result["delphiafit_score_0_100"])
        self.assertIsNone(result["image_url"])
        self.assertIn("saturated_fat_g", result["missing_score_nutrients"])

    def test_all_five_grade_bands_have_discrete_documented_index_values(self):
        for grade, expected in (("a", 90), ("b", 70), ("c", 50),
                                ("d", 30), ("e", 10)):
            with self.subTest(grade=grade):
                product = sample_product()
                product["nutriscore_grade"] = grade
                result = food_scan.normalize_product("12345678", product)
                self.assertEqual(result["delphiafit_score_0_100"], expected)
                self.assertEqual(result["nutri_score_grade"], grade)
                self.assertEqual(result["score_status"], "standard-derived")

    def test_missing_provider_grade_is_unrated_even_with_complete_nutrients(self):
        for grade in ("unknown", "not-applicable", "", None):
            with self.subTest(grade=grade):
                product = sample_product()
                product["nutriscore_grade"] = grade
                result = food_scan.normalize_product("12345678", product)
                self.assertIsNone(result["delphiafit_score_0_100"])
                self.assertEqual(result["score_status"], "unrated")
                self.assertIn("no supported Nutri-Score", result["score_note"])

    def test_missing_fiber_does_not_invent_values_or_recalculate_official_grade(self):
        product = sample_product()
        product["nutriments"].pop("fiber_100g")
        result = food_scan.normalize_product("12345678", product)
        self.assertIsNone(result["nutrition_per_100g_or_100ml"]["fiber_g"])
        self.assertEqual(result["delphiafit_score_0_100"], 90)
        self.assertLess(result["data_completeness_percent"], 100)

    def test_flagged_provider_data_quality_or_missing_nutrition_blocks_index(self):
        for overrides in (
            {"data_quality_errors_tags": ["en:nutrition-value-errors"]},
            {"no_nutrition_data": True},
        ):
            with self.subTest(overrides=overrides):
                product = {**sample_product(), **overrides}
                result = food_scan.normalize_product("12345678", product)
                self.assertIsNone(result["delphiafit_score_0_100"])
                self.assertEqual(result["score_status"], "unrated")
                self.assertTrue(result["score_unrated_reasons"])

    def test_provider_is_cached_by_barcode(self):
        with patch.object(food_scan, "_fetch_provider", return_value=sample_product()) as fetch:
            first = food_scan.get_product("12345678")
            second = food_scan.get_product("12345678")
        self.assertEqual(fetch.call_count, 1)
        self.assertEqual(first, second)

    def test_missing_product_is_cached_without_fabricating_result(self):
        with patch.object(food_scan, "_fetch_provider", return_value=None) as fetch:
            self.assertIsNone(food_scan.get_product("12345678"))
            self.assertIsNone(food_scan.get_product("12345678"))
            self.assertEqual(fetch.call_count, 1)

    def test_provider_calls_throttled(self):
        with patch.object(food_scan, "_fetch_provider", return_value=None):
            for i in range(food_scan.MAX_PROVIDER_CALLS_PER_MINUTE):
                food_scan.get_product(str(10000000 + i))
            with self.assertRaises(food_scan.ScanRateLimited):
                food_scan.get_product("99999999")


    def test_provider_http_contract_parses_v3_sample_response(self):
        import json
        from io import BytesIO
        from urllib.parse import parse_qs, urlparse

        payload = {"status": "success", "product": sample_product()}
        with patch.object(food_scan, "urlopen", return_value=BytesIO(json.dumps(payload).encode())) as transport:
            result = food_scan._fetch_provider("3017620422003")
        self.assertEqual(result["product_name"], "Plain test yogurt")
        sent_request = transport.call_args.args[0]
        parsed = urlparse(sent_request.full_url)
        self.assertEqual(parsed.scheme, "https")
        self.assertEqual(parsed.netloc, "world.openfoodfacts.org")
        self.assertEqual(parsed.path, "/api/v3/product/3017620422003")
        params = parse_qs(parsed.query)
        self.assertEqual(params["product_type"], ["food"])
        self.assertIn("nutriscore_grade", params["fields"][0])
        self.assertIn("data_quality_errors_tags", params["fields"][0])
        self.assertIn("DelphiaFit/", sent_request.get_header("User-agent"))
        self.assertEqual(transport.call_args.kwargs["timeout"], 6)

    def test_provider_not_found_and_failed_body_do_not_invent_product(self):
        import json
        from io import BytesIO
        from urllib.error import HTTPError
        error = HTTPError("https://world.openfoodfacts.org/api/v3/product/12345678", 404, "Not found", {}, None)
        with patch.object(food_scan, "urlopen", side_effect=error):
            self.assertIsNone(food_scan._fetch_provider("12345678"))
        with patch.object(food_scan, "urlopen", return_value=BytesIO(json.dumps({
            "status": "failure", "product": sample_product()
        }).encode())):
            self.assertIsNone(food_scan._fetch_provider("12345678"))

    def test_provider_timeout_and_oversized_payload_fail_closed(self):
        from io import BytesIO
        from urllib.error import URLError
        with patch.object(food_scan, "urlopen", side_effect=URLError("network outage")):
            with self.assertRaises(food_scan.ScanProviderUnavailable):
                food_scan._fetch_provider("12345678")
        with patch.object(food_scan, "urlopen", return_value=BytesIO(b"X" * (256 * 1024 + 1))):
            with self.assertRaises(food_scan.ScanProviderUnavailable):
                food_scan._fetch_provider("12345678")


if __name__ == "__main__":
    unittest.main()
