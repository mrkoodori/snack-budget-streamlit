from __future__ import annotations

import csv
import io

import pandas as pd
import streamlit as st

from snack_recommender import (
    AGE_GROUPS,
    BEVERAGE_MODES,
    HEADCOUNT_RANGES,
    Recommendation,
    build_recommendation,
    recommendation_to_markdown,
)

st.set_page_config(
    page_title="예산 맞춤형 교육용 다과 추천",
    page_icon="🍪",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
        .block-container {
            max-width: 1180px;
            padding-top: 2.1rem;
            padding-bottom: 3rem;
        }
        .hero {
            padding: 1.55rem 1.7rem;
            border-radius: 18px;
            background: linear-gradient(135deg, #fff7ed 0%, #fffbeb 55%, #f0fdf4 100%);
            border: 1px solid #fed7aa;
            margin-bottom: 1.25rem;
        }
        .hero h1 {
            margin: 0 0 .45rem 0;
            font-size: clamp(1.75rem, 4vw, 2.55rem);
            line-height: 1.18;
        }
        .hero p {
            margin: 0;
            color: #4b5563;
            line-height: 1.7;
        }
        .soft-card {
            padding: 1rem 1.1rem;
            border-radius: 14px;
            background: #fafafa;
            border: 1px solid #e5e7eb;
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
        .stAlert {
            border-radius: 12px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <h1>🍪 예산 맞춤형 교육용 다과 추천</h1>
        <p>
            1인당 최대 5,000원 안에서 교육·워크숍·세미나에 나눠주기 쉬운
            가성비 좋은 낱개포장 과자와 음료를 추천합니다.
            구매 수량, 예산 배분, 가격 오차범위, 쿠팡 검색 링크까지 한 번에 확인하세요.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.form("recommendation_form", border=True):
    st.subheader("조건 입력")
    st.caption("기본 입력은 3개입니다. 세부 조건은 ‘고급 설정’에서 조정할 수 있습니다.")

    c1, c2, c3 = st.columns(3)
    with c1:
        headcount_range = st.selectbox(
            "1. 인원수",
            options=list(HEADCOUNT_RANGES.keys()),
            index=2,
            help="구간 선택 시 구간의 상한 인원을 기준으로 계산합니다.",
        )
    with c2:
        beverage_mode = st.selectbox(
            "2. 음료 포함 여부",
            options=BEVERAGE_MODES,
            index=0,
        )
    with c3:
        age_group = st.selectbox(
            "3. 주 연령대",
            options=AGE_GROUPS,
            index=4,
        )

    with st.expander("고급 설정", expanded=False):
        a1, a2, a3 = st.columns(3)
        with a1:
            exact_headcount_enabled = st.toggle(
                "정확한 인원수 직접 입력",
                value=False,
                help="끄면 선택한 구간의 상한 인원을 사용합니다.",
            )
            exact_headcount = st.number_input(
                "정확한 인원수",
                min_value=1,
                max_value=100,
                value=30,
                step=1,
                disabled=not exact_headcount_enabled,
            )
        with a2:
            per_person_budget = st.slider(
                "1인 예산 상한",
                min_value=3_500,
                max_value=5_000,
                value=5_000,
                step=100,
                format="%d원",
            )
            spare_rate = st.slider(
                "다과 여유 수량",
                min_value=10,
                max_value=20,
                value=15,
                step=1,
                format="%d%%",
            )
        with a3:
            duration = st.selectbox(
                "교육 시간",
                options=("2시간 이하", "2~4시간", "4시간 초과"),
                index=1,
                help="4시간 초과 시 음료 수량을 약 20% 늘립니다.",
            )
            price_error_rate = st.select_slider(
                "가격 오차범위",
                options=(10, 12, 15),
                value=15,
                format_func=lambda value: f"±{value}%",
            )

    submitted = st.form_submit_button(
        "맞춤 구성 추천받기",
        type="primary",
        width="stretch",
    )

if submitted:
    basis_headcount = (
        int(exact_headcount)
        if exact_headcount_enabled
        else HEADCOUNT_RANGES[headcount_range]
    )

    try:
        st.session_state["recommendation"] = build_recommendation(
            headcount=basis_headcount,
            beverage_mode=beverage_mode,
            age_group=age_group,
            per_person_budget=int(per_person_budget),
            spare_rate=int(spare_rate),
            duration=duration,
            price_error_rate=price_error_rate / 100,
        )
    except (ValueError, RuntimeError) as error:
        st.error(str(error))

result: Recommendation | None = st.session_state.get("recommendation")

if result is None:
    st.info(
        "기본값은 30명, 음료 포함, 연령대 혼합, 1인당 최대 5,000원입니다. "
        "조건을 선택한 뒤 추천 버튼을 눌러 주세요."
    )
    st.stop()

st.divider()

st.header("1. 추천 조건 요약")
summary_cols = st.columns(4)
summary_cols[0].metric("기준 인원", f"{result.headcount:,}명")
summary_cols[1].metric("1인 예산 상한", f"{result.per_person_budget:,}원")
summary_cols[2].metric("총예산 상한", f"{result.budget_cap:,}원")
summary_cols[3].metric("예상 1인 비용", f"{result.estimated_total / result.headcount:,.0f}원")

st.markdown(
    f"""
    <div class="soft-card">
        <b>음료 구성</b> · {result.beverage_mode}<br>
        <b>주 연령대</b> · {result.age_group}<br>
        <b>추천 방향</b> · 가성비 중심, 대중 과자, 낱개포장 또는 개별포장, 교육용 대량 배포 구성<br>
        <b>수량 기준</b> · 다과 {result.spare_rate}% 여유, 교육 시간 {result.duration}
    </div>
    """,
    unsafe_allow_html=True,
)

st.header("2. 예산 배분")
budget_cols = st.columns(4)
budget_cols[0].metric("음료 예상 예산", f"{result.drink_total:,}원")
budget_cols[1].metric("다과 예상 예산", f"{result.snack_total:,}원")
budget_cols[2].metric("전체 예상 합계", f"{result.estimated_total:,}원")
budget_cols[3].metric("예비 예산", f"{result.reserve:,}원")

status_text = "초과하지 않음" if result.estimated_total <= result.budget_cap else "초과"
st.write(
    f"가격 오차범위: **약 {result.low_total:,}~{result.high_total:,}원** · "
    f"총예산 초과 여부: **{status_text}**"
)

for warning in result.warnings:
    st.warning(warning)

st.header("3. 최종 추천 구성")
table_rows = []
for row in result.rows:
    table_rows.append(
        {
            "항목": row.category,
            "추천 품목": row.product_name,
            "권장 수량": f"{row.purchased_units}개",
            "구매 묶음": row.pack_description,
            "예상 단가": row.estimated_unit_price,
            "예상 금액": row.estimated_amount,
            "가격 오차범위": f"{row.low_amount:,}~{row.high_amount:,}원",
            "추천 이유": row.reason,
        }
    )

df = pd.DataFrame(table_rows)
st.dataframe(
    df,
    hide_index=True,
    width="stretch",
    column_config={
        "예상 단가": st.column_config.NumberColumn("예상 단가", format="%d원"),
        "예상 금액": st.column_config.NumberColumn("예상 금액", format="%d원"),
        "추천 이유": st.column_config.TextColumn("추천 이유", width="large"),
        "구매 묶음": st.column_config.TextColumn("구매 묶음", width="medium"),
    },
)

st.caption(
    "예상 단가는 선택된 묶음 조합의 총액을 실제 구매 수량으로 나눈 값입니다. "
    "실제 상품의 입수량과 가격은 검색 결과에서 다시 확인해 주세요."
)

st.header("4. 쿠팡 검색 키워드 및 링크")
st.caption("실제 상품 페이지를 고정하지 않고, 재고와 가격을 비교할 수 있는 쿠팡 검색 링크를 제공합니다.")

for index, row in enumerate(result.rows):
    with st.container(border=True):
        link_col, button_col = st.columns([3, 1])
        with link_col:
            st.markdown(f"**{row.product_name}**")
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

st.header("5. 구매 시 확인사항")
checklist = [
    "낱개포장 또는 개별포장 여부 확인",
    "총 수량이 참석 인원보다 10~20% 많은지 확인",
    "총 구매 금액이 인원수 × 1인 예산을 넘지 않는지 확인",
    "로켓배송 또는 도착 예정일 확인",
    "유통기한 확인",
    "상품 리뷰에서 파손, 녹음, 부스러기, 포장 상태 확인",
    "초콜릿류는 여름철 보관 온도 확인",
    "음료 포함 시 냉장 보관 필요 여부 확인",
    "교육 장소에 보관 공간이 있는지 확인",
    "고급 디저트 위주로 담겨 단가가 올라가지 않았는지 확인",
]
left, right = st.columns(2)
for idx, item in enumerate(checklist):
    target = left if idx % 2 == 0 else right
    target.checkbox(item, value=False, key=f"check_{idx}_{result.estimated_total}")

st.header("결과 저장")
download_1, download_2 = st.columns(2)

csv_buffer = io.StringIO()
writer = csv.DictWriter(csv_buffer, fieldnames=list(df.columns))
writer.writeheader()
writer.writerows(table_rows)
csv_data = "\ufeff" + csv_buffer.getvalue()

with download_1:
    st.download_button(
        "구매 구성표 CSV 다운로드",
        data=csv_data.encode("utf-8-sig"),
        file_name=f"교육용_다과_추천_{result.headcount}명.csv",
        mime="text/csv",
        width="stretch",
    )

with download_2:
    report = recommendation_to_markdown(result)
    st.download_button(
        "전체 추천서 Markdown 다운로드",
        data=report.encode("utf-8"),
        file_name=f"교육용_다과_추천서_{result.headcount}명.md",
        mime="text/markdown",
        width="stretch",
    )

st.divider()
st.markdown(
    """
    <p class="fine-print">
        가격은 추천 계산을 위한 추정치이며 쿠팡의 실시간 가격·재고와 다를 수 있습니다.
        결제 전 상품 수량, 개별포장 여부, 배송일, 유통기한과 최종 금액을 확인하세요.
        이 웹앱은 자동결제, 계정 로그인, 장바구니 자동담기 또는 실제 주문 대행을 하지 않습니다.
    </p>
    """,
    unsafe_allow_html=True,
)
