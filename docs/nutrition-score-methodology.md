# DelphiaFit nutrition profile — scoring specification v1.0

**Status:** Source-based production display index. This is not an independent
clinical validation of food health effects or of community-sourced product data.

## Source and provenance

DelphiaFit retrieves the product's **Nutri-Score letter grade (A–E)** from the
Open Food Facts API and displays it alongside a discrete 0–100 index. Nutri-Score
is a recognized front-of-package nutrition-profiling system. Its calculation
has evolved, including an update in 2023. DelphiaFit does **not** attempt to
calculate or reinterpret the official grade from nutrients. The particular
calculation revision used for each Open Food Facts product record is not
independently verified.

Nutri-Score official reference:
https://www.santepubliquefrance.fr/en/nutrition-and-physical-activity/nutri-score

Open Food Facts product API:
https://openfoodfacts.github.io/documentation/docs/Product-Opener/api/

## 0–100 conversion

| Provider-reported Nutri-Score | DelphiaFit grade index |
|:--:|--:|
| A | 90 |
| B | 70 |
| C | 50 |
| D | 30 |
| E | 10 |

This index is a transparent **five-band display conversion** of a source grade.
It does not yield 101 independent outcome categories, and it is not a validated
measure of disease risk, overall food safety, or expected fitness performance.
Do not use the term **percent healthy**, claim a food is **100% safe**, or compare
the numerical difference between grades as if it were a continuous medical
metric. Food categories and serving sizes still matter.

## Eligibility

The app displays a numerical index only when:
1. Open Food Facts reports one of the five supported grade letters.
2. Essential per-100 g / 100 ml composition values pass basic checks: energy
   (kcal), sugar (g), saturated fat (g), and sodium (mg).
3. Open Food Facts has not flagged the record with a data-quality error.
4. The record is not explicitly marked as having no nutrition data.

Otherwise the product is **Unrated**, and the response identifies why. Product
data completeness is shown separately. Missing optional nutrients remain
unknown, not zero.

The app still shows the source grade when one exists but explains when the
numeric index has been withheld.

## Boundaries and safety

- A nutritional composition grade is not an allergen screen. Always verify
  ingredients, allergen warnings, and package labeling.
- Additives and ingredients are presented as source data; this index does not
  determine whether an additive is harmful.
- Products without an eligible grade remain unrated even if their macronutrients
  are complete. Do not fall back to a guessed score.
- A logged food portion is separate from a lookup or grade. A user must
  explicitly choose to log consumption; amount and unit are required.
- Provider data are community-contributed and may be incorrect. Preserve
  Open Food Facts source attribution and ODbL conditions.
- This mapping is versioned as **1.0**. Future scoring changes must create a
  new version and regression tests, rather than silently altering the values.

## Release regression expectations

- A through E produce exactly the five documented numbers.
- Invalid, missing, or inapplicable grades yield an Unrated index.
- Missing / unrealistic core composition values yield Unrated.
- Provider-flagged data-quality errors yield Unrated.
- A prior experimental score response is **not** shown as a production score.
- Existing ingredient, allergen, scan-history, explicit nutrition logging,
  and camera/manual-entry flows continue to function unchanged.
