from __future__ import annotations

import unittest

from catalog import DRINK_OPTIONS, PARTICIPANT_PROFILES, PackOption, PRODUCTS
from snack_recommender import (
    DAILY_BUDGET,
    SNACKS_PER_PERSON_DAY,
    build_recommendation,
    choose_pack_mix,
    coupang_search_url,
    snack_pool_size_for_days,
)


class PackMixTests(unittest.TestCase):
    def test_pack_mix_meets_target_and_chooses_low_cost(self) -> None:
        quantity, cost, description = choose_pack_mix(
            25,
            (PackOption(1, 600), PackOption(12, 6_000), PackOption(24, 10_000)),
        )
        self.assertGreaterEqual(quantity, 25)
        self.assertEqual(cost, 10_600)
        self.assertIn("24입", description)


class RecommendationTests(unittest.TestCase):
    def test_exact_headcount_is_used(self) -> None:
        result = build_recommendation(headcount=37, education_days=2)
        self.assertEqual(result.headcount, 37)
        self.assertEqual(result.person_days, 74)

    def test_fixed_daily_budget_is_ten_thousand_won(self) -> None:
        result = build_recommendation(headcount=30, education_days=5)
        self.assertEqual(result.per_person_daily_budget, DAILY_BUDGET)
        self.assertEqual(result.cumulative_per_person_cap, 50_000)
        self.assertEqual(result.budget_cap, 1_500_000)

    def test_pool_size_follows_explicit_examples(self) -> None:
        expected = {1: 8, 2: 10, 3: 12, 4: 14, 5: 16}
        for days, size in expected.items():
            self.assertEqual(snack_pool_size_for_days(days), size)
            result = build_recommendation(headcount=30, education_days=days)
            self.assertEqual(result.snack_pool_size, size)

    def test_every_day_has_three_snack_types(self) -> None:
        result = build_recommendation(headcount=30, education_days=5)
        self.assertEqual(result.snacks_per_person_day, SNACKS_PER_PERSON_DAY)
        self.assertTrue(
            all(len(plan.snack_names) == SNACKS_PER_PERSON_DAY for plan in result.daily_plans)
        )

    def test_multi_day_plan_rotates(self) -> None:
        result = build_recommendation(headcount=30, education_days=5)
        combinations = {plan.snack_names for plan in result.daily_plans}
        self.assertGreaterEqual(len(combinations), 4)

    def test_default_starts_with_no_drinks(self) -> None:
        result = build_recommendation(headcount=30, education_days=1)
        self.assertEqual(result.drink_options, ())
        self.assertFalse(any(row.category == "음료" for row in result.rows))

    def test_drink_checkboxes_are_independent_and_combinable(self) -> None:
        result = build_recommendation(
            headcount=30,
            education_days=2,
            drink_options=DRINK_OPTIONS,
        )
        self.assertEqual(result.drink_options, DRINK_OPTIONS)
        drink_keys = {row.product_key for row in result.rows if row.category == "음료"}
        self.assertIn("water_samdasoo", drink_keys)
        self.assertTrue(any(key.startswith("coffee_") for key in drink_keys))
        self.assertTrue(any(key.startswith("other_") for key in drink_keys))

    def test_coffee_is_at_least_one_thousand_won_per_unit(self) -> None:
        result = build_recommendation(
            headcount=40,
            education_days=3,
            drink_options=("커피 포함",),
        )
        coffee_rows = [
            row for row in result.rows if row.product_key.startswith("coffee_")
        ]
        self.assertTrue(coffee_rows)
        self.assertTrue(all(row.estimated_unit_price >= 1_000 for row in coffee_rows))

    def test_all_pool_snacks_are_individually_packed(self) -> None:
        result = build_recommendation(headcount=30, education_days=5)
        self.assertTrue(
            all(PRODUCTS[item.product_key].individually_packed for item in result.snack_pool)
        )

    def test_all_links_are_coupang_search_links(self) -> None:
        result = build_recommendation(
            headcount=30,
            education_days=2,
            drink_options=("생수 포함", "커피 포함"),
        )
        for row in result.rows:
            self.assertTrue(row.search_url.startswith("https://www.coupang.com/np/search?q="))
        for item in result.snack_pool:
            self.assertTrue(item.search_url.startswith("https://www.coupang.com/np/search?q="))

    def test_budget_never_exceeds_cap_across_common_conditions(self) -> None:
        headcounts = (1, 7, 30, 100)
        days_options = (1, 3, 5)
        drink_sets = (
            (),
            ("생수 포함",),
            ("커피 포함",),
            ("그 외 음료 포함",),
            DRINK_OPTIONS,
        )
        for headcount in headcounts:
            for days in days_options:
                for profile in PARTICIPANT_PROFILES:
                    for drinks in drink_sets:
                        result = build_recommendation(
                            headcount=headcount,
                            education_days=days,
                            drink_options=drinks,
                            participant_profile=profile,
                        )
                        self.assertLessEqual(result.estimated_total, result.budget_cap)

    def test_invalid_inputs_raise(self) -> None:
        with self.assertRaises(ValueError):
            build_recommendation(headcount=0)
        with self.assertRaises(ValueError):
            build_recommendation(headcount=30, education_days=6)
        with self.assertRaises(ValueError):
            build_recommendation(headcount=30, drink_options=("탄산만",))

    def test_coupang_url_encodes_keyword(self) -> None:
        url = coupang_search_url("오설록 그린티 랑드샤")
        self.assertIn("q=", url)
        self.assertNotIn(" ", url)


if __name__ == "__main__":
    unittest.main()
