"""프리미엄 교육용 다과 추천에 사용하는 추정 상품 카탈로그.

가격은 실시간 판매가가 아니라 추천 계산용 기준값입니다.
모든 다과는 '개별포장/소포장 상품을 검색한다'는 전제로 구성했습니다.
행사 전 쿠팡 검색 결과에서 입수량, 개별포장 여부와 최종 가격을 확인하세요.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

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
