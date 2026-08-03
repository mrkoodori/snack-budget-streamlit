"""예산 맞춤형 교육용 다과 추천 엔진."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Iterable
from urllib.parse import quote_plus

from catalog import AGE_DRINK_PRIORITY, AGE_SNACK_PRIORITY, PRODUCTS, PackOption, Product

BEVERAGE_MODES = (
    "음료 포함",
    "음료 제외",
    "생수만 포함",
    "커피 포함",
    "생수 + 커피 + 주스 포함",
)

AGE_GROUPS = tuple(AGE_SNACK_PRIORITY.keys())

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
    search_keyword: str
    search_url: str


@dataclass(frozen=True)
class Recommendation:
    headcount: int
    per_person_budget: int
    budget_cap: int
    beverage_mode: str
    age_group: str
    spare_rate: int
    duration: str
    rows: tuple[RecommendationRow, ...]
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

    # 수량별 (가격, 총 묶음 수, 각 옵션 사용 개수)
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


def make_row(product_key: str, target_units: int, price_error_rate: float) -> RecommendationRow:
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
        search_keyword=product.search_keyword,
        search_url=coupang_search_url(product.search_keyword),
    )


def _drink_plan(
    headcount: int,
    beverage_mode: str,
    age_group: str,
    duration: str,
) -> list[tuple[str, int]]:
    if beverage_mode == "음료 제외":
        return []

    duration_multiplier = {
        "2시간 이하": 1.0,
        "2~4시간": 1.0,
        "4시간 초과": 1.2,
    }[duration]

    plan: list[tuple[str, int]] = [("water", ceil(headcount * duration_multiplier))]
    primary, secondary = AGE_DRINK_PRIORITY[age_group]

    if beverage_mode == "생수만 포함":
        return plan

    if beverage_mode == "커피 포함":
        coffee_key = "coffee_can" if age_group == "20~30대 중심" else "coffee_bottle"
        plan.append((coffee_key, max(1, ceil(headcount * 0.60 * duration_multiplier))))
        return plan

    if beverage_mode == "생수 + 커피 + 주스 포함":
        coffee_key = "coffee_can" if age_group == "20~30대 중심" else "coffee_bottle"
        plan.append((coffee_key, max(1, ceil(headcount * 0.55 * duration_multiplier))))
        plan.append(("juice", max(1, ceil(headcount * 0.35 * duration_multiplier))))
        return plan

    # 기본 '음료 포함': 연령대에 맞춘 보조 음료를 섞되 생수는 전원분 확보
    plan.append((primary, max(1, ceil(headcount * 0.35 * duration_multiplier))))
    plan.append((secondary, max(1, ceil(headcount * 0.15 * duration_multiplier))))
    return plan


def build_recommendation(
    *,
    headcount: int,
    beverage_mode: str = "음료 포함",
    age_group: str = "연령대 혼합",
    per_person_budget: int = 5_000,
    spare_rate: int = 15,
    duration: str = "2~4시간",
    price_error_rate: float = 0.15,
) -> Recommendation:
    if not 1 <= headcount <= 100:
        raise ValueError("인원수는 1명 이상 100명 이하로 입력해 주세요.")
    if beverage_mode not in BEVERAGE_MODES:
        raise ValueError("지원하지 않는 음료 구성입니다.")
    if age_group not in AGE_GROUPS:
        raise ValueError("지원하지 않는 연령대입니다.")
    if not 3_500 <= per_person_budget <= 5_000:
        raise ValueError("1인 예산은 3,500원 이상 5,000원 이하로 설정해 주세요.")
    if not 10 <= spare_rate <= 20:
        raise ValueError("여유 수량은 10~20%로 설정해 주세요.")
    if duration not in {"2시간 이하", "2~4시간", "4시간 초과"}:
        raise ValueError("지원하지 않는 교육 시간입니다.")

    budget_cap = headcount * per_person_budget
    warnings: list[str] = []
    rows: list[RecommendationRow] = []

    # 음료를 먼저 확보합니다.
    drink_plan = _drink_plan(
        headcount=headcount,
        beverage_mode=beverage_mode,
        age_group=age_group,
        duration=duration,
    )

    def build_drink_rows(plan: list[tuple[str, int]]) -> list[RecommendationRow]:
        return [
            make_row(product_key, target_units, price_error_rate)
            for product_key, target_units in plan
        ]

    drink_rows = build_drink_rows(drink_plan)

    # 장시간 옵션 또는 소규모 묶음 구매로 음료만 예산을 넘으면 최소 인원분으로 조정합니다.
    if sum(row.estimated_amount for row in drink_rows) > budget_cap and duration == "4시간 초과":
        drink_plan = _drink_plan(
            headcount=headcount,
            beverage_mode=beverage_mode,
            age_group=age_group,
            duration="2~4시간",
        )
        drink_rows = build_drink_rows(drink_plan)
        warnings.append(
            "장시간 음료 증량분이 예산을 넘을 수 있어 최소 인원분 기준으로 조정했습니다."
        )

    # 비싼 병커피·차음료가 소규모 예산을 압박하면 동일 목적의 저가 대안으로 교체합니다.
    if sum(row.estimated_amount for row in drink_rows) > budget_cap:
        substitutions = {
            "coffee_bottle": "coffee_can",
            "tea": "juice",
        }
        substituted_plan = [
            (substitutions.get(product_key, product_key), target_units)
            for product_key, target_units in drink_plan
        ]
        drink_plan = substituted_plan
        drink_rows = build_drink_rows(drink_plan)
        warnings.append(
            "소규모 예산을 맞추기 위해 병커피·차음료를 캔커피·주스 등 저가 대안으로 조정했습니다."
        )

    # 기본 '음료 포함'은 필요 시 두 번째 보조 음료를 제외해 예산 상한을 지킵니다.
    if sum(row.estimated_amount for row in drink_rows) > budget_cap and beverage_mode == "음료 포함":
        drink_plan = drink_plan[:2]
        drink_rows = build_drink_rows(drink_plan)
        warnings.append(
            "예산 상한을 지키기 위해 기본 음료 구성의 보조 음료 1종을 제외했습니다."
        )

    # 선택한 음료 종류는 유지하되, 보조 음료 수량을 1개씩 줄여 절대 상한을 지킵니다.
    minimum_targets = []
    for product_key, target_units in drink_plan:
        minimum_targets.append(headcount if product_key == "water" else 1)

    while sum(row.estimated_amount for row in drink_rows) > budget_cap:
        adjustable_indexes = [
            index
            for index, ((_, target_units), minimum_target) in enumerate(
                zip(drink_plan, minimum_targets)
            )
            if target_units > minimum_target
        ]
        if not adjustable_indexes:
            break

        # 현재 예상금액이 큰 보조 음료부터 수량을 줄입니다.
        reduce_index = max(
            adjustable_indexes,
            key=lambda index: drink_rows[index].estimated_amount,
        )
        product_key, target_units = drink_plan[reduce_index]
        drink_plan[reduce_index] = (product_key, target_units - 1)
        drink_rows = build_drink_rows(drink_plan)

    rows.extend(drink_rows)

    # 다과는 참석 인원보다 10~20% 여유 있게 준비합니다.
    snack_target_units = ceil(headcount * (1 + spare_rate / 100))
    snack_priority = AGE_SNACK_PRIORITY[age_group]

    # 가격 변동을 감안해 기본적으로 총예산의 88% 안에서 구성합니다.
    safe_budget = int(budget_cap * 0.88)
    current_total = sum(row.estimated_amount for row in rows)

    max_snack_types = 4 if beverage_mode != "음료 제외" else 5
    min_snack_types = 2
    selected_snack_count = 0

    for product_key in snack_priority:
        if selected_snack_count >= max_snack_types:
            break

        candidate = make_row(product_key, snack_target_units, price_error_rate)
        next_total = current_total + candidate.estimated_amount

        # 최소 2종까지는 총예산 상한 안에서 우선 확보하고, 이후에는 안전 예산을 적용합니다.
        threshold = budget_cap if selected_snack_count < min_snack_types else safe_budget
        if next_total <= threshold:
            rows.append(candidate)
            current_total = next_total
            selected_snack_count += 1

    # 예산이 낮아 2종 확보가 어려우면 가장 저렴한 후보부터 상한 내에서 보완합니다.
    if selected_snack_count < min_snack_types:
        existing_keys = {row.product_key for row in rows}
        candidates = [
            make_row(key, snack_target_units, price_error_rate)
            for key in snack_priority
            if key not in existing_keys
        ]
        candidates.sort(key=lambda row: row.estimated_amount)
        for candidate in candidates:
            if current_total + candidate.estimated_amount <= budget_cap:
                rows.append(candidate)
                current_total += candidate.estimated_amount
                selected_snack_count += 1
            if selected_snack_count >= min_snack_types:
                break

    # 절대 상한을 넘는 경우 선택 우선순위가 낮은 다과부터 제거합니다.
    while sum(row.estimated_amount for row in rows) > budget_cap:
        snack_indexes = [i for i, row in enumerate(rows) if row.category == "다과"]
        if not snack_indexes:
            break
        rows.pop(snack_indexes[-1])

    snack_total = sum(row.estimated_amount for row in rows if row.category == "다과")
    drink_total = sum(row.estimated_amount for row in rows if row.category == "음료")
    estimated_total = snack_total + drink_total
    low_total = sum(row.low_amount for row in rows)
    high_total = sum(row.high_amount for row in rows)
    reserve = max(0, budget_cap - estimated_total)

    selected_snack_count = sum(1 for row in rows if row.category == "다과")
    if selected_snack_count < min_snack_types:
        warnings.append(
            "선택한 음료 구성과 예산에서는 다과 2종 확보가 어렵습니다. "
            "1인 예산을 높이거나 음료 구성을 단순화해 주세요."
        )
    if high_total > budget_cap:
        warnings.append(
            "가격이 오차범위 상단까지 상승하면 예산 상한을 넘을 수 있습니다. "
            "결제 전 실제 판매가를 확인하고 필요 시 한 품목을 줄여 주세요."
        )
    if headcount < 10:
        warnings.append(
            "10명 미만은 소포장·낱개 구매 비중이 높아 대량 구매보다 단가가 올라갈 수 있습니다."
        )
    if duration == "4시간 초과":
        warnings.append(
            "장시간 교육 기준으로 음료 수량을 약 20% 늘렸습니다. 현장 보관 공간을 확인해 주세요."
        )

    if estimated_total > budget_cap:
        raise RuntimeError("추천 결과가 총예산 상한을 초과했습니다.")

    return Recommendation(
        headcount=headcount,
        per_person_budget=per_person_budget,
        budget_cap=budget_cap,
        beverage_mode=beverage_mode,
        age_group=age_group,
        spare_rate=spare_rate,
        duration=duration,
        rows=tuple(rows),
        snack_total=snack_total,
        drink_total=drink_total,
        estimated_total=estimated_total,
        low_total=low_total,
        high_total=high_total,
        reserve=reserve,
        warnings=tuple(warnings),
    )


def recommendation_to_markdown(result: Recommendation) -> str:
    lines = [
        "# 예산 맞춤형 교육용 다과 추천서",
        "",
        "## 1. 추천 조건 요약",
        f"- 기준 인원: {result.headcount}명",
        f"- 1인 예산 상한: {result.per_person_budget:,}원",
        f"- 총예산 상한: {result.budget_cap:,}원",
        f"- 음료 포함 여부: {result.beverage_mode}",
        f"- 주 연령대: {result.age_group}",
        f"- 여유 수량: {result.spare_rate}%",
        f"- 교육 시간: {result.duration}",
        "- 추천 방향: 가성비 중심, 대중 과자, 낱개포장 또는 개별포장, 교육용 대량 배포 구성",
        "",
        "## 2. 예산 배분",
        f"- 음료 예상 예산: {result.drink_total:,}원",
        f"- 다과 예상 예산: {result.snack_total:,}원",
        f"- 예비 예산: {result.reserve:,}원",
        f"- 전체 예상 합계: {result.estimated_total:,}원",
        f"- 가격 오차범위: {result.low_total:,}~{result.high_total:,}원",
        f"- 총예산 초과 여부: {'초과' if result.estimated_total > result.budget_cap else '초과하지 않음'}",
        "",
        "## 3. 최종 추천 구성",
        "| 항목 | 추천 품목 | 권장 수량 | 예상 단가 | 예상 금액 | 가격 오차범위 | 추천 이유 |",
        "|---|---|---:|---:|---:|---:|---|",
    ]

    for row in result.rows:
        lines.append(
            f"| {row.category} | {row.product_name} | "
            f"{row.purchased_units}개 ({row.pack_description}) | "
            f"{row.estimated_unit_price:,}원/개 | {row.estimated_amount:,}원 | "
            f"{row.low_amount:,}~{row.high_amount:,}원 | {row.reason} |"
        )

    lines += ["", "## 4. 쿠팡 검색 키워드 및 링크"]
    for row in result.rows:
        lines += [
            f"- 검색어: {row.search_keyword}",
            f"- 쿠팡 검색 링크: {row.search_url}",
        ]

    lines += [
        "",
        "## 5. 구매 시 확인사항",
        "- 낱개포장 또는 개별포장 여부 확인",
        "- 총 수량이 참석 인원보다 10~20% 많은지 확인",
        "- 총 구매 금액이 인원수 × 1인 예산을 넘지 않는지 확인",
        "- 로켓배송 또는 도착 예정일 확인",
        "- 유통기한 확인",
        "- 상품 리뷰에서 파손, 녹음, 부스러기, 포장 상태 확인",
        "- 초콜릿류는 여름철 보관 온도 확인",
        "- 음료 포함 시 냉장 보관 필요 여부 확인",
        "- 교육 장소에 보관 공간이 있는지 확인",
        "- 너무 고급 디저트 위주로 담겨 단가가 올라가지 않았는지 확인",
        "",
        "> 안내: 가격은 계산용 추정치이며 쿠팡의 실시간 가격·재고와 다를 수 있습니다. "
        "이 서비스는 자동결제, 로그인, 장바구니 담기 또는 주문 대행을 하지 않습니다.",
    ]

    if result.warnings:
        lines += ["", "## 주의사항"]
        lines += [f"- {warning}" for warning in result.warnings]

    return "\n".join(lines)
