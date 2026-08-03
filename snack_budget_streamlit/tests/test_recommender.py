import unittest

from snack_recommender import AGE_GROUPS, BEVERAGE_MODES, build_recommendation


class RecommendationEngineTest(unittest.TestCase):
    def test_all_standard_combinations_stay_within_budget(self):
        for headcount in (1, 5, 10, 20, 30, 50, 80, 100):
            for beverage_mode in BEVERAGE_MODES:
                for age_group in AGE_GROUPS:
                    with self.subTest(
                        headcount=headcount,
                        beverage_mode=beverage_mode,
                        age_group=age_group,
                    ):
                        result = build_recommendation(
                            headcount=headcount,
                            beverage_mode=beverage_mode,
                            age_group=age_group,
                            per_person_budget=5_000,
                            spare_rate=15,
                            duration="2~4시간",
                        )
                        self.assertLessEqual(result.estimated_total, result.budget_cap)
                        self.assertTrue(result.rows)
                        self.assertTrue(all(row.search_url.startswith("https://www.coupang.com/np/search?q=") for row in result.rows))

    def test_no_drink_mode_has_no_drink_rows(self):
        result = build_recommendation(
            headcount=30,
            beverage_mode="음료 제외",
            age_group="연령대 혼합",
        )
        self.assertTrue(all(row.category == "다과" for row in result.rows))

    def test_water_mode_contains_water(self):
        result = build_recommendation(
            headcount=30,
            beverage_mode="생수만 포함",
            age_group="연령대 혼합",
        )
        self.assertIn("water", {row.product_key for row in result.rows})

    def test_snack_quantity_has_spare(self):
        result = build_recommendation(
            headcount=30,
            beverage_mode="음료 제외",
            age_group="연령대 혼합",
            spare_rate=20,
        )
        snack_rows = [row for row in result.rows if row.category == "다과"]
        self.assertTrue(snack_rows)
        self.assertTrue(all(row.purchased_units >= 36 for row in snack_rows))


if __name__ == "__main__":
    unittest.main()
