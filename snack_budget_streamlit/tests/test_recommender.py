from __future__ import annotations

import unittest

from catalog import AGE_PROFILE_DESCRIPTIONS
from snack_recommender import (
    build_recommendation,
    choose_pack_mix,
    coupang_search_url,
)
from catalog import PackOption


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
    def test_budget_cap_uses_headcount_days_and_daily_budget(self) -> None:
        result = build_recommendation(
            headcount=30,
            education_days=5,
            per_person_daily_budget=10_000,
        )
        self.assertEqual(result.person_days, 150)
        self.assertEqual(result.cumulative_per_person_cap, 50_000)
        self.assertEqual(result.budget_cap, 1_500_000)
        self.assertLessEqual(result.estimated_total, result.budget_cap)


    def test_default_daily_budget_is_ten_thousand_won(self) -> None:
        result = build_recommendation(headcount=30, education_days=5)
        self.assertEqual(result.per_person_daily_budget, 10_000)
        self.assertEqual(result.cumulative_per_person_cap, 50_000)
        self.assertEqual(result.budget_cap, 1_500_000)

    def test_budget_above_daily_cap_raises_error(self) -> None:
        with self.assertRaises(ValueError):
            build_recommendation(
                headcount=30,
                education_days=1,
                per_person_daily_budget=10_100,
            )

    def test_daily_plan_count_matches_days(self) -> None:
        result = build_recommendation(headcount=20, education_days=4)
        self.assertEqual(len(result.daily_plans), 4)
        self.assertTrue(all(plan.day >= 1 for plan in result.daily_plans))

    def test_five_day_plan_rotates_snacks(self) -> None:
        result = build_recommendation(headcount=30, education_days=5)
        combinations = {plan.snack_names for plan in result.daily_plans}
        self.assertGreaterEqual(len(combinations), 3)

    def test_default_plan_has_at_least_two_snacks_per_day(self) -> None:
        result = build_recommendation(headcount=30, education_days=3)
        self.assertTrue(all(len(plan.snack_names) >= 2 for plan in result.daily_plans))

    def test_beverage_excluded_has_no_drink_rows(self) -> None:
        result = build_recommendation(
            headcount=30,
            education_days=2,
            beverage_mode="음료 제외",
        )
        self.assertEqual(result.drink_total, 0)
        self.assertTrue(all(row.category != "음료" for row in result.rows))
        self.assertTrue(all(not plan.drink_names for plan in result.daily_plans))

    def test_urls_are_coupang_search_links(self) -> None:
        result = build_recommendation(headcount=15, education_days=2)
        self.assertGreaterEqual(len(result.rows), 3)
        self.assertTrue(all(row.search_url.startswith("https://www.coupang.com/np/search?q=") for row in result.rows))
        self.assertIn("+", coupang_search_url("생수 500ml 대량"))

    def test_age_descriptions_are_distinct(self) -> None:
        self.assertNotEqual(
            AGE_PROFILE_DESCRIPTIONS["20~30대 중심"],
            AGE_PROFILE_DESCRIPTIONS["40~50대 중심"],
        )

    def test_invalid_days_raise_error(self) -> None:
        with self.assertRaises(ValueError):
            build_recommendation(headcount=30, education_days=0)
        with self.assertRaises(ValueError):
            build_recommendation(headcount=30, education_days=6)

    def test_low_budget_still_respects_cap(self) -> None:
        result = build_recommendation(
            headcount=10,
            education_days=5,
            beverage_mode="생수 + 커피 + 주스 포함",
            per_person_daily_budget=3_500,
        )
        self.assertLessEqual(result.estimated_total, result.budget_cap)

    def test_markdown_and_service_days_are_consistent(self) -> None:
        result = build_recommendation(headcount=30, education_days=3)
        valid_days = set(range(1, 4))
        for row in result.rows:
            self.assertTrue(set(row.service_days).issubset(valid_days))


if __name__ == "__main__":
    unittest.main()
