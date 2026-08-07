from __future__ import annotations

"""프리미엄 교육용 다과 추천 Streamlit 앱.

배포 안정성을 위해 상품 카탈로그, 추천 엔진, 화면을 하나의 파일에 통합했습니다.
catalog.py 또는 snack_recommender.py의 이전 버전이 저장소에 남아 있어도 이 파일은
해당 모듈을 import하지 않으므로 버전 불일치 ImportError가 발생하지 않습니다.
"""

import csv
import io
from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
from itertools import product
from math import ceil, floor
from typing import Iterable, Literal, Sequence
from urllib.parse import quote_plus

import streamlit as st

Category = Literal["다과", "음료"]


@dataclass(frozen=True)
class PackOption:
    size: int
    price: int


@dataclass(frozen=True)
class Product:
    key: str
    name: str
    category: Category
    search_keyword: str
    reason: str
    pack_options: tuple[PackOption, ...]
    premium_label: str
    individually_packed: bool = True

    @property
    def reference_unit_price(self) -> int:
        """카탈로그 묶음 중 현실적인 최저 개당 추정가."""
        return round(min(option.price / option.size for option in self.pack_options))


PRODUCTS: dict[str, Product] = {
    # 프리미엄 다과 16종
    "osulloc_langue": Product(
        "osulloc_langue",
        "오설록 그린티 랑드샤 소포장",
        "다과",
        "오설록 그린티 랑드샤 개별포장",
        "오설록 브랜드가 바로 보여 환대감이 높고 차·커피와 잘 어울림",
        (PackOption(1, 2_900), PackOption(10, 28_000), PackOption(20, 54_000), PackOption(30, 79_500)),
        "제주 티푸드",
    ),
    "osulloc_wafer": Product(
        "osulloc_wafer",
        "오설록 제주 녹차 웨하스 소포장",
        "다과",
        "오설록 녹차 웨하스 개별포장",
        "녹차 풍미와 브랜드 인지도가 있어 일반 대중과자보다 대접받는 인상을 줌",
        (PackOption(1, 2_500), PackOption(10, 24_000), PackOption(20, 48_000), PackOption(30, 69_000)),
        "제주 티푸드",
    ),
    "godiva_napolitain": Product(
        "godiva_napolitain",
        "고디바 나폴리탄 초콜릿 소포장",
        "다과",
        "고디바 나폴리탄 초콜릿 개별포장",
        "브랜드 인지도가 높고 작은 소포장만으로도 프리미엄 인상을 주기 좋음",
        (PackOption(1, 3_200), PackOption(10, 30_000), PackOption(20, 58_000), PackOption(40, 112_000)),
        "프리미엄 초콜릿",
    ),
    "ferrero_rocher": Product(
        "ferrero_rocher",
        "페레로로쉐 3구 소포장",
        "다과",
        "페레로로쉐 3구 소포장 대량",
        "금색 포장과 높은 인지도로 교육 참가자가 선물형 간식처럼 느끼기 쉬움",
        (PackOption(1, 2_900), PackOption(8, 22_000), PackOption(16, 42_000), PackOption(32, 80_000)),
        "프리미엄 초콜릿",
    ),
    "lindt_lindor": Product(
        "lindt_lindor",
        "린트 린도르 2구 소포장",
        "다과",
        "린트 린도르 초콜릿 개별포장 소포장",
        "부드러운 초콜릿으로 만족도가 높고 개별 배포가 깔끔함",
        (PackOption(1, 2_600), PackOption(10, 24_500), PackOption(20, 46_000), PackOption(40, 88_000)),
        "프리미엄 초콜릿",
    ),
    "shilla_madeleine": Product(
        "shilla_madeleine",
        "신라명과 마들렌 개별포장",
        "다과",
        "신라명과 마들렌 개별포장 대량",
        "부드럽고 포만감이 있으며 브랜드 베이커리 느낌을 살리기 좋음",
        (PackOption(1, 1_900), PackOption(10, 17_500), PackOption(20, 33_000), PackOption(40, 62_000)),
        "브랜드 베이커리",
    ),
    "premium_financier": Product(
        "premium_financier",
        "프리미엄 휘낭시에 개별포장",
        "다과",
        "프리미엄 휘낭시에 개별포장 대량",
        "일반 과자보다 격식 있는 구운과자 인상을 주면서 낱개 배포가 가능함",
        (PackOption(1, 2_300), PackOption(10, 22_000), PackOption(20, 44_000), PackOption(30, 64_500)),
        "구운과자",
    ),
    "walkers_shortbread": Product(
        "walkers_shortbread",
        "워커스 쇼트브레드 소포장",
        "다과",
        "워커스 쇼트브레드 개별포장",
        "수입 버터 쿠키의 깔끔한 인상과 커피 궁합이 좋아 교육용 테이블에 잘 어울림",
        (PackOption(1, 1_900), PackOption(12, 21_000), PackOption(24, 39_500), PackOption(36, 57_000)),
        "수입 버터쿠키",
    ),
    "marketo_brownie": Product(
        "marketo_brownie",
        "마켓오 리얼브라우니 개별포장",
        "다과",
        "마켓오 리얼브라우니 개별포장 대용량",
        "익숙하면서도 일반 파이류보다 고급스러운 초콜릿 디저트 인상을 줌",
        (PackOption(1, 1_600), PackOption(8, 12_000), PackOption(16, 23_000), PackOption(24, 33_000)),
        "초콜릿 디저트",
    ),
    "loacker_minis": Product(
        "loacker_minis",
        "로아커 미니스 웨하스 소포장",
        "다과",
        "로아커 미니스 웨하스 개별포장 대량",
        "수입 브랜드 웨하스로 가볍고 깔끔하며 포장 상태가 단정함",
        (PackOption(1, 1_500), PackOption(10, 14_000), PackOption(20, 26_000), PackOption(40, 49_000)),
        "수입 웨하스",
    ),
    "premium_nuts": Product(
        "premium_nuts",
        "프리미엄 하루견과 소포장",
        "다과",
        "프리미엄 하루견과 개별포장 30개",
        "달콤한 품목 사이에 담백함과 포만감을 더해 구성의 완성도를 높임",
        (PackOption(1, 1_900), PackOption(10, 18_000), PackOption(20, 34_000), PackOption(30, 48_000)),
        "건강 간식",
    ),
    "nature_valley": Product(
        "nature_valley",
        "네이처밸리 그래놀라바 소포장",
        "다과",
        "네이처밸리 그래놀라바 개별포장 대량",
        "수입 브랜드와 곡물 이미지를 함께 갖춰 담백한 균형 구성에 적합",
        (PackOption(1, 1_500), PackOption(12, 17_000), PackOption(24, 32_000), PackOption(48, 60_000)),
        "곡물 바",
    ),
    "orga_rice_snack": Product(
        "orga_rice_snack",
        "올가 현미·쌀과자 소포장",
        "다과",
        "올가 현미 쌀과자 개별포장",
        "단맛을 낮추면서도 유기농·건강한 브랜드 이미지를 보완함",
        (PackOption(1, 1_600), PackOption(10, 15_000), PackOption(20, 28_000), PackOption(30, 40_500)),
        "담백한 쌀과자",
    ),
    "jeju_peanut_pie": Product(
        "jeju_peanut_pie",
        "제주 우도땅콩 찰떡파이 개별포장",
        "다과",
        "제주 우도땅콩 찰떡파이 개별포장",
        "지역 특산물 느낌과 쫀득한 식감으로 평범한 대중과자 구성을 피할 수 있음",
        (PackOption(1, 1_700), PackOption(10, 15_800), PackOption(20, 30_000), PackOption(30, 43_500)),
        "제주 특산 디저트",
    ),
    "premium_yakgwa": Product(
        "premium_yakgwa",
        "프리미엄 미니약과 개별포장",
        "다과",
        "프리미엄 미니약과 개별포장 선물용",
        "전통 간식을 깔끔하게 개별 배포할 수 있어 혼합 연령대에도 무난함",
        (PackOption(1, 1_500), PackOption(10, 14_000), PackOption(20, 26_500), PackOption(40, 50_000)),
        "전통 디저트",
    ),
    "protein_bar": Product(
        "protein_bar",
        "프리미엄 단백질바 개별포장",
        "다과",
        "프리미엄 단백질바 개별포장 대량",
        "장시간 교육에서 포만감을 보완하고 지나치게 단 디저트 비중을 낮춤",
        (PackOption(1, 2_000), PackOption(12, 22_500), PackOption(24, 43_000), PackOption(36, 61_500)),
        "포만감 간식",
    ),
    "dancake_cookie": Product(
        "dancake_cookie",
        "댄케이크 버터쿠키 소포장",
        "다과",
        "댄케이크 버터쿠키 소포장 개별포장",
        "수입 쿠키 특유의 단정한 이미지로 커피와 함께 제공하기 좋음",
        (PackOption(1, 1_700), PackOption(10, 15_800), PackOption(20, 30_000), PackOption(40, 56_000)),
        "수입 버터쿠키",
    ),

    # 음료: 커피는 모든 기준 묶음에서 개당 1,000원 이상이 되도록 설정
    "water_samdasoo": Product(
        "water_samdasoo",
        "제주삼다수 500ml",
        "음료",
        "제주삼다수 500ml 대량",
        "브랜드 인지도가 높고 모든 참가자에게 기본 제공하기 좋은 생수",
        (PackOption(1, 700), PackOption(20, 11_500), PackOption(40, 21_000)),
        "브랜드 생수",
        False,
    ),
    "coffee_starbucks": Product(
        "coffee_starbucks",
        "스타벅스 프라푸치노 병커피",
        "음료",
        "스타벅스 프라푸치노 병커피 대량",
        "한 병만 놓아도 환대감이 분명한 프리미엄 브랜드 커피",
        (PackOption(1, 2_700), PackOption(6, 15_600), PackOption(12, 30_000), PackOption(24, 58_000)),
        "프리미엄 병커피",
        False,
    ),
    "coffee_cantata": Product(
        "coffee_cantata",
        "칸타타 콘트라베이스 PET 커피",
        "음료",
        "칸타타 콘트라베이스 500ml PET 대량",
        "대용량 PET와 브랜드 인지도를 갖춘 고급형 교육용 커피",
        (PackOption(1, 2_000), PackOption(6, 11_500), PackOption(12, 22_000), PackOption(24, 42_000)),
        "프리미엄 PET 커피",
        False,
    ),
    "coffee_top": Product(
        "coffee_top",
        "TOP 마스터라떼 병·캔커피",
        "음료",
        "TOP 마스터라떼 대량 세트",
        "개당 1,000원 이상의 브랜드 커피로 예산과 품질의 균형이 좋음",
        (PackOption(1, 1_700), PackOption(10, 16_000), PackOption(20, 30_000), PackOption(30, 43_500)),
        "브랜드 커피",
        False,
    ),
    "other_imreal": Product(
        "other_imreal",
        "풀무원 아임리얼 과일주스",
        "음료",
        "풀무원 아임리얼 주스 소용량 대량",
        "커피를 마시지 않는 참가자에게도 프리미엄 대안을 제공할 수 있음",
        (PackOption(1, 2_500), PackOption(6, 14_500), PackOption(12, 28_000), PackOption(24, 53_000)),
        "프리미엄 주스",
        False,
    ),
    "other_teazle": Product(
        "other_teazle",
        "티즐 제로 차음료 500ml",
        "음료",
        "티즐 제로 500ml 대량",
        "깔끔한 병 디자인과 가벼운 맛으로 교육 중 마시기 편함",
        (PackOption(1, 1_700), PackOption(12, 19_000), PackOption(24, 36_000)),
        "브랜드 차음료",
        False,
    ),
    "other_barley": Product(
        "other_barley",
        "하늘보리 500ml",
        "음료",
        "하늘보리 500ml 대량",
        "단맛 부담이 적고 다양한 참가자가 편하게 마실 수 있는 보조 음료",
        (PackOption(1, 1_400), PackOption(12, 15_500), PackOption(24, 29_000)),
        "담백한 차음료",
        False,
    ),
}


