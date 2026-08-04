"""예산 맞춤형 교육용 다과 추천 엔진.

핵심 계산 기준
- 총예산 상한 = 인원수 × 교육일수 × 1인 1일 예산
- 다과 수량 = 일자별 참석 인원에 10~20% 여유분을 더해 합산
- 음료 수량 = 최소 인원수 × 교육일수 기준
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from math import ceil
from typing import Iterable
from urllib.parse import quote_plus

from catalog import (
    AGE_DRINK_PRIORITY,
    AGE_PROFILE_DESCRIPTIONS,
    AGE_SNACK_PRIORITY,
    PRODUCTS,
    TASTE_SNACK_PRIORITY,
    PackOption,
    Product,
)

BEVERAGE_MODES = (
    "음료 포함",
    "음료 제외",
    "생수만 포함",
    "커피 포함",
    "생수 + 커피 + 주스 포함",
)

AGE_GROUPS = tuple(AGE_SNACK_PRIORITY.keys())
TASTE_PROFILES = tuple(TASTE_SNACK_PRIORITY.keys())
HEADCOUNT_RANGES: dict[str, int] = {
    "1~10명": 10,
    "11~20명": 20,
    "21~30명": 30,
    "31~40명": 40,
    "41~50명": 50,
    "51~60명": 60,
    "61~70명": 70,
    "71~80명": 80,
    "81~90명": 90,
    "91~100명": 100,
}


@dataclass(frozen=True)
class RecommendationRow:
    category: str
    product_key: str
    product_name: str
    target_units: int
    purchased_units: int
    pack_description: str
    estimated_unit_price: int
    estimated_amount: int
    low_amount: int
    high_amount: int
    reason: str
    service_days: tuple[int, ...]
    search_keyword: str
    search_url: str


@dataclass(frozen=True)
class DailyPlan:
    day: int
    snack_names: tuple[str, ...]
    drink_names: tuple[str, ...]
    distribution_note: str


@dataclass(frozen=True)
class Recommendation:
    headcount: int
    education_days: int
    person_days: int
    per_person_daily_budget: int
    cumulative_per_person_cap: int
    budget_cap: int
    beverage_mode: str
    age_group: str
    taste_profile: str
    age_profile_description: str
    spare_rate: int
    rows: tuple[RecommendationRow, ...]
    daily_plans: tuple[DailyPlan, ...]
    snack_total: int
    drink_total: int
    estimated_total: int
    low_total: int
    high_total: int
    reserve: int
    warnings: tuple[str, ...]


def round_hundred(value: float) -> int:
    return max(0, int(round(value / 100.0) * 100))


def coupang_search_url(keyword: str) -> str:
    return f"https://www.coupang.com/np/search?q={quote_plus(keyword)}"


def choose_pack_mix(target_units: int, options: Iterable[PackOption]) -> tuple[int, int, str]:
    """목표 수량 이상을 충족하는 최저가 묶음 조합을 찾습니다."""
    if target_units <= 0:
        return 0, 0, ""

    opts = sorted(options, key=lambda item: (item.size, item.price))
    max_size = max(item.size for item in opts)
    search_limit = target_units + (max_size * 2)
    inf = 10**18
    dp: list[tuple[int, int, tuple[int, ...]]] = [
        (inf, inf, tuple(0 for _ in opts)) for _ in range(search_limit + 1)
    ]
    dp[0] = (0, 0, tuple(0 for _ in opts))

    for quantity in range(search_limit + 1):
        current_cost, current_pack_count, current_counts = dp[quantity]
        if current_cost == inf:
            continue
        for index, option in enumerate(opts):
            next_quantity = min(search_limit, quantity + option.size)
            next_counts = list(current_counts)
            next_counts[index] += 1
            candidate = (
                current_cost + option.price,
                current_pack_count + 1,
                tuple(next_counts),
            )
            if candidate[:2] < dp[next_quantity][:2]:
                dp[next_quantity] = candidate

    best_quantity = min(
        range(target_units, search_limit + 1),
        key=lambda quantity: (dp[quantity][0], quantity - target_units, dp[quantity][1]),
    )
    best_cost, _, counts = dp[best_quantity]
    parts = [
        f"{option.size}입 × {count}개"
        for option, count in zip(opts, counts)
        if count
    ]
    return best_quantity, best_cost, " + ".join(parts)


def make_row(
    product_key: str,
    target_units: int,
    price_error_rate: float,
    service_days: Iterable[int],
) -> RecommendationRow:
    product: Product = PRODUCTS[product_key]
    purchased_units, amount, pack_description = choose_pack_mix(
        target_units=target_units,
        options=product.pack_options,
    )
    unit_price = round(amount / purchased_units) if purchased_units else 0
    return RecommendationRow(
        category=product.category,
        product_key=product.key,
        product_name=product.name,
        target_units=target_units,
        purchased_units=purchased_units,
        pack_description=pack_description,
        estimated_unit_price=unit_price,
        estimated_amount=amount,
        low_amount=round_hundred(amount * (1 - price_error_rate)),
        high_amount=round_hundred(amount * (1 + price_error_rate)),
        reason=product.reason,
        service_days=tuple(sorted(set(service_days))),
        search_keyword=product.search_keyword,
        search_url=coupang_search_url(product.search_keyword),
    )


def _base_drink_plan(person_days: int, beverage_mode: str, age_group: str) -> list[tuple[str, int]]:
    if beverage_mode == "음료 제외":
        return []

    plan: list[tuple[str, int]] = [("water", person_days)]
    primary, secondary = AGE_DRINK_PRIORITY[age_group]

    if beverage_mode == "생수만 포함":
        return plan
    if beverage_mode == "커피 포함":
        coffee_key = "coffee_can" if age_group == "20~30대 중심" else "coffee_bottle"
        plan.append((coffee_key, max(1, ceil(person_days * 0.60))))
        return plan
    if beverage_mode == "생수 + 커피 + 주스 포함":
        coffee_key = "coffee_can" if age_group == "20~30대 중심" else "coffee_bottle"
        plan.append((coffee_key, max(1, ceil(person_days * 0.55))))
        plan.append(("juice", max(1, ceil(person_days * 0.35))))
        return plan

    plan.append((primary, max(1, ceil(person_days * 0.35))))
    plan.append((secondary, max(1, ceil(person_days * 0.15))))
    return plan


def _unique_plans(plans: Iterable[list[tuple[str, int]]]) -> list[list[tuple[str, int]]]:
    seen: set[tuple[tuple[str, int], ...]] = set()
    result: list[list[tuple[str, int]]] = []
    for plan in plans:
        normalized = tuple((key, max(1, int(count))) for key, count in plan)
        if normalized not in seen:
            seen.add(normalized)
            result.append(list(normalized))
    return result


def _drink_plan_candidates(
    person_days: int,
    beverage_mode: str,
    age_group: str,
) -> list[list[tuple[str, int]]]:
    base = _base_drink_plan(person_days, beverage_mode, age_group)
    if not base:
        return [[]]

    substitutions = {
        "coffee_bottle": "coffee_can",
        "tea": "juice",
        "soy_milk": "juice",
    }
    cheaper = [(substitutions.get(key, key), count) for key, count in base]
    water_only = [("water", person_days)]

    plans: list[list[tuple[str, int]]] = [base, cheaper]
    if beverage_mode == "음료 포함":
        primary = cheaper[1][0] if len(cheaper) > 1 else "coffee_can"
        plans.extend([
            [("water", person_days), (primary, max(1, ceil(person_days * 0.25)))],
            water_only,
        ])
    elif beverage_mode == "커피 포함":
        coffee_key = cheaper[1][0]
        plans.extend([
            [("water", person_days), (coffee_key, max(1, ceil(person_days * 0.35)))],
            [("water", person_days), (coffee_key, max(1, ceil(person_days * 0.20)))],
            water_only,
        ])
    elif beverage_mode == "생수 + 커피 + 주스 포함":
        coffee_key = cheaper[1][0]
        plans.extend([
            [
                ("water", person_days),
                (coffee_key, max(1, ceil(person_days * 0.35))),
                ("juice", max(1, ceil(person_days * 0.20))),
            ],
            [("water", person_days), (coffee_key, max(1, ceil(person_days * 0.25)))],
            water_only,
        ])
    else:
        plans.append(water_only)
    return _unique_plans(plans)


def _build_drink_rows(
    *,
    person_days: int,
    education_days: int,
    beverage_mode: str,
    age_group: str,
    budget_cap: int,
    price_error_rate: float,
) -> tuple[list[RecommendationRow], bool]:
    all_days = range(1, education_days + 1)
    candidates = _drink_plan_candidates(person_days, beverage_mode, age_group)

    for index, plan in enumerate(candidates):
        rows = [
            make_row(key, target, price_error_rate, all_days)
            for key, target in plan
        ]
        if sum(row.estimated_amount for row in rows) <= budget_cap:
            return rows, index > 0

    raise RuntimeError("선택한 예산으로 최소 음료 구성을 만들기 어렵습니다.")


def _snack_priority(age_group: str, taste_profile: str) -> tuple[str, ...]:
    if taste_profile == "연령대 추천 자동":
        return AGE_SNACK_PRIORITY[age_group]
    return TASTE_SNACK_PRIORITY[taste_profile]


def _rotation_schedule(
    product_keys: tuple[str, ...],
    education_days: int,
    snacks_per_day: int,
) -> list[tuple[str, ...]]:
    """일자별로 같은 조합이 반복되지 않도록 순환 배치합니다."""
    if not product_keys:
        return [tuple() for _ in range(education_days)]

    starts_for_two = (0, 2, 4, 1, 3)
    starts_for_three = (0, 3, 1, 4, 2)
    starts = starts_for_three if snacks_per_day >= 3 else starts_for_two

    schedule: list[tuple[str, ...]] = []
    for day_index in range(education_days):
        start = starts[day_index % len(starts)] % len(product_keys)
        chosen: list[str] = []
        offset = 0
        while len(chosen) < min(snacks_per_day, len(product_keys)):
            key = product_keys[(start + offset) % len(product_keys)]
            if key not in chosen:
                chosen.append(key)
            offset += 1
        schedule.append(tuple(chosen))
    return schedule


def _build_snack_rows_and_schedule(
    *,
    headcount: int,
    education_days: int,
    beverage_mode: str,
    age_group: str,
    taste_profile: str,
    spare_rate: int,
    available_budget: int,
    safe_available_budget: int,
    price_error_rate: float,
) -> tuple[list[RecommendationRow], list[tuple[str, ...]], bool]:
    priority = _snack_priority(age_group, taste_profile)
    desired_unique = min(len(priority), education_days + 1)
    preferred_per_day = 3 if beverage_mode == "음료 제외" else 2
    target_per_day = ceil(headcount * (1 + spare_rate / 100))

    def build_for(pool_size: int, per_day: int) -> tuple[list[RecommendationRow], list[tuple[str, ...]]]:
        pool = tuple(priority[:pool_size])
        schedule = _rotation_schedule(pool, education_days, per_day)
        days_by_product: dict[str, list[int]] = defaultdict(list)
        for day, keys in enumerate(schedule, start=1):
            for key in keys:
                days_by_product[key].append(day)

        rows: list[RecommendationRow] = []
        for key in pool:
            service_days = days_by_product.get(key, [])
            if not service_days:
                continue
            rows.append(
                make_row(
                    key,
                    target_per_day * len(service_days),
                    price_error_rate,
                    service_days,
                )
            )
        return rows, schedule

    # 먼저 12% 예비비를 남기는 구성을 찾습니다.
    for limit, used_reserve in (
        (safe_available_budget, False),
        (available_budget, True),
    ):
        for per_day in range(preferred_per_day, 0, -1):
            min_pool = max(per_day, 1)
            for pool_size in range(desired_unique, min_pool - 1, -1):
                rows, schedule = build_for(pool_size, per_day)
                if sum(row.estimated_amount for row in rows) <= limit:
                    return rows, schedule, used_reserve or per_day < preferred_per_day

    return [], [tuple() for _ in range(education_days)], True


def build_recommendation(
    *,
    headcount: int,
    education_days: int = 1,
    beverage_mode: str = "음료 포함",
    age_group: str = "연령대 혼합",
    taste_profile: str = "연령대 추천 자동",
    per_person_daily_budget: int = 10_000,
    spare_rate: int = 15,
    price_error_rate: float = 0.15,
) -> Recommendation:
    if not 1 <= headcount <= 100:
        raise ValueError("인원수는 1명 이상 100명 이하로 입력해 주세요.")
    if not 1 <= education_days <= 5:
        raise ValueError("교육일수는 1일 이상 5일 이하로 입력해 주세요.")
    if beverage_mode not in BEVERAGE_MODES:
        raise ValueError("지원하지 않는 음료 구성입니다.")
    if age_group not in AGE_GROUPS:
        raise ValueError("지원하지 않는 연령대입니다.")
    if taste_profile not in TASTE_PROFILES:
        raise ValueError("지원하지 않는 구성 성향입니다.")
    if not 3_500 <= per_person_daily_budget <= 10_000:
        raise ValueError("1인 1일 예산은 3,500원 이상 10,000원 이하로 설정해 주세요.")
    if not 10 <= spare_rate <= 20:
        raise ValueError("여유 수량은 10~20%로 설정해 주세요.")
    if price_error_rate not in {0.10, 0.12, 0.15}:
        raise ValueError("가격 오차범위는 10%, 12%, 15% 중에서 선택해 주세요.")

    person_days = headcount * education_days
    budget_cap = person_days * per_person_daily_budget
    cumulative_per_person_cap = education_days * per_person_daily_budget
    warnings: list[str] = []

    drink_rows, drinks_adjusted = _build_drink_rows(
        person_days=person_days,
        education_days=education_days,
        beverage_mode=beverage_mode,
        age_group=age_group,
        budget_cap=budget_cap,
        price_error_rate=price_error_rate,
    )
    drink_total = sum(row.estimated_amount for row in drink_rows)
    if drinks_adjusted:
        warnings.append(
            "묶음 단가와 총예산을 맞추기 위해 보조 음료의 종류 또는 수량을 더 경제적인 구성으로 조정했습니다."
        )

    available_budget = max(0, budget_cap - drink_total)
    safe_available_budget = max(0, int(budget_cap * 0.88) - drink_total)
    snack_rows, snack_schedule, snack_adjusted = _build_snack_rows_and_schedule(
        headcount=headcount,
        education_days=education_days,
        beverage_mode=beverage_mode,
        age_group=age_group,
        taste_profile=taste_profile,
        spare_rate=spare_rate,
        available_budget=available_budget,
        safe_available_budget=safe_available_budget,
        price_error_rate=price_error_rate,
    )
    if snack_adjusted:
        warnings.append(
            "예산 상한을 지키기 위해 다과 종류 수 또는 일일 제공 품목 수를 기본안보다 줄였습니다."
        )

    rows = [*drink_rows, *snack_rows]
    selected_drink_names = tuple(row.product_name for row in drink_rows)
    selected_snack_keys = {row.product_key for row in snack_rows}
    daily_plans: list[DailyPlan] = []
    for day, planned_keys in enumerate(snack_schedule, start=1):
        snack_names = tuple(
            PRODUCTS[key].name for key in planned_keys if key in selected_snack_keys
        )
        if beverage_mode == "음료 제외":
            drink_names: tuple[str, ...] = tuple()
            note = f"다과별 약 {ceil(headcount * (1 + spare_rate / 100))}개 준비"
        else:
            drink_names = selected_drink_names
            note = (
                f"다과별 약 {ceil(headcount * (1 + spare_rate / 100))}개, "
                f"생수는 {headcount}개/일 기준; 보조 음료는 선택 제공"
            )
        daily_plans.append(
            DailyPlan(
                day=day,
                snack_names=snack_names,
                drink_names=drink_names,
                distribution_note=note,
            )
        )

    snack_total = sum(row.estimated_amount for row in snack_rows)
    estimated_total = snack_total + drink_total
    low_total = sum(row.low_amount for row in rows)
    high_total = sum(row.high_amount for row in rows)
    reserve = max(0, budget_cap - estimated_total)

    if not snack_rows:
        warnings.append(
            "선택한 조건에서는 다과를 추가할 예산이 부족합니다. 음료 구성을 단순화하거나 1인 1일 예산을 높여 주세요."
        )
    if any(len(plan.snack_names) < 2 for plan in daily_plans):
        warnings.append(
            "일부 일자는 예산 또는 포장 단위 때문에 다과가 2종 미만입니다. 실제 판매가를 확인해 추가 구매를 검토해 주세요."
        )
    if high_total > budget_cap:
        warnings.append(
            "가격이 오차범위 상단까지 상승하면 총예산 상한을 넘을 수 있습니다. 결제 전 실제 판매가를 확인해 주세요."
        )
    if headcount < 10:
        warnings.append(
            "10명 미만은 소포장·낱개 구매 비중이 높아 대량 구매보다 단가가 올라갈 수 있습니다."
        )
    if education_days >= 4:
        warnings.append(
            "장기차수는 보관 공간과 일자별 분배 박스를 미리 구분하고, 초콜릿류의 보관 온도를 확인해 주세요."
        )
    if estimated_total > budget_cap:
        raise RuntimeError("추천 결과가 총예산 상한을 초과했습니다.")

    return Recommendation(
        headcount=headcount,
        education_days=education_days,
        person_days=person_days,
        per_person_daily_budget=per_person_daily_budget,
        cumulative_per_person_cap=cumulative_per_person_cap,
        budget_cap=budget_cap,
        beverage_mode=beverage_mode,
        age_group=age_group,
        taste_profile=taste_profile,
        age_profile_description=AGE_PROFILE_DESCRIPTIONS[age_group],
        spare_rate=spare_rate,
        rows=tuple(rows),
        daily_plans=tuple(daily_plans),
        snack_total=snack_total,
        drink_total=drink_total,
        estimated_total=estimated_total,
        low_total=low_total,
        high_total=high_total,
        reserve=reserve,
        warnings=tuple(dict.fromkeys(warnings)),
    )


def recommendation_to_markdown(result: Recommendation) -> str:
    lines = [
        "# 예산 맞춤형 교육용 다과 추천서",
        "",
        "## 1. 추천 조건 요약",
        f"- 기준 인원: {result.headcount}명",
        f"- 교육일수: {result.education_days}일",
        f"- 총 제공 기준: {result.person_days}인일(인원 × 교육일수)",
        f"- 1인 1일 예산 상한: {result.per_person_daily_budget:,}원",
        f"- 1인 누적 예산 상한: {result.cumulative_per_person_cap:,}원",
        f"- 총예산 상한: {result.budget_cap:,}원",
        f"- 음료 포함 여부: {result.beverage_mode}",
        f"- 주 연령대: {result.age_group}",
        f"- 구성 성향: {result.taste_profile}",
        f"- 연령대 추천 설명: {result.age_profile_description}",
        f"- 다과 여유 수량: {result.spare_rate}%",
        "- 추천 방향: 가성비 중심, 대중 과자, 낱개포장 또는 개별포장, 교육용 대량 배포 구성",
        "",
        "## 2. 일자별 운영안",
        "| 교육일 | 다과 구성 | 음료 구성 | 배포 기준 |",
        "|---:|---|---|---|",
    ]
    for plan in result.daily_plans:
        snacks = ", ".join(plan.snack_names) or "다과 없음"
        drinks = ", ".join(plan.drink_names) or "음료 없음"
        lines.append(f"| {plan.day}일차 | {snacks} | {drinks} | {plan.distribution_note} |")

    lines += [
        "",
        "## 3. 예산 배분",
        f"- 음료 예상 예산: {result.drink_total:,}원",
        f"- 다과 예상 예산: {result.snack_total:,}원",
        f"- 예비 예산: {result.reserve:,}원",
        f"- 전체 예상 합계: {result.estimated_total:,}원",
        f"- 가격 오차범위: {result.low_total:,}~{result.high_total:,}원",
        f"- 총예산 초과 여부: {'초과' if result.estimated_total > result.budget_cap else '초과하지 않음'}",
        "",
        "## 4. 최종 구매 구성",
        "| 항목 | 추천 품목 | 제공일 | 목표 수량 | 구매 수량 | 예상 단가 | 예상 금액 | 가격 오차범위 | 추천 이유 |",
        "|---|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in result.rows:
        service_days = ", ".join(f"{day}일차" for day in row.service_days)
        lines.append(
            f"| {row.category} | {row.product_name} | {service_days} | "
            f"{row.target_units}개 | {row.purchased_units}개 ({row.pack_description}) | "
            f"{row.estimated_unit_price:,}원/개 | {row.estimated_amount:,}원 | "
            f"{row.low_amount:,}~{row.high_amount:,}원 | {row.reason} |"
        )

    lines += ["", "## 5. 쿠팡 검색 키워드 및 링크"]
    for row in result.rows:
        lines += [
            f"- 검색어: {row.search_keyword}",
            f"- 쿠팡 검색 링크: {row.search_url}",
        ]

    lines += [
        "",
        "## 6. 구매 시 확인사항",
        "- 낱개포장 또는 개별포장 여부 확인",
        "- 일자별 다과 수량이 참석 인원보다 10~20% 많은지 확인",
        "- 총 구매 금액이 인원수 × 교육일수 × 1인 1일 예산을 넘지 않는지 확인",
        "- 로켓배송 또는 도착 예정일 확인",
        "- 유통기한과 장기차수 보관 가능 기간 확인",
        "- 상품 리뷰에서 파손, 녹음, 부스러기, 포장 상태 확인",
        "- 초콜릿류는 여름철 보관 온도 확인",
        "- 음료 포함 시 냉장 보관 필요 여부 확인",
        "- 교육 장소의 보관 공간과 일자별 분배 방법 확인",
        "- 고급 디저트 위주로 담겨 단가가 올라가지 않았는지 확인",
        "",
        "> 안내: 가격은 계산용 추정치이며 쿠팡의 실시간 가격·재고와 다를 수 있습니다. "
        "이 서비스는 자동결제, 로그인, 장바구니 담기 또는 주문 대행을 하지 않습니다.",
    ]
    if result.warnings:
        lines += ["", "## 주의사항"]
        lines += [f"- {warning}" for warning in result.warnings]

    return "\n".join(lines)
