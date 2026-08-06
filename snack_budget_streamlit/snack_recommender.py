"""프리미엄 교육용 다과 추천 엔진.

고정 운영 기준
- 1인 1일 예산 상한: 10,000원
- 다과: 1인 1일 평균 3개, 전체 수량에 10% 여유
- 다과 후보 풀: 1일 8종, 2일 10종, 3일 12종, 4일 14종, 5일 16종
- 음료: 생수/커피/기타 음료를 독립 체크박스로 중복 선택
- 커피: 개당 추정가가 최소 1,000원 이상인 브랜드 완제품만 사용
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
from itertools import product
from math import ceil, floor
from typing import Iterable, Sequence
from urllib.parse import quote_plus

from catalog import (
    DRINK_OPTIONS,
    PARTICIPANT_PROFILES,
    PRODUCTS,
    PROFILE_PRIORITIES,
    PackOption,
    Product,
)

DAILY_BUDGET = 10_000
SNACKS_PER_PERSON_DAY = 3
SNACK_SPARE_RATE = 10
PRICE_ERROR_RATE = 0.15
COUPANG_HOME_URL = "https://www.coupang.com/"


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
    premium_label: str


@dataclass(frozen=True)
class PoolItem:
    rank: int
    product_key: str
    product_name: str
    premium_label: str
    reference_unit_price: int
    search_keyword: str
    search_url: str
    reason: str


@dataclass(frozen=True)
class DailyPlan:
    day: int
    snack_names: tuple[str, ...]
    snack_units: int
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
    drink_options: tuple[str, ...]
    participant_profile: str
    snack_pool_size: int
    snack_pool: tuple[PoolItem, ...]
    snacks_per_person_day: int
    snack_spare_rate: int
    rows: tuple[RecommendationRow, ...]
    daily_plans: tuple[DailyPlan, ...]
    snack_total: int
    drink_total: int
    estimated_total: int
    low_total: int
    high_total: int
    reserve: int
    budget_usage_rate: float
    warnings: tuple[str, ...]

    @property
    def drink_summary(self) -> str:
        return ", ".join(self.drink_options) if self.drink_options else "음료 선택 없음"


def round_hundred(value: float) -> int:
    return max(0, int(round(value / 100.0) * 100))


def coupang_search_url(keyword: str) -> str:
    return f"https://www.coupang.com/np/search?q={quote_plus(keyword)}"


@lru_cache(maxsize=None)
def choose_pack_mix(target_units: int, options: tuple[PackOption, ...]) -> tuple[int, int, str]:
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
    service_days: Iterable[int],
) -> RecommendationRow:
    product_info: Product = PRODUCTS[product_key]
    purchased_units, amount, pack_description = choose_pack_mix(
        target_units=target_units,
        options=product_info.pack_options,
    )
    unit_price = round(amount / purchased_units) if purchased_units else 0
    return RecommendationRow(
        category=product_info.category,
        product_key=product_info.key,
        product_name=product_info.name,
        target_units=target_units,
        purchased_units=purchased_units,
        pack_description=pack_description,
        estimated_unit_price=unit_price,
        estimated_amount=amount,
        low_amount=round_hundred(amount * (1 - PRICE_ERROR_RATE)),
        high_amount=round_hundred(amount * (1 + PRICE_ERROR_RATE)),
        reason=product_info.reason,
        service_days=tuple(sorted(set(service_days))),
        search_keyword=product_info.search_keyword,
        search_url=coupang_search_url(product_info.search_keyword),
        premium_label=product_info.premium_label,
    )


def snack_pool_size_for_days(education_days: int) -> int:
    """사용자가 제시한 예시(1일 8, 2일 10, 3일 12)를 그대로 일반화."""
    return min(16, 6 + 2 * education_days)


def _pool_items(profile: str, education_days: int) -> tuple[PoolItem, ...]:
    pool_size = snack_pool_size_for_days(education_days)
    keys = PROFILE_PRIORITIES[profile][:pool_size]
    return tuple(
        PoolItem(
            rank=index,
            product_key=key,
            product_name=PRODUCTS[key].name,
            premium_label=PRODUCTS[key].premium_label,
            reference_unit_price=PRODUCTS[key].reference_unit_price,
            search_keyword=PRODUCTS[key].search_keyword,
            search_url=coupang_search_url(PRODUCTS[key].search_keyword),
            reason=PRODUCTS[key].reason,
        )
        for index, key in enumerate(keys, start=1)
    )


def _daily_snack_units(headcount: int) -> int:
    base_units = headcount * SNACKS_PER_PERSON_DAY
    # 소수 인원에서 10%를 올림하면 1명도 4개가 되어 예산이 왜곡되므로,
    # 전체 수량 기준으로 10%를 내림 누적합니다.
    return base_units + floor(base_units * SNACK_SPARE_RATE / 100)


def _allocate_daily_units(keys: Sequence[str], total_units: int, day: int) -> dict[str, int]:
    base, remainder = divmod(total_units, len(keys))
    quantities = [base] * len(keys)
    for offset in range(remainder):
        quantities[(day - 1 + offset) % len(keys)] += 1
    return dict(zip(keys, quantities))


def _rotation_from_order(
    order: Sequence[str],
    education_days: int,
    offset: int = 0,
) -> tuple[tuple[str, ...], ...]:
    if len(order) < SNACKS_PER_PERSON_DAY:
        raise RuntimeError("다과 후보 풀이 부족합니다.")

    schedules: list[tuple[str, ...]] = []
    for day_index in range(education_days):
        start = (offset + day_index * SNACKS_PER_PERSON_DAY) % len(order)
        chosen: list[str] = []
        cursor = 0
        while len(chosen) < SNACKS_PER_PERSON_DAY:
            key = order[(start + cursor) % len(order)]
            if key not in chosen:
                chosen.append(key)
            cursor += 1
        schedules.append(tuple(chosen))
    return tuple(schedules)


def _snack_schedule_candidates(
    pool_keys: Sequence[str],
    education_days: int,
) -> tuple[tuple[tuple[str, ...], ...], ...]:
    price_asc = sorted(pool_keys, key=lambda key: PRODUCTS[key].reference_unit_price)
    price_desc = list(reversed(price_asc))
    profile_order = list(pool_keys)

    midpoint = sorted(
        pool_keys,
        key=lambda key: abs(PRODUCTS[key].reference_unit_price - 1_900),
    )

    candidates: list[tuple[tuple[str, ...], ...]] = []
    seen: set[tuple[tuple[str, ...], ...]] = set()

    # 전체 후보 풀은 8/10/12/14/16종으로 유지하되,
    # 실제 일자별 제공 조합은 가격대별 상위/중간/하위 부분집합도 함께 탐색합니다.
    # 음료가 적으면 상위 프리미엄 품목을 다른 조합으로 재등장시켜 예산을 적극 활용하고,
    # 음료가 많으면 비교적 가벼운 프리미엄 품목으로 10,000원 상한을 지킵니다.
    minimum_subset = min(len(pool_keys), max(3, education_days + 2))
    maximum_subset = min(len(pool_keys), max(minimum_subset, 10))

    for full_order in (profile_order, price_asc, price_desc, midpoint):
        subset_sizes = list(range(minimum_subset, maximum_subset + 1))
        if len(full_order) not in subset_sizes:
            subset_sizes.append(len(full_order))

        for subset_size in subset_sizes:
            order = full_order[:subset_size]
            for offset in range(min(len(order), 8)):
                schedule = _rotation_from_order(order, education_days, offset)
                if schedule not in seen:
                    seen.add(schedule)
                    candidates.append(schedule)
    return tuple(candidates)


def _rows_from_snack_schedule(
    schedule: Sequence[Sequence[str]],
    headcount: int,
) -> tuple[list[RecommendationRow], list[dict[str, int]]]:
    daily_total = _daily_snack_units(headcount)
    quantities_by_product: dict[str, int] = defaultdict(int)
    days_by_product: dict[str, list[int]] = defaultdict(list)
    daily_allocations: list[dict[str, int]] = []

    for day, keys in enumerate(schedule, start=1):
        allocation = _allocate_daily_units(keys, daily_total, day)
        daily_allocations.append(allocation)
        for key, quantity in allocation.items():
            quantities_by_product[key] += quantity
            days_by_product[key].append(day)

    rows = [
        make_row(
            product_key=key,
            target_units=quantities_by_product[key],
            service_days=days_by_product[key],
        )
        for key in quantities_by_product
    ]
    return rows, daily_allocations


def _drink_rotation(
    keys: Sequence[str],
    education_days: int,
) -> tuple[str, ...]:
    return tuple(keys[day % len(keys)] for day in range(education_days))


def _drink_plan_variants(
    drink_options: tuple[str, ...],
    education_days: int,
) -> tuple[tuple[tuple[str, ...], ...], ...]:
    if not drink_options:
        return (tuple(tuple() for _ in range(education_days)),)

    coffee_variants: tuple[tuple[str, ...], ...] = (
        ("coffee_starbucks",),
        ("coffee_starbucks", "coffee_cantata"),
        ("coffee_cantata",),
        ("coffee_cantata", "coffee_top"),
        ("coffee_top",),
    )
    other_variants: tuple[tuple[str, ...], ...] = (
        ("other_imreal",),
        ("other_imreal", "other_teazle"),
        ("other_teazle",),
        ("other_teazle", "other_barley"),
        ("other_barley",),
    )

    coffee_choices = coffee_variants if "커피 포함" in drink_options else (tuple(),)
    other_choices = other_variants if "그 외 음료 포함" in drink_options else (tuple(),)

    plans: list[tuple[tuple[str, ...], ...]] = []
    for coffee_keys, other_keys in product(coffee_choices, other_choices):
        coffee_rotation = (
            _drink_rotation(coffee_keys, education_days) if coffee_keys else tuple("" for _ in range(education_days))
        )
        other_rotation = (
            _drink_rotation(other_keys, education_days) if other_keys else tuple("" for _ in range(education_days))
        )

        daily: list[tuple[str, ...]] = []
        for day_index in range(education_days):
            keys: list[str] = []
            if "생수 포함" in drink_options:
                keys.append("water_samdasoo")
            if coffee_rotation[day_index]:
                keys.append(coffee_rotation[day_index])
            if other_rotation[day_index]:
                keys.append(other_rotation[day_index])
            daily.append(tuple(keys))
        plans.append(tuple(daily))
    return tuple(dict.fromkeys(plans))


def _rows_from_drink_schedule(
    schedule: Sequence[Sequence[str]],
    headcount: int,
) -> list[RecommendationRow]:
    quantities_by_product: dict[str, int] = defaultdict(int)
    days_by_product: dict[str, list[int]] = defaultdict(list)
    for day, keys in enumerate(schedule, start=1):
        for key in keys:
            quantities_by_product[key] += headcount
            days_by_product[key].append(day)

    return [
        make_row(
            product_key=key,
            target_units=quantity,
            service_days=days_by_product[key],
        )
        for key, quantity in quantities_by_product.items()
    ]


def _candidate_score(
    total: int,
    budget_cap: int,
    snack_schedule: Sequence[Sequence[str]],
    drink_schedule: Sequence[Sequence[str]],
) -> tuple[float, int, int]:
    # 90% 안팎을 우선하되, 같으면 더 다양한 품목과 스타벅스 포함을 선호합니다.
    target = budget_cap * 0.90
    distance = abs(total - target)
    unique_snacks = len({key for day in snack_schedule for key in day})
    premium_coffee_bonus = int(any("coffee_starbucks" in day for day in drink_schedule))
    return (-distance, unique_snacks, premium_coffee_bonus)


def build_recommendation(
    *,
    headcount: int,
    education_days: int = 1,
    drink_options: Iterable[str] = (),
    participant_profile: str = "둘 다 혼합",
) -> Recommendation:
    if not 1 <= headcount <= 1_000:
        raise ValueError("인원수는 1명 이상 1,000명 이하로 입력해 주세요.")
    if not 1 <= education_days <= 5:
        raise ValueError("교육일수는 1일 이상 5일 이하로 입력해 주세요.")
    if participant_profile not in PARTICIPANT_PROFILES:
        raise ValueError("지원하지 않는 참가자 성향입니다.")

    normalized_drinks = tuple(
        option for option in DRINK_OPTIONS if option in set(drink_options)
    )
    invalid_drinks = set(drink_options) - set(DRINK_OPTIONS)
    if invalid_drinks:
        raise ValueError("지원하지 않는 음료 옵션이 포함되어 있습니다.")

    person_days = headcount * education_days
    budget_cap = person_days * DAILY_BUDGET
    pool_items = _pool_items(participant_profile, education_days)
    pool_keys = tuple(item.product_key for item in pool_items)

    best = None
    best_score = None
    snack_candidates = _snack_schedule_candidates(pool_keys, education_days)
    drink_candidates = _drink_plan_variants(normalized_drinks, education_days)

    for drink_schedule in drink_candidates:
        drink_rows = _rows_from_drink_schedule(drink_schedule, headcount)
        drink_total = sum(row.estimated_amount for row in drink_rows)

        for snack_schedule in snack_candidates:
            snack_rows, daily_allocations = _rows_from_snack_schedule(
                snack_schedule, headcount
            )
            snack_total = sum(row.estimated_amount for row in snack_rows)
            total = drink_total + snack_total
            if total > budget_cap:
                continue

            score = _candidate_score(
                total, budget_cap, snack_schedule, drink_schedule
            )
            if best_score is None or score > best_score:
                best_score = score
                best = (
                    drink_schedule,
                    drink_rows,
                    snack_schedule,
                    snack_rows,
                    daily_allocations,
                )

    if best is None:
        raise RuntimeError(
            "선택한 조건으로 1인 1일 10,000원 상한 안에서 프리미엄 3종 구성을 만들기 어렵습니다."
        )

    (
        drink_schedule,
        drink_rows,
        snack_schedule,
        snack_rows,
        daily_allocations,
    ) = best

    rows = [*drink_rows, *snack_rows]
    daily_plans: list[DailyPlan] = []
    daily_total_units = _daily_snack_units(headcount)

    for day_index in range(education_days):
        snack_keys = snack_schedule[day_index]
        drink_keys = drink_schedule[day_index]
        allocation = daily_allocations[day_index]
        allocation_text = ", ".join(
            f"{PRODUCTS[key].name} {allocation[key]}개" for key in snack_keys
        )
        daily_plans.append(
            DailyPlan(
                day=day_index + 1,
                snack_names=tuple(PRODUCTS[key].name for key in snack_keys),
                snack_units=daily_total_units,
                drink_names=tuple(PRODUCTS[key].name for key in drink_keys),
                distribution_note=(
                    f"다과 총 {daily_total_units}개(1인 평균 3개 + 전체 10% 여유) · "
                    f"{allocation_text}"
                ),
            )
        )

    snack_total = sum(row.estimated_amount for row in snack_rows)
    drink_total = sum(row.estimated_amount for row in drink_rows)
    estimated_total = snack_total + drink_total
    low_total = sum(row.low_amount for row in rows)
    high_total = sum(row.high_amount for row in rows)
    reserve = budget_cap - estimated_total
    budget_usage_rate = estimated_total / budget_cap if budget_cap else 0.0

    warnings: list[str] = []
    if high_total > budget_cap:
        warnings.append(
            "가격이 오차범위 상단까지 상승하면 총예산을 넘을 수 있습니다. 결제 전 쿠팡 실판매가를 확인하세요."
        )
    if budget_usage_rate < 0.72:
        warnings.append(
            "선택한 음료가 적어 예상 사용률이 낮습니다. 다만 매일 프리미엄 다과 3종과 10% 여유 수량은 유지했습니다."
        )
    if headcount < 5:
        warnings.append(
            "소수 인원은 묶음 포장 때문에 남는 수량과 개당 단가가 커질 수 있습니다."
        )
    if education_days >= 3:
        warnings.append(
            "여러 날 운영 시 일자별 박스와 라벨을 미리 나누고 초콜릿·냉장 음료의 보관 온도를 확인하세요."
        )

    if estimated_total > budget_cap:
        raise RuntimeError("추천 결과가 총예산 상한을 초과했습니다.")

    return Recommendation(
        headcount=headcount,
        education_days=education_days,
        person_days=person_days,
        per_person_daily_budget=DAILY_BUDGET,
        cumulative_per_person_cap=education_days * DAILY_BUDGET,
        budget_cap=budget_cap,
        drink_options=normalized_drinks,
        participant_profile=participant_profile,
        snack_pool_size=len(pool_items),
        snack_pool=pool_items,
        snacks_per_person_day=SNACKS_PER_PERSON_DAY,
        snack_spare_rate=SNACK_SPARE_RATE,
        rows=tuple(rows),
        daily_plans=tuple(daily_plans),
        snack_total=snack_total,
        drink_total=drink_total,
        estimated_total=estimated_total,
        low_total=low_total,
        high_total=high_total,
        reserve=reserve,
        budget_usage_rate=budget_usage_rate,
        warnings=tuple(dict.fromkeys(warnings)),
    )


def recommendation_to_markdown(result: Recommendation) -> str:
    lines = [
        "# 프리미엄 교육용 다과 추천서",
        "",
        "## 1. 추천 조건 요약",
        f"- 정확한 인원: {result.headcount}명",
        f"- 교육일수: {result.education_days}일",
        f"- 총 제공 기준: {result.person_days}인일",
        f"- 1인 1일 예산 상한: {result.per_person_daily_budget:,}원",
        f"- 총예산 상한: {result.budget_cap:,}원",
        f"- 음료 선택: {result.drink_summary}",
        f"- 참가자 성향: {result.participant_profile}",
        f"- 프리미엄 다과 후보 풀: {result.snack_pool_size}종",
        f"- 제공 기준: 1인 1일 평균 {result.snacks_per_person_day}개, 전체 {result.snack_spare_rate}% 여유",
        "- 모든 다과는 개별포장 또는 소포장 상품 검색을 전제로 합니다.",
        "",
        "## 2. 프리미엄 다과 후보 풀",
        "| 순위 | 후보 품목 | 구분 | 기준 개당 추정가 | 쿠팡 검색 |",
        "|---:|---|---|---:|---|",
    ]
    for item in result.snack_pool:
        lines.append(
            f"| {item.rank} | {item.product_name} | {item.premium_label} | "
            f"{item.reference_unit_price:,}원 | {item.search_url} |"
        )

    lines += [
        "",
        "## 3. 일자별 운영안",
        "| 교육일 | 다과 3종 | 음료 | 배포 기준 |",
        "|---:|---|---|---|",
    ]
    for plan in result.daily_plans:
        drinks = ", ".join(plan.drink_names) or "음료 없음"
        lines.append(
            f"| {plan.day}일차 | {', '.join(plan.snack_names)} | {drinks} | {plan.distribution_note} |"
        )

    lines += [
        "",
        "## 4. 예산 배분",
        f"- 음료 예상 예산: {result.drink_total:,}원",
        f"- 다과 예상 예산: {result.snack_total:,}원",
        f"- 전체 예상 합계: {result.estimated_total:,}원",
        f"- 예비 예산: {result.reserve:,}원",
        f"- 예산 사용률: {result.budget_usage_rate:.1%}",
        f"- 가격 오차범위: {result.low_total:,}~{result.high_total:,}원",
        "",
        "## 5. 최종 구매 구성",
        "| 항목 | 추천 품목 | 제공일 | 목표 수량 | 구매 수량 | 예상 단가 | 예상 금액 | 쿠팡 검색 |",
        "|---|---|---|---:|---:|---:|---:|---|",
    ]
    for row in result.rows:
        days = ", ".join(f"{day}일차" for day in row.service_days)
        lines.append(
            f"| {row.category} | {row.product_name} | {days} | {row.target_units}개 | "
            f"{row.purchased_units}개 ({row.pack_description}) | {row.estimated_unit_price:,}원 | "
            f"{row.estimated_amount:,}원 | {row.search_url} |"
        )

    lines += [
        "",
        "## 6. 구매 확인사항",
        "- 다과가 실제로 낱개포장 또는 개별포장인지 확인",
        "- 커피가 완제품 병/PET/캔이며 개당 1,000원 이상인지 확인",
        "- 쿠팡의 실제 입수량과 앱의 묶음 추정치가 같은지 확인",
        "- 로켓배송 또는 행사 전 도착 예정일 확인",
        "- 냉장 음료와 초콜릿류 보관 온도 확인",
        "- 유통기한과 일자별 분배 박스 확인",
        "",
        f"- 쿠팡 홈: {COUPANG_HOME_URL}",
        "",
        "> 가격은 계산용 추정치이며 쿠팡의 실시간 가격·재고를 보장하지 않습니다.",
    ]
    if result.warnings:
        lines += ["", "## 주의사항"]
        lines += [f"- {warning}" for warning in result.warnings]
    return "\n".join(lines)