PROFILE_PRIORITIES: dict[str, tuple[str, ...]] = {
    "달콤하고 간편한 구성": (
        "godiva_napolitain",
        "ferrero_rocher",
        "osulloc_langue",
        "lindt_lindor",
        "osulloc_wafer",
        "premium_financier",
        "shilla_madeleine",
        "marketo_brownie",
        "walkers_shortbread",
        "loacker_minis",
        "dancake_cookie",
        "jeju_peanut_pie",
        "premium_yakgwa",
        "nature_valley",
        "premium_nuts",
        "protein_bar",
    ),
    "담백함을 더한 균형 구성": (
        "premium_nuts",
        "protein_bar",
        "nature_valley",
        "orga_rice_snack",
        "osulloc_wafer",
        "walkers_shortbread",
        "shilla_madeleine",
        "premium_financier",
        "jeju_peanut_pie",
        "premium_yakgwa",
        "dancake_cookie",
        "loacker_minis",
        "osulloc_langue",
        "marketo_brownie",
        "lindt_lindor",
        "ferrero_rocher",
    ),
    "둘 다 혼합": (
        "osulloc_langue",
        "premium_nuts",
        "ferrero_rocher",
        "nature_valley",
        "osulloc_wafer",
        "shilla_madeleine",
        "godiva_napolitain",
        "orga_rice_snack",
        "premium_financier",
        "jeju_peanut_pie",
        "lindt_lindor",
        "protein_bar",
        "walkers_shortbread",
        "premium_yakgwa",
        "marketo_brownie",
        "loacker_minis",
    ),
}

