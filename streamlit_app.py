#######################
# Import libraries
import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import re

#######################
# Page configuration
st.set_page_config(
    page_title="서울시 문화행사 대시보드",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="expanded")

alt.themes.enable("default")

#######################
# CSS styling (KPI 카드 수정)
st.markdown("""
<style>
.kpi-card {
    background-color: #ffffff;
    padding: 12px;
    border-radius: 8px;
    border: 1px solid #ddd;
    box-shadow: 1px 1px 5px rgba(0,0,0,0.1);
    text-align: center;
    margin-bottom: 10px;
}
.kpi-title {
    font-size: 1.2rem;
    font-weight: bold;
    color: #000;
    margin-bottom: 4px;
}
.kpi-value {
    font-size: 1rem;
    color: #333;
}
</style>
""", unsafe_allow_html=True)

#######################
# Load data
df = pd.read_csv(
    "서울시 문화행사 정보.csv",
    encoding="euc-kr",
    encoding_errors="ignore",
    quotechar='"',
    on_bad_lines="skip",
    low_memory=False
)

#######################
# Sidebar
with st.sidebar:
    st.title("서울시 문화행사 대시보드 🎭")

    if "시작일" in df.columns:
        years = sorted(df['시작일'].astype(str).str[:4].unique())
        selected_year = st.selectbox("연도 선택", years)
    else:
        selected_year = None

    gu_list = sorted(df['자치구'].dropna().unique()) if "자치구" in df.columns else []
    selected_gu = st.multiselect("자치구 선택", gu_list, default=[])

    category_list = sorted(df['분류'].dropna().unique()) if "분류" in df.columns else []
    selected_category = st.multiselect("행사 분류 선택", category_list, default=[])

    org_list = sorted(df['기관명'].dropna().unique()) if "기관명" in df.columns else []
    selected_org = st.multiselect("기관 선택", org_list, default=[])

    free_paid = df['유무료'].dropna().unique() if "유무료" in df.columns else []
    selected_fee = st.multiselect("유/무료 선택", free_paid, default=[])

    keyword = st.text_input("행사명/장소 검색", "")

#######################
# 데이터 필터링
df_filtered = df.copy()

if selected_year:
    df_filtered = df_filtered[df_filtered["시작일"].astype(str).str.startswith(str(selected_year))]

if selected_gu:
    df_filtered = df_filtered[df_filtered["자치구"].isin(selected_gu)]

if selected_category:
    df_filtered = df_filtered[df_filtered["분류"].isin(selected_category)]

if selected_org:
    df_filtered = df_filtered[df_filtered["기관명"].isin(selected_org)]

if selected_fee:
    df_filtered = df_filtered[df_filtered["유무료"].isin(selected_fee)]

if keyword:
    df_filtered = df_filtered[
        df_filtered["공연/행사명"].astype(str).str.contains(keyword, case=False, na=False) |
        df_filtered["장소"].astype(str).str.contains(keyword, case=False, na=False)
    ]

#######################
# Dashboard Main Panel
col = st.columns((1.8, 3.6, 2.6), gap='medium')

