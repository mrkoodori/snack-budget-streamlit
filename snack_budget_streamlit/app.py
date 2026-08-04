from __future__ import annotations

import csv
import io

import pandas as pd
import streamlit as st

from snack_recommender import (
    AGE_GROUPS,
    BEVERAGE_MODES,
    HEADCOUNT_RANGES,
    TASTE_PROFILES,
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
            max-width: 1220px;
            padding-top: 2rem;
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
        .profile-card {
            padding: 1rem 1.1rem;
            border-radius: 14px;
            background: #f8fafc;
            border-left: 4px solid #94a3b8;
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
            교육시간 대신 <b>교육일수</b>를 기준으로 계산합니다.
            총예산 상한은 <b>인원수 × 교육일수 × 1인 1일 예산</b>이며,
            1인 1일 예산은 최대 <b>10,000원</b>까지 설정할 수 있습니다.
            1~5일 장기차수에는 일자별로 다과 구성을 순환해 추천합니다.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.form("recommendation_form", border=True):
    st.subheader("조건 입력")
    st.caption("기본값은 30명, 1일, 음료 포함, 연령대 혼합, 1인 1일 최대 10,000원입니다.")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        headcount_range = st.selectbox(
            "1. 인원수",
            options=list(HEADCOUNT_RANGES.keys()),
            index=2,
            help="구간 선택 시 구간의 상한 인원을 기준으로 계산합니다.",
        )
    with c2:
        education_days = st.number_input(
            "2. 교육일수",
            min_value=1,
            max_value=5,
            value=1,
            step=1,
            help="최소 1일, 최대 5일입니다. 매일 같은 인원이 참석하는 기준입니다.",
        )
    with c3:
        beverage_mode = st.selectbox(
            "3. 음료 포함 여부",
            options=BEVERAGE_MODES,
            index=0,
        )
    with c4:
        age_group = st.selectbox(
            "4. 주 연령대",
            options=AGE_GROUPS,
            index=4,
            help="연령대는 선호를 단정하지 않고 추천 우선순위를 조정하는 값입니다.",
        )

    with st.expander("고급 설정", expanded=False):
        a1, a2, a3, a4 = st.columns(4)
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
            per_person_daily_budget = st.slider(
                "1인 1일 예산 상한",
                min_value=3_500,
                max_value=10_000,
                value=10_000,
                step=100,
                format="%d원",
                help="최대 10,000원/인·일의 지출 상한입니다. 예산을 억지로 모두 사용하지 않으며, 교육일수가 늘어나면 누적 상한과 총예산이 자동 증가합니다.",
            )
        with a3:
            spare_rate = st.slider(
                "다과 여유 수량",
                min_value=10,
                max_value=20,
                value=15,
                step=1,
                format="%d%%",
            )
            price_error_rate = st.select_slider(
                "가격 오차범위",
                options=(10, 12, 15),
                value=15,
                format_func=lambda value: f"±{value}%",
            )
        with a4:
            taste_profile = st.selectbox(
                "구성 성향",
                options=TASTE_PROFILES,
                index=0,
                help="연령대 추천을 그대로 쓰거나 달콤함·담백함·기본형으로 조정할 수 있습니다.",
            )

    preview_headcount = (
        int(exact_headcount)
        if exact_headcount_enabled
        else HEADCOUNT_RANGES[headcount_range]
    )
    preview_cap = preview_headcount * int(education_days) * int(per_person_daily_budget)
    st.caption(
        f"현재 총예산 상한 미리보기: {preview_headcount}명 × {int(education_days)}일 × "
        f"{int(per_person_daily_budget):,}원 = {preview_cap:,}원"
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
            education_days=int(education_days),
            beverage_mode=beverage_mode,
            age_group=age_group,
            taste_profile=taste_profile,
            per_person_daily_budget=int(per_person_daily_budget),
            spare_rate=int(spare_rate),
            price_error_rate=price_error_rate / 100,
        )
    except (ValueError, RuntimeError) as error:
        st.error(str(error))

result: Recommendation | None = st.session_state.get("recommendation")

if result is None:
    st.info(
        "조건을 선택한 뒤 추천 버튼을 눌러 주세요. 교육일수는 1~5일이며, "
        "총예산은 인원수 × 교육일수 × 1인 1일 예산으로 계산됩니다."
    )
    st.stop()

st.divider()
st.header("1. 추천 조건 요약")
summary_cols = st.columns(5)
summary_cols[0].metric("기준 인원", f"{result.headcount:,}명")
summary_cols[1].metric("교육일수", f"{result.education_days}일")
summary_cols[2].metric("총 제공 기준", f"{result.person_days:,}인일")
summary_cols[3].metric("1인 누적 상한", f"{result.cumulative_per_person_cap:,}원")
summary_cols[4].metric("총예산 상한", f"{result.budget_cap:,}원")

estimated_per_person_day = result.estimated_total / result.person_days
st.markdown(
    f"""
    <div class="soft-card">
        <b>1인 1일 예산 상한</b> · {result.per_person_daily_budget:,}원<br>
        <b>예상 1인 1일 비용</b> · {estimated_per_person_day:,.0f}원<br>
        <b>음료 구성</b> · {result.beverage_mode}<br>
        <b>주 연령대</b> · {result.age_group}<br>
        <b>구성 성향</b> · {result.taste_profile}<br>
        <b>수량 기준</b> · 다과 일자별 {result.spare_rate}% 여유, 음료 인원수 × 교육일수 기준
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="profile-card">
        <b>연령대별 추천 차이</b><br>
        {result.age_profile_description}<br><br>
        연령대는 특정 선호를 단정하는 값이 아니라, 추천 품목의 우선순위를 조정하는 참고값입니다.
    </div>
    """,
    unsafe_allow_html=True,
)

st.header("2. 일자별 운영안")
daily_rows = []
for plan in result.daily_plans:
    daily_rows.append(
        {
            "교육일": f"{plan.day}일차",
            "다과 구성": ", ".join(plan.snack_names) or "다과 없음",
            "음료 구성": ", ".join(plan.drink_names) or "음료 없음",
            "배포 기준": plan.distribution_note,
        }
    )
daily_df = pd.DataFrame(daily_rows)
st.dataframe(
    daily_df,
    hide_index=True,
    width="stretch",
    column_config={
        "다과 구성": st.column_config.TextColumn("다과 구성", width="large"),
        "음료 구성": st.column_config.TextColumn("음료 구성", width="large"),
        "배포 기준": st.column_config.TextColumn("배포 기준", width="large"),
    },
)
st.caption(
    "장기차수는 대용량 구매 효율을 유지하면서 조합을 순환합니다. "
    "일자별 분배 상자나 라벨을 미리 나누면 현장 운영이 편해집니다."
)

st.header("3. 예산 배분")
budget_cols = st.columns(5)
budget_cols[0].metric("음료 예상 예산", f"{result.drink_total:,}원")
budget_cols[1].metric("다과 예상 예산", f"{result.snack_total:,}원")
budget_cols[2].metric("전체 예상 합계", f"{result.estimated_total:,}원")
budget_cols[3].metric("예비 예산", f"{result.reserve:,}원")
budget_cols[4].metric("예상 1인 1일", f"{estimated_per_person_day:,.0f}원")

status_text = "초과하지 않음" if result.estimated_total <= result.budget_cap else "초과"
st.write(
    f"가격 오차범위: **약 {result.low_total:,}~{result.high_total:,}원** · "
    f"총예산 초과 여부: **{status_text}**"
)
for warning in result.warnings:
    st.warning(warning)

st.header("4. 최종 구매 구성")
table_rows = []
for row in result.rows:
    table_rows.append(
        {
            "항목": row.category,
            "추천 품목": row.product_name,
            "제공일": ", ".join(f"{day}일차" for day in row.service_days),
            "목표 수량": row.target_units,
            "권장 구매 수량": row.purchased_units,
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
        "목표 수량": st.column_config.NumberColumn("목표 수량", format="%d개"),
        "권장 구매 수량": st.column_config.NumberColumn("권장 구매 수량", format="%d개"),
        "예상 단가": st.column_config.NumberColumn("예상 단가", format="%d원"),
        "예상 금액": st.column_config.NumberColumn("예상 금액", format="%d원"),
        "추천 이유": st.column_config.TextColumn("추천 이유", width="large"),
        "구매 묶음": st.column_config.TextColumn("구매 묶음", width="medium"),
    },
)
st.caption(
    "목표 수량은 일자별 배포량을 합산한 값이며, 권장 구매 수량은 실제 묶음 조합으로 확보되는 수량입니다."
)

st.header("5. 쿠팡 검색 키워드 및 링크")
st.caption("실제 상품 페이지를 고정하지 않고 재고와 가격을 비교할 수 있는 쿠팡 검색 링크를 제공합니다.")
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

st.header("6. 구매 시 확인사항")
checklist = [
    "낱개포장 또는 개별포장 여부 확인",
    "일자별 다과 수량이 참석 인원보다 10~20% 많은지 확인",
    "총 구매 금액이 인원수 × 교육일수 × 1인 1일 예산을 넘지 않는지 확인",
    "로켓배송 또는 도착 예정일 확인",
    "유통기한과 장기차수 보관 가능 기간 확인",
    "상품 리뷰에서 파손, 녹음, 부스러기, 포장 상태 확인",
    "초콜릿류는 여름철 보관 온도 확인",
    "음료 포함 시 냉장 보관 필요 여부 확인",
    "교육 장소의 보관 공간과 일자별 분배 방법 확인",
    "고급 디저트 위주로 담겨 단가가 올라가지 않았는지 확인",
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
download_1, download_2, download_3 = st.columns(3)

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

with download_1:
    st.download_button(
        "구매 구성표 CSV",
        data=csv_data.encode("utf-8-sig"),
        file_name=f"교육용_다과_구매구성_{result.headcount}명_{result.education_days}일.csv",
        mime="text/csv",
        width="stretch",
    )
with download_2:
    st.download_button(
        "일자별 운영안 CSV",
        data=daily_csv_data.encode("utf-8-sig"),
        file_name=f"교육용_다과_일자별운영_{result.headcount}명_{result.education_days}일.csv",
        mime="text/csv",
        width="stretch",
    )
with download_3:
    report = recommendation_to_markdown(result)
    st.download_button(
        "전체 추천서 Markdown",
        data=report.encode("utf-8"),
        file_name=f"교육용_다과_추천서_{result.headcount}명_{result.education_days}일.md",
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