PARTICIPANT_PROFILES = tuple(PROFILE_PRIORITIES.keys())
DRINK_OPTIONS = ("생수 포함", "커피 포함", "그 외 음료 포함")


DAILY_BUDGET = 10_000
MIN_DAILY_BUDGET = 1_000
MAX_DAILY_BUDGET = 10_000
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
    estimated_amount: int
    budget_cap: int
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


def snack_type_count_for_days(education_days: int) -> int:
    """최종 구매 다과 종류 수: 1일 8종에서 일수마다 2종씩 늘립니다."""
    return min(16, 6 + 2 * education_days)


def snack_pool_size_for_days(education_days: int) -> int:
    """하위 호환용 별칭입니다. 반환값은 최종 구매 다과 종류 수입니다."""
    return snack_type_count_for_days(education_days)


def _configuration_items(profile: str, education_days: int) -> tuple[PoolItem, ...]:
    snack_type_count = snack_type_count_for_days(education_days)
    priority_keys = PROFILE_PRIORITIES[profile]
    # 짧은 교육은 오설록·고디바처럼 인지도가 높은 품목을 전면에 두되,
    # 묶음 구매 단가가 낮은 품목도 함께 넣어 음료를 더해도 예산을 지킬 수 있게 합니다.
    # 교육일수가 길어지면 더 많은 가성비 품목이 실제 구매 구성으로 자연스럽게 확장됩니다.
    premium_target = 2 if education_days < 5 else snack_type_count
    premium_keys = [
        key for key in priority_keys
        if PRODUCTS[key].reference_unit_price >= 2_000
    ][:premium_target]
    value_keys = [
        key for key in priority_keys
        if PRODUCTS[key].reference_unit_price < 2_000 and key not in premium_keys
    ]
    remaining_keys = [
        key for key in priority_keys
        if key not in premium_keys and key not in value_keys
    ]
    keys = tuple((premium_keys + value_keys + remaining_keys)[:snack_type_count])
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