# ------------------- 컬럼1 -------------------
with col[0]:
    st.subheader("📊 주요 지표 (KPI)")

    total_events = len(df_filtered)
    free_count = (df_filtered["유무료"] == "무료").sum() if "유무료" in df_filtered.columns else 0
    paid_count = (df_filtered["유무료"] == "유료").sum() if "유무료" in df_filtered.columns else 0

    if "이용요금" in df_filtered.columns:
        df_filtered["요금숫자"] = df_filtered["이용요금"].astype(str).apply(
            lambda x: int(re.sub(r"[^0-9]", "", x)) if re.search(r"\d", x) else 0
        )
        avg_fee = df_filtered.loc[df_filtered["요금숫자"] > 0, "요금숫자"].mean()
    else:
        avg_fee = None

    if "기관명" in df_filtered.columns and not df_filtered["기관명"].empty:
        top_org = df_filtered["기관명"].value_counts().idxmax()
        top_org_count = df_filtered["기관명"].value_counts().max()
    else:
        top_org, top_org_count = "정보 없음", 0

    # KPI 카드 2열 레이아웃
    kpi1, kpi2 = st.columns(2)
    with kpi1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">전체 행사 수</div>
            <div class="kpi-value">{total_events:,} 개</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">무료 행사 수</div>
            <div class="kpi-value">{free_count:,} 개</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">유료 행사 수</div>
            <div class="kpi-value">{paid_count:,} 개</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi2:
        if avg_fee:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">평균 요금</div>
                <div class="kpi-value">{int(avg_fee):,} 원</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">평균 요금</div>
                <div class="kpi-value">데이터 없음</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">최다 개최 기관</div>
            <div class="kpi-value">{top_org} ({top_org_count}건)</div>
        </div>
        """, unsafe_allow_html=True)

# ------------------- 컬럼2 -------------------
with col[1]:
    st.subheader("🗺️ 지도 & 행사 분포")

    if "위도(Y좌표)" in df_filtered.columns and "경도(X좌표)" in df_filtered.columns:
        df_filtered["위도(Y좌표)"] = pd.to_numeric(df_filtered["위도(Y좌표)"], errors="coerce")
        df_filtered["경도(X좌표)"] = pd.to_numeric(df_filtered["경도(X좌표)"], errors="coerce")
        map_df = df_filtered.dropna(subset=["위도(Y좌표)", "경도(X좌표)"])

        if not map_df.empty:
            fig_map = px.scatter_mapbox(
                map_df,
                lat="위도(Y좌표)", lon="경도(X좌표)",
                color="유무료" if "유무료" in df_filtered.columns else None,
                hover_name="공연/행사명" if "공연/행사명" in df_filtered.columns else None,
                hover_data=["자치구", "기관명"] if "자치구" in df_filtered.columns and "기관명" in df_filtered.columns else None,
                zoom=10, height=400
            )
            fig_map.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":0,"l":0,"b":0})
            st.plotly_chart(fig_map, use_container_width=True)

    if "시작일" in df_filtered.columns and "자치구" in df_filtered.columns:
        df_filtered["시작일"] = pd.to_datetime(df_filtered["시작일"], errors="coerce")
        df_filtered["월"] = df_filtered["시작일"].dt.month
        heat_df = df_filtered.groupby(["자치구", "월"]).size().reset_index(name="행사수")

        fig_heat = px.density_heatmap(
            heat_df, x="월", y="자치구", z="행사수",
            color_continuous_scale="Blues", title="자치구별 월별 행사 분포", height=400
        )
        st.plotly_chart(fig_heat, use_container_width=True)

# ------------------- 컬럼3 -------------------
with col[2]:
    st.subheader("🏆 Top 리스트 & 상세 정보")

    if "기관명" in df_filtered.columns:
        top_orgs = df_filtered["기관명"].value_counts().head(10).reset_index()
        top_orgs.columns = ["기관명", "행사수"]
        fig_top_org = px.bar(top_orgs, x="행사수", y="기관명",
                             orientation="h", title="Top 10 개최 기관", height=250)
        st.plotly_chart(fig_top_org, use_container_width=True)

    if "장소" in df_filtered.columns:
        top_places = df_filtered["장소"].value_counts().head(10).reset_index()
        top_places.columns = ["장소", "행사수"]
        fig_top_place = px.bar(top_places, x="행사수", y="장소",
                               orientation="h", title="Top 10 행사 장소", height=250)
        st.plotly_chart(fig_top_place, use_container_width=True)

    if "요금숫자" in df_filtered.columns and (df_filtered["요금숫자"] > 0).any():
        fee_df = df_filtered[df_filtered["요금숫자"] > 0]
        fig_fee = px.histogram(fee_df, x="요금숫자", nbins=30,
                               title="행사 요금 분포 (원)", height=250)
        st.plotly_chart(fig_fee, use_container_width=True)

    st.markdown("### 📋 세부 행사 데이터")
    show_cols = [col for col in ["공연/행사명", "자치구", "기관명", "장소", "이용대상", "이용요금", "시작일", "종료일"] if col in df_filtered.columns]
    if show_cols:
        st.dataframe(df_filtered[show_cols].head(30), height=300)

