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
        self.assertEqual(result["score_status"], "experimental")
        self.assertIn("not clinically validated", result["score_methodology"]["limits"])
        self.assertIn("ODbL", result["source"]["license"])

    def test_never_invents_missing_nutrition_facts_or_scores(self):
        product = sample_product()
        product["nutriments"].pop("fiber_100g")
        result = food_scan.normalize_product("12345678", product)
        self.assertIsNone(result["nutrition_per_100g_or_100ml"]["fiber_g"])
        self.assertIsNone(result["delphiafit_score_0_100"])
        self.assertEqual(result["score_status"], "unrated")
        self.assertIn("fiber_g", result["missing_score_nutrients"])

    def test_impossible_values_are_unrated_and_invalid_images_excluded(self):
        product = sample_product()
        product["nutriments"]["proteins_100g"] = 900
        product["image_front_url"] = "https://example.org/tracker.png"
        result = food_scan.normalize_product("12345678", product)
        self.assertIsNone(result["delphiafit_score_0_100"])
        self.assertIsNone(result["image_url"])
        self.assertIn("protein_g", result["missing_score_nutrients"])

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


if __name__ == "__main__":
    unittest.main()
