"""교육용 다과 추천에 사용하는 추정 상품 카탈로그.

가격은 실시간 판매가가 아니라 추천 계산용 기준값입니다.
운영 시 ``pack_options``를 월 1회 또는 행사 전에 점검해 주세요.
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


PRODUCTS: dict[str, Product] = {
    # 다과
    "butter_waffle": Product(
        "butter_waffle", "버터와플", "다과", "버터와플 개별포장 대용량",
        "호불호가 적고 손에 잘 묻지 않아 교육용 배포에 적합",
        (PackOption(1, 550), PackOption(4, 2_200), PackOption(12, 5_500), PackOption(36, 13_500)),
    ),
    "monshell": Product(
        "monshell", "몽쉘", "다과", "몽쉘 대용량 개별포장",
        "익숙한 초코 과자로 만족도가 높고 낱개 배포가 쉬움",
        (PackOption(1, 700), PackOption(6, 4_300), PackOption(12, 7_400), PackOption(24, 12_500)),
    ),
    "custard": Product(
        "custard", "카스타드", "다과", "카스타드 대용량 개별포장",
        "부드럽고 연령대가 섞인 교육에서도 무난한 선택",
        (PackOption(1, 650), PackOption(6, 4_000), PackOption(12, 6_800), PackOption(24, 11_500)),
    ),
    "chamssal": Product(
        "chamssal", "참쌀설병", "다과", "참쌀설병 대용량 개별포장",
        "단맛 위주 구성을 보완하고 중장년층이 포함된 교육에도 무난함",
        (PackOption(1, 550), PackOption(6, 3_400), PackOption(15, 7_400), PackOption(30, 13_000)),
    ),
    "mini_yakgwa": Product(
        "mini_yakgwa", "미니약과", "다과", "미니약과 개별포장 대용량",
        "작고 개별포장되어 배포가 쉽고 차·커피와 잘 어울림",
        (PackOption(1, 450), PackOption(10, 4_000), PackOption(25, 7_500), PackOption(50, 12_500)),
    ),
    "binch": Product(
        "binch", "빈츠", "다과", "빈츠 대용량 개별포장",
        "깔끔한 초콜릿 비스킷으로 달콤한 구성을 원하는 교육에 적합",
        (PackOption(1, 700), PackOption(6, 4_200), PackOption(12, 7_500), PackOption(24, 13_500)),
    ),
    "kukudas": Product(
        "kukudas", "쿠크다스", "다과", "쿠크다스 대용량 개별포장",
        "가볍고 익숙한 과자로 책상 위 개별 배포에 적합",
        (PackOption(1, 500), PackOption(10, 4_300), PackOption(30, 11_500), PackOption(48, 16_500)),
    ),
    "grain_bar": Product(
        "grain_bar", "곡물바", "다과", "곡물바 30개 개별포장",
        "장기 교육에서 포만감을 보완하고 지나치게 달지 않음",
        (PackOption(1, 800), PackOption(6, 5_000), PackOption(12, 9_200), PackOption(30, 19_500)),
    ),
    "nuts": Product(
        "nuts", "견과류 소포장", "다과", "견과류 소포장 30개",
        "단 과자 비중을 낮추고 실용적인 간식 구성을 만듦",
        (PackOption(1, 1_100), PackOption(10, 10_500), PackOption(30, 26_000)),
    ),
    "free_time": Product(
        "free_time", "자유시간 미니", "다과", "자유시간 미니 대용량",
        "작은 크기로 배포가 편하고 달콤한 바 형태 간식을 선호할 때 적합",
        (PackOption(1, 750), PackOption(10, 6_500), PackOption(18, 10_500), PackOption(36, 18_000)),
    ),
    "ohyes": Product(
        "ohyes", "오예스", "다과", "오예스 대용량 개별포장",
        "익숙하고 부드러운 초코 과자로 교육용 만족도가 높음",
        (PackOption(1, 750), PackOption(6, 4_500), PackOption(12, 7_800), PackOption(28, 15_500)),
    ),
    "chocopie": Product(
        "chocopie", "초코파이", "다과", "초코파이 대용량 개별포장",
        "대중적이고 단가가 안정적인 대표 교육용 간식",
        (PackOption(1, 600), PackOption(6, 3_900), PackOption(12, 6_500), PackOption(39, 14_500)),
    ),
    "french_pie": Product(
        "french_pie", "후렌치파이", "다과", "후렌치파이 대용량 개별포장",
        "과일 맛을 더해 초코 위주 구성을 피할 수 있음",
        (PackOption(1, 500), PackOption(10, 4_200), PackOption(30, 11_000)),
    ),
    "sand": Product(
        "sand", "크라운산도", "다과", "크라운산도 대용량 개별포장",
        "익숙한 샌드형 과자로 가격 부담이 낮고 배포가 쉬움",
        (PackOption(1, 550), PackOption(6, 3_400), PackOption(24, 11_000)),
    ),
    # 음료
    "water": Product(
        "water", "생수 500ml", "음료", "생수 500ml 대량",
        "모든 참석자에게 매일 기본으로 제공하기 좋고 보관이 간편",
        (PackOption(1, 500), PackOption(6, 3_300), PackOption(20, 7_500), PackOption(40, 12_500)),
    ),
    "coffee_can": Product(
        "coffee_can", "캔커피", "음료", "캔커피 대량 세트",
        "상온 배포가 쉽고 교육 중 간편하게 마시기 좋음",
        (PackOption(1, 1_100), PackOption(6, 6_500), PackOption(10, 9_800), PackOption(30, 25_500)),
    ),
    "coffee_bottle": Product(
        "coffee_bottle", "병커피", "음료", "병커피 대량 세트",
        "깔끔한 인상과 휴대성을 갖춘 실무 교육용 음료",
        (PackOption(1, 1_500), PackOption(6, 8_500), PackOption(10, 13_500), PackOption(20, 27_000)),
    ),
    "juice": Product(
        "juice", "과일주스", "음료", "주스 30개 세트",
        "커피를 마시지 않는 참석자를 위한 무난한 대안",
        (PackOption(1, 900), PackOption(6, 5_200), PackOption(10, 8_200), PackOption(24, 18_000)),
    ),
    "tea": Product(
        "tea", "차음료", "음료", "차음료 대량 세트",
        "단맛이 과하지 않고 다양한 연령대에 폭넓게 제공 가능",
        (PackOption(1, 1_200), PackOption(6, 6_800), PackOption(10, 10_800), PackOption(20, 21_000)),
    ),
    "soy_milk": Product(
        "soy_milk", "두유", "음료", "두유 대량 세트",
        "포만감을 보완하며 담백한 음료를 원하는 교육에 적합",
        (PackOption(1, 1_000), PackOption(6, 5_800), PackOption(16, 14_500), PackOption(24, 20_000)),
    ),
}


AGE_SNACK_PRIORITY: dict[str, tuple[str, ...]] = {
    "20~30대 중심": ("monshell", "binch", "kukudas", "free_time", "grain_bar", "french_pie"),
    "30~40대 중심": ("butter_waffle", "monshell", "custard", "binch", "grain_bar", "nuts"),
    "40~50대 중심": ("butter_waffle", "custard", "chamssal", "mini_yakgwa", "grain_bar", "nuts"),
    "50대 이상 포함": ("custard", "chamssal", "mini_yakgwa", "butter_waffle", "grain_bar", "nuts"),
    "연령대 혼합": ("butter_waffle", "monshell", "custard", "chamssal", "mini_yakgwa", "kukudas"),
}

AGE_DRINK_PRIORITY: dict[str, tuple[str, str]] = {
    "20~30대 중심": ("coffee_can", "juice"),
    "30~40대 중심": ("coffee_bottle", "tea"),
    "40~50대 중심": ("tea", "coffee_bottle"),
    "50대 이상 포함": ("soy_milk", "tea"),
    "연령대 혼합": ("coffee_can", "juice"),
}

AGE_PROFILE_DESCRIPTIONS: dict[str, str] = {
    "20~30대 중심": (
        "달콤하고 간편한 구성의 비중을 높입니다. 초콜릿·쿠키·바류와 "
        "캔커피·주스를 우선하되, 선호를 단정하지 않고 기본 추천 가중치로만 사용합니다."
    ),
    "30~40대 중심": (
        "달콤한 과자와 담백한 간식의 균형을 맞춥니다. 버터와플·카스타드·곡물바와 "
        "병커피·차음료를 함께 고려합니다."
    ),
    "40~50대 중심": (
        "너무 단 제품에 치우치지 않도록 담백한 과자·곡물바·견과류 비중을 높이고 "
        "차음료·병커피를 우선합니다."
    ),
    "50대 이상 포함": (
        "부드럽고 익숙한 과자와 담백한 음료를 우선합니다. 지나치게 딱딱하거나 "
        "단맛이 강한 품목만으로 구성하지 않습니다."
    ),
    "연령대 혼합": (
        "버터와플·몽쉘·카스타드·참쌀설병처럼 호불호가 적은 품목을 섞고 "
        "생수와 보조 음료를 무난하게 배분합니다."
    ),
}

TASTE_SNACK_PRIORITY: dict[str, tuple[str, ...]] = {
    "연령대 추천 자동": (),
    "달콤하고 간편한 구성": ("monshell", "binch", "kukudas", "free_time", "ohyes", "french_pie"),
    "담백함을 더한 균형 구성": ("butter_waffle", "custard", "chamssal", "mini_yakgwa", "grain_bar", "nuts"),
    "호불호 적은 기본 구성": ("butter_waffle", "monshell", "custard", "chamssal", "mini_yakgwa", "kukudas"),
}