def _daily_type_counts(
    snack_type_count: int,
    education_days: int,
) -> tuple[int, ...]:
    """모든 최종 구매 품목을 일자별로 한 번씩 배치합니다."""
    base, remainder = divmod(snack_type_count, education_days)
    return tuple(base + (1 if day < remainder else 0) for day in range(education_days))


def _schedule_from_order(
    order: Sequence[str],
    daily_type_counts: Sequence[int],
    offset: int = 0,
) -> tuple[tuple[str, ...], ...]:
    if sum(daily_type_counts) != len(order):
        raise RuntimeError("최종 구매 다과 종류 수와 일자별 배치 수가 일치하지 않습니다.")

    rotated_order = tuple(order[offset:]) + tuple(order[:offset])
    schedules: list[tuple[str, ...]] = []
    cursor = 0
    for count in daily_type_counts:
        schedules.append(tuple(rotated_order[cursor : cursor + count]))
        cursor += count
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

    # 8/10/12/14/16종은 후보 풀이 아니라 실제 최종 구매 구성입니다.
    # 따라서 모든 일정안은 전체 품목을 정확히 한 번씩 포함합니다. 일수가 길수록
    # 우선순위 뒤쪽의 비교적 저렴한 품목까지 포함돼 프리미엄·가성비 구성이 자연스럽게 섞입니다.
    daily_type_counts = _daily_type_counts(len(pool_keys), education_days)
    for full_order in (profile_order, price_asc, price_desc, midpoint):
        for offset in range(min(len(full_order), 8)):
            schedule = _schedule_from_order(full_order, daily_type_counts, offset)
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


def _daily_estimated_amounts(
    snack_schedule: Sequence[Sequence[str]],
    daily_allocations: Sequence[dict[str, int]],
    drink_schedule: Sequence[Sequence[str]],
    headcount: int,
) -> tuple[int, ...]:
    """일자별 제공안이 각각 1일 예산 상한 안에 드는지 계산합니다."""
    amounts: list[int] = []
    for day_index, (snack_keys, allocation, drink_keys) in enumerate(
        zip(snack_schedule, daily_allocations, drink_schedule), start=1
    ):
        snack_amount = sum(
            make_row(key, allocation[key], (day_index,)).estimated_amount
            for key in snack_keys
        )
        drink_amount = sum(
            make_row(key, headcount, (day_index,)).estimated_amount
            for key in drink_keys
        )
        amounts.append(snack_amount + drink_amount)
    return tuple(amounts)


def _candidate_score(
    total: int,
    budget_cap: int,
    snack_schedule: Sequence[Sequence[str]],
    drink_schedule: Sequence[Sequence[str]],
    daily_amounts: Sequence[int],
) -> tuple[float, int, int, int]:
    # 90% 안팎을 우선하되, 같으면 더 다양한 품목과 스타벅스 포함을 선호합니다.
    target = budget_cap * 0.90
    distance = abs(total - target)
    daily_spread = max(daily_amounts) - min(daily_amounts)
    unique_snacks = len({key for day in snack_schedule for key in day})
    premium_coffee_bonus = int(any("coffee_starbucks" in day for day in drink_schedule))
    return (-distance, -daily_spread, unique_snacks, premium_coffee_bonus)


