from __future__ import annotations

import csv
import io

import pandas as pd
import streamlit as st

from catalog import DRINK_OPTIONS, PARTICIPANT_PROFILES
from snack_recommender import (
    COUPANG_HOME_URL,
    DAILY_BUDGET,
    Recommendation,
    build_recommendation,
    recommendation_to_markdown,
    snack_pool_size_for_days,
)

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
            정확한 인원수와 교육일수로 계산하며, <b>1인 1일 10,000원</b> 상한 안에서
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

    c1, c2, c3 = st.columns([1, 1, 1.35])
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
        participant_profile = st.selectbox(
            "3. 참가자 성향",
            options=PARTICIPANT_PROFILES,
            index=2,
            help="달콤한 구성, 담백한 균형 구성, 두 성향의 혼합 중 하나를 선택합니다.",
        )

    st.markdown("**4. 음료 포함 항목**")
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

    preview_cap = int(headcount) * int(education_days) * DAILY_BUDGET
    preview_pool = snack_pool_size_for_days(int(education_days))
    st.info(
        f"총예산 상한: {int(headcount):,}명 × {int(education_days)}일 × "
        f"{DAILY_BUDGET:,}원 = {preview_cap:,}원 · 프리미엄 다과 후보 풀 {preview_pool}종"
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
summary_cols[3].metric("다과 후보 풀", f"{result.snack_pool_size}종")
summary_cols[4].metric("총예산 상한", f"{result.budget_cap:,}원")

estimated_per_person_day = result.estimated_total / result.person_days
st.markdown(
    f"""
    <div class="soft-card">
        <b>참가자 성향</b> · {result.participant_profile}<br>
        <b>음료 선택</b> · {result.drink_summary}<br>
        <b>다과 제공 기준</b> · 하루 1인 평균 {result.snacks_per_person_day}개,
        전체 {result.snack_spare_rate}% 여유<br>
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

st.header("2. 프리미엄 다과 후보 풀")
st.caption(
    "요청하신 예시를 적용해 1일 8종, 2일 10종, 3일 12종, 4일 14종, 5일 16종으로 후보 풀을 구성합니다. "
    "실제 구매안은 이 풀에서 매일 3종씩 순환 선정합니다."
)
pool_rows = [
    {
        "순위": item.rank,
        "후보 품목": item.product_name,
        "프리미엄 구분": item.premium_label,
        "기준 개당 추정가": item.reference_unit_price,
        "추천 이유": item.reason,
        "쿠팡 검색": item.search_url,
    }
    for item in result.snack_pool
]
pool_df = pd.DataFrame(pool_rows)
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
        "다과 3종": ", ".join(plan.snack_names),
        "총 다과 수량": plan.snack_units,
        "음료 구성": ", ".join(plan.drink_names) or "음료 없음",
        "배포 기준": plan.distribution_note,
    }
    for plan in result.daily_plans
]
daily_df = pd.DataFrame(daily_rows)
st.dataframe(
    daily_df,
    hide_index=True,
    width="stretch",
    column_config={
        "다과 3종": st.column_config.TextColumn("다과 3종", width="large"),
        "총 다과 수량": st.column_config.NumberColumn("총 다과 수량", format="%d개"),
        "음료 구성": st.column_config.TextColumn("음료 구성", width="large"),
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
df = pd.DataFrame(table_rows)
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
writer = csv.DictWriter(csv_buffer, fieldnames=list(df.columns))
writer.writeheader()
writer.writerows(table_rows)
csv_data = "\ufeff" + csv_buffer.getvalue()

daily_csv_buffer = io.StringIO()
daily_writer = csv.DictWriter(daily_csv_buffer, fieldnames=list(daily_df.columns))
daily_writer.writeheader()
daily_writer.writerows(daily_rows)
daily_csv_data = "\ufeff" + daily_csv_buffer.getvalue()

pool_csv_buffer = io.StringIO()
pool_writer = csv.DictWriter(pool_csv_buffer, fieldnames=list(pool_df.columns))
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
        "후보 풀 CSV",
        data=pool_csv_data.encode("utf-8-sig"),
        file_name=f"프리미엄_다과_후보풀_{result.education_days}일.csv",
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