def build_recommendation(
    *,
    headcount: int,
    education_days: int = 1,
    daily_budget: int = DAILY_BUDGET,
    drink_options: Iterable[str] = (),
    participant_profile: str = "둘 다 혼합",
) -> Recommendation:
    if not 1 <= headcount <= 1_000:
        raise ValueError("인원수는 1명 이상 1,000명 이하로 입력해 주세요.")
    if not 1 <= education_days <= 5:
        raise ValueError("교육일수는 1일 이상 5일 이하로 입력해 주세요.")
    if not MIN_DAILY_BUDGET <= daily_budget <= MAX_DAILY_BUDGET:
        raise ValueError(
            f"1인 1일 예산 상한은 {MIN_DAILY_BUDGET:,}원 이상 {MAX_DAILY_BUDGET:,}원 이하로 입력해 주세요."
        )
    if participant_profile not in PARTICIPANT_PROFILES:
        raise ValueError("지원하지 않는 참가자 성향입니다.")

    normalized_drinks = tuple(
        option for option in DRINK_OPTIONS if option in set(drink_options)
    )
    invalid_drinks = set(drink_options) - set(DRINK_OPTIONS)
    if invalid_drinks:
        raise ValueError("지원하지 않는 음료 옵션이 포함되어 있습니다.")

    person_days = headcount * education_days
    budget_cap = person_days * daily_budget
    pool_items = _configuration_items(participant_profile, education_days)
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
            daily_amounts = _daily_estimated_amounts(
                snack_schedule,
                daily_allocations,
                drink_schedule,
                headcount,
            )
            daily_budget_cap = headcount * daily_budget
            if total > budget_cap or any(amount > daily_budget_cap for amount in daily_amounts):
                continue

            score = _candidate_score(
                total, budget_cap, snack_schedule, drink_schedule, daily_amounts
            )
            if best_score is None or score > best_score:
                best_score = score
                best = (
                    drink_schedule,
                    drink_rows,
                    snack_schedule,
                    snack_rows,
                    daily_allocations,
                    daily_amounts,
                )

    if best is None:
        raise RuntimeError(
            "선택한 예산 안에서 최종 구매 다과 구성을 만들기 어렵습니다. 예산 상한 또는 음료 구성을 조정해 주세요."
        )

    (
        drink_schedule,
        drink_rows,
        snack_schedule,
        snack_rows,
        daily_allocations,
        daily_amounts,
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
                estimated_amount=daily_amounts[day_index],
                budget_cap=headcount * daily_budget,
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
            "선택한 음료가 적어 예상 사용률이 낮습니다. 다만 최종 구매 다과 종류 수와 전체 10% 여유 수량은 유지했습니다."
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
        per_person_daily_budget=daily_budget,
        cumulative_per_person_cap=education_days * daily_budget,
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
        f"- 최종 구매 다과 구성: {result.snack_pool_size}종",
        f"- 제공 기준: 1인 1일 평균 {result.snacks_per_person_day}개, 전체 {result.snack_spare_rate}% 여유",
        "- 모든 다과는 개별포장 또는 소포장 상품 검색을 전제로 합니다.",
        "",
        "## 2. 최종 구매 다과 구성",
        "| 순위 | 구매 품목 | 구분 | 기준 개당 추정가 | 쿠팡 검색 |",
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
        "| 교육일 | 다과 구성 | 음료 | 일자별 예상 금액 | 일자별 상한 | 배포 기준 |",
        "|---:|---|---|---:|---:|---|",
    ]
    for plan in result.daily_plans:
        drinks = ", ".join(plan.drink_names) or "음료 없음"
        lines.append(
            f"| {plan.day}일차 | {', '.join(plan.snack_names)} | {drinks} | "
            f"{plan.estimated_amount:,}원 | {plan.budget_cap:,}원 | {plan.distribution_note} |"
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


st.set_page_config(
    page_title="프리미엄 교육용 다과 추천",
    page_icon="🎁",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
        .block-container {
            max-width: 1260px;
            padding-top: 1.7rem;
            padding-bottom: 3rem;
        }
        .hero {
            padding: 1.7rem 1.8rem;
            border-radius: 20px;
            background: linear-gradient(135deg, #fffaf0 0%, #fff7ed 45%, #f7fee7 100%);
            border: 1px solid #fed7aa;
            margin-bottom: 1.2rem;
        }
        .hero h1 {
            margin: 0 0 .45rem 0;
            font-size: clamp(1.8rem, 4vw, 2.65rem);
            line-height: 1.18;
        }
        .hero p {
            margin: 0;
            color: #4b5563;
            line-height: 1.72;
        }
        .soft-card {
            padding: 1rem 1.15rem;
            border-radius: 14px;
            background: #fafafa;
            border: 1px solid #e5e7eb;
        }
        .premium-card {
            padding: 1rem 1.15rem;
            border-radius: 14px;
            background: #fffbeb;
            border-left: 4px solid #d97706;
            margin-top: .8rem;
        }
        .fine-print {
            color: #6b7280;
            font-size: .9rem;
            line-height: 1.65;
        }
        div[data-testid="stMetric"] {
            border: 1px solid #e5e7eb;
            padding: .8rem 1rem;
            border-radius: 14px;
            background: white;
        }
        .stAlert { border-radius: 12px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <h1>🎁 프리미엄 교육용 다과 추천</h1>
        <p>
            정확한 인원수와 교육일수로 계산하며, <b>1인 1일 예산 상한(최대 10,000원)</b> 안에서
            참가자가 대접받는 느낌을 받을 수 있는 브랜드 다과를 추천합니다.
            모든 다과는 <b>개별포장·소포장</b>을 전제로 하고,
            하루 <b>1인 평균 3개</b>와 전체 10% 여유 수량을 적용합니다.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.form("recommendation_form", border=True):
    st.subheader("조건 입력")
    st.caption(
        "고급 설정 없이 네 가지 항목만 사용합니다. 음료 체크박스는 모두 해제된 상태에서 시작하며 중복 선택할 수 있습니다."
    )

    c1, c2, c3, c4 = st.columns([1, 1, 1, 1.35])
    with c1:
        headcount = st.number_input(
            "1. 정확한 인원수",
            min_value=1,
            max_value=1_000,
            value=30,
            step=1,
            help="구간 선택 없이 실제 참석 인원을 바로 입력합니다.",
        )
    with c2:
        education_days = st.number_input(
            "2. 교육일수",
            min_value=1,
            max_value=5,
            value=1,
            step=1,
            help="최소 1일, 최대 5일입니다.",
        )
    with c3:
        daily_budget = st.number_input(
            "3. 1인 1일 예산 상한",
            min_value=MIN_DAILY_BUDGET,
            max_value=MAX_DAILY_BUDGET,
            value=DAILY_BUDGET,
            step=100,
            help="1,000원부터 최대 10,000원까지 자유롭게 설정할 수 있습니다.",
        )
    with c4:
        participant_profile = st.selectbox(
            "4. 참가자 성향",
            options=PARTICIPANT_PROFILES,
            index=2,
            help="달콤한 구성, 담백한 균형 구성, 두 성향의 혼합 중 하나를 선택합니다.",
        )

    st.markdown("**5. 음료 포함 항목**")
    st.caption("필요한 항목만 체크하세요. 세 항목을 동시에 선택할 수도 있습니다.")
    d1, d2, d3 = st.columns(3)
    with d1:
        include_water = st.checkbox("생수 포함", value=False)
    with d2:
        include_coffee = st.checkbox("커피 포함", value=False)
    with d3:
        include_other = st.checkbox("그 외 음료 포함", value=False)

    selected_drinks = tuple(
        option
        for option, enabled in (
            ("생수 포함", include_water),
            ("커피 포함", include_coffee),
            ("그 외 음료 포함", include_other),
        )
        if enabled
    )

    preview_cap = int(headcount) * int(education_days) * int(daily_budget)
    preview_type_count = snack_type_count_for_days(int(education_days))
    st.info(
        f"총예산 상한: {int(headcount):,}명 × {int(education_days)}일 × "
        f"{int(daily_budget):,}원 = {preview_cap:,}원 · 최종 구매 다과 구성 {preview_type_count}종"
    )

    submitted = st.form_submit_button(
        "프리미엄 구성 추천받기",
        type="primary",
        width="stretch",
    )

if submitted:
    try:
        st.session_state["recommendation"] = build_recommendation(
            headcount=int(headcount),
            education_days=int(education_days),
            daily_budget=int(daily_budget),
            drink_options=selected_drinks,
            participant_profile=participant_profile,
        )
    except (ValueError, RuntimeError) as error:
        st.error(str(error))

result: Recommendation | None = st.session_state.get("recommendation")

if result is None:
    st.info("조건을 입력하고 추천 버튼을 눌러 주세요.")
    st.stop()

st.divider()
top_left, top_right = st.columns([4, 1])
with top_left:
    st.header("1. 추천 조건 요약")
with top_right:
    st.link_button(
        "쿠팡 홈 바로가기",
        COUPANG_HOME_URL,
        type="primary",
        width="stretch",
    )

summary_cols = st.columns(5)
summary_cols[0].metric("정확한 인원", f"{result.headcount:,}명")
summary_cols[1].metric("교육일수", f"{result.education_days}일")
summary_cols[2].metric("총 제공 기준", f"{result.person_days:,}인일")
summary_cols[3].metric("최종 구매 다과", f"{result.snack_pool_size}종")
summary_cols[4].metric("총예산 상한", f"{result.budget_cap:,}원")

estimated_per_person_day = result.estimated_total / result.person_days
st.markdown(
    f"""
    <div class="soft-card">
        <b>참가자 성향</b> · {result.participant_profile}<br>
        <b>음료 선택</b> · {result.drink_summary}<br>
        <b>다과 제공 기준</b> · 하루 1인 평균 {result.snacks_per_person_day}개,
        전체 {result.snack_spare_rate}% 여유<br>
        <b>최종 구매 구성</b> · 교육 {result.education_days}일 기준 {result.snack_pool_size}종
        (일수가 길수록 가성비 품목 비중 확대)<br>
        <b>예상 1인 1일 비용</b> · {estimated_per_person_day:,.0f}원<br>
        <b>포장 기준</b> · 모든 다과는 낱개포장 또는 개별 소포장 상품
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="premium-card">
        <b>프리미엄 선정 원칙</b><br>
        오설록·고디바·페레로로쉐·린트·신라명과·워커스·로아커처럼
        참가자가 상품명과 포장만 보고도 일반 대중과자보다 한 단계 높게 느낄 수 있는 품목을 우선합니다.
        커피는 스타벅스 병커피, 칸타타 콘트라베이스, TOP 등 개당 추정가 1,000원 이상의 완제품만 사용합니다.
    </div>
    """,
    unsafe_allow_html=True,
)

st.header("2. 최종 구매 다과 구성")
st.caption(
    "요청하신 예시를 적용해 최종 구매 품목을 1일 8종, 2일 10종, 3일 12종, 4일 14종, 5일 16종으로 구성합니다. "
    "교육일수가 길수록 프리미엄 품목에 가성비 품목을 더해 하루 총예산은 동일하게 유지합니다."
)
pool_rows = [
    {
        "순위": item.rank,
        "구매 품목": item.product_name,
        "프리미엄 구분": item.premium_label,
        "기준 개당 추정가": item.reference_unit_price,
        "추천 이유": item.reason,
        "쿠팡 검색": item.search_url,
    }
    for item in result.snack_pool
]
pool_df = pool_rows
st.dataframe(
    pool_df,
    hide_index=True,
    width="stretch",
    column_config={
        "기준 개당 추정가": st.column_config.NumberColumn(
            "기준 개당 추정가", format="%d원"
        ),
        "추천 이유": st.column_config.TextColumn("추천 이유", width="large"),
        "쿠팡 검색": st.column_config.LinkColumn(
            "쿠팡 검색", display_text="바로 열기"
        ),
    },
)

st.header("3. 일자별 운영안")
daily_rows = [
    {
        "교육일": f"{plan.day}일차",
        "다과 구성": ", ".join(plan.snack_names),
        "총 다과 수량": plan.snack_units,
        "음료 구성": ", ".join(plan.drink_names) or "음료 없음",
        "일자별 예상 금액": plan.estimated_amount,
        "일자별 예산 상한": plan.budget_cap,
        "배포 기준": plan.distribution_note,
    }
    for plan in result.daily_plans
]
daily_df = daily_rows
st.dataframe(
    daily_df,
    hide_index=True,
    width="stretch",
    column_config={
        "다과 구성": st.column_config.TextColumn("다과 구성", width="large"),
        "총 다과 수량": st.column_config.NumberColumn("총 다과 수량", format="%d개"),
        "음료 구성": st.column_config.TextColumn("음료 구성", width="large"),
        "일자별 예상 금액": st.column_config.NumberColumn("일자별 예상 금액", format="%d원"),
        "일자별 예산 상한": st.column_config.NumberColumn("일자별 예산 상한", format="%d원"),
        "배포 기준": st.column_config.TextColumn("배포 기준", width="large"),
    },
)

st.header("4. 예산 배분")
budget_cols = st.columns(5)
budget_cols[0].metric("음료 예상 예산", f"{result.drink_total:,}원")
budget_cols[1].metric("다과 예상 예산", f"{result.snack_total:,}원")
budget_cols[2].metric("전체 예상 합계", f"{result.estimated_total:,}원")
budget_cols[3].metric("예비 예산", f"{result.reserve:,}원")
budget_cols[4].metric("예산 사용률", f"{result.budget_usage_rate:.1%}")

status_text = "초과하지 않음" if result.estimated_total <= result.budget_cap else "초과"
st.write(
    f"가격 오차범위: **약 {result.low_total:,}~{result.high_total:,}원** · "
    f"총예산 초과 여부: **{status_text}**"
)
for warning in result.warnings:
    st.warning(warning)

st.header("5. 최종 구매 구성")
table_rows = [
    {
        "항목": row.category,
        "추천 품목": row.product_name,
        "프리미엄 구분": row.premium_label,
        "제공일": ", ".join(f"{day}일차" for day in row.service_days),
        "목표 수량": row.target_units,
        "권장 구매 수량": row.purchased_units,
        "구매 묶음": row.pack_description,
        "예상 단가": row.estimated_unit_price,
        "예상 금액": row.estimated_amount,
        "가격 오차범위": f"{row.low_amount:,}~{row.high_amount:,}원",
        "추천 이유": row.reason,
        "쿠팡 검색": row.search_url,
    }
    for row in result.rows
]
df = table_rows
st.dataframe(
    df,
    hide_index=True,
    width="stretch",
    column_config={
        "목표 수량": st.column_config.NumberColumn("목표 수량", format="%d개"),
        "권장 구매 수량": st.column_config.NumberColumn(
            "권장 구매 수량", format="%d개"
        ),
        "예상 단가": st.column_config.NumberColumn("예상 단가", format="%d원"),
        "예상 금액": st.column_config.NumberColumn("예상 금액", format="%d원"),
        "추천 이유": st.column_config.TextColumn("추천 이유", width="large"),
        "구매 묶음": st.column_config.TextColumn("구매 묶음", width="medium"),
        "쿠팡 검색": st.column_config.LinkColumn(
            "쿠팡 검색", display_text="바로 열기"
        ),
    },
)

st.header("6. 쿠팡 바로가기")
st.caption(
    "상품 상세 주소는 재고와 판매자가 자주 바뀌므로 검색 링크를 사용합니다. "
    "아래 버튼은 현재 결과에 포함된 모든 구매 품목을 쿠팡에서 바로 검색합니다."
)
for index, row in enumerate(result.rows):
    with st.container(border=True):
        link_col, button_col = st.columns([3, 1])
        with link_col:
            st.markdown(f"**{row.product_name}** · {row.premium_label}")
            st.code(row.search_keyword, language=None)
            st.caption(
                f"권장 {row.purchased_units}개 · 예상 {row.estimated_amount:,}원 · "
                f"{row.pack_description}"
            )
        with button_col:
            st.link_button(
                "쿠팡에서 검색",
                row.search_url,
                type="primary" if index < 3 else "secondary",
                width="stretch",
            )

st.header("7. 구매 시 확인사항")
checklist = [
    "모든 다과가 실제 낱개포장 또는 개별 소포장인지 확인",
    "하루 총 다과 수량이 인원수 × 3개보다 약 10% 많은지 확인",
    "커피가 완제품 병/PET/캔이며 실제 개당 가격이 1,000원 이상인지 확인",
    "쿠팡 상품의 입수량과 앱의 구매 묶음 추정치가 일치하는지 확인",
    "총 구매 금액이 인원수 × 교육일수 × 10,000원을 넘지 않는지 확인",
    "로켓배송 또는 행사 전 도착 예정일 확인",
    "유통기한과 장기 교육 보관 가능 기간 확인",
    "초콜릿류의 여름철 녹음 및 파손 리뷰 확인",
    "아임리얼 등 냉장 음료 선택 시 냉장 보관 공간 확인",
    "일자별 분배 박스와 라벨을 미리 준비했는지 확인",
]
left, right = st.columns(2)
for idx, item in enumerate(checklist):
    target = left if idx % 2 == 0 else right
    target.checkbox(
        item,
        value=False,
        key=f"check_{idx}_{result.headcount}_{result.education_days}_{result.estimated_total}",
    )

st.header("결과 저장")
download_1, download_2, download_3, download_4 = st.columns(4)

csv_buffer = io.StringIO()
writer = csv.DictWriter(csv_buffer, fieldnames=list(table_rows[0].keys()) if table_rows else [])
writer.writeheader()
writer.writerows(table_rows)
csv_data = "\ufeff" + csv_buffer.getvalue()

daily_csv_buffer = io.StringIO()
daily_writer = csv.DictWriter(daily_csv_buffer, fieldnames=list(daily_rows[0].keys()) if daily_rows else [])
daily_writer.writeheader()
daily_writer.writerows(daily_rows)
daily_csv_data = "\ufeff" + daily_csv_buffer.getvalue()

pool_csv_buffer = io.StringIO()
pool_writer = csv.DictWriter(pool_csv_buffer, fieldnames=list(pool_rows[0].keys()) if pool_rows else [])
pool_writer.writeheader()
pool_writer.writerows(pool_rows)
pool_csv_data = "\ufeff" + pool_csv_buffer.getvalue()

with download_1:
    st.download_button(
        "구매 구성표 CSV",
        data=csv_data.encode("utf-8-sig"),
        file_name=f"프리미엄_다과_구매구성_{result.headcount}명_{result.education_days}일.csv",
        mime="text/csv",
        width="stretch",
    )
with download_2:
    st.download_button(
        "일자별 운영안 CSV",
        data=daily_csv_data.encode("utf-8-sig"),
        file_name=f"프리미엄_다과_일자별운영_{result.headcount}명_{result.education_days}일.csv",
        mime="text/csv",
        width="stretch",
    )
with download_3:
    st.download_button(
        "최종 구매 다과 구성 CSV",
        data=pool_csv_data.encode("utf-8-sig"),
        file_name=f"프리미엄_다과_최종구성_{result.education_days}일.csv",
        mime="text/csv",
        width="stretch",
    )
with download_4:
    report = recommendation_to_markdown(result)
    st.download_button(
        "전체 추천서 Markdown",
        data=report.encode("utf-8"),
        file_name=f"프리미엄_다과_추천서_{result.headcount}명_{result.education_days}일.md",
        mime="text/markdown",
        width="stretch",
    )

st.divider()
st.markdown(
    """
    <p class="fine-print">
        가격은 추천 계산을 위한 추정치이며 쿠팡의 실시간 가격·재고와 다를 수 있습니다.
        결제 전 상품 수량, 개별포장 여부, 배송일, 유통기한, 냉장 조건과 최종 금액을 확인하세요.
        이 웹앱은 자동결제, 계정 로그인, 장바구니 자동담기 또는 주문 대행을 하지 않습니다.
    </p>
    """,
    unsafe_allow_html=True,
)
