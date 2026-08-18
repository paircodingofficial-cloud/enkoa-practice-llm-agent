# 멀티페이지 데모: 데이터 대시보드 페이지 (펭귄)
import os

# [제공 코드] pandas/Streamlit 이 쓰는 Arrow 의 메모리 할당기를 표준(system)으로 고정.
# 기본 할당기(mimalloc)는 macOS 에서 화면 재실행 시 앱이 죽는 문제가 있어 미리 막아 둔다.
# 반드시 pandas 를 import 하기 전에 설정해야 효과가 있다.
os.environ.setdefault("ARROW_DEFAULT_MEMORY_POOL", "system")

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import seaborn as sns
import streamlit as st

# [제공 코드] 이 페이지만 따로 실행해도 경로가 맞도록 프로젝트 루트를 찾습니다.
PROJECT_ROOT = next(
    (p for p in Path(__file__).resolve().parents if (p / "core").is_dir()),
    Path(__file__).resolve().parent,
)
DATA_DIR = PROJECT_ROOT / "data"
sys.path.insert(0, str(PROJECT_ROOT))
from core.fonts import apply_korean_font

apply_korean_font()

st.title("📊 펭귄 데이터 대시보드")


@st.cache_data
def load_penguins():
    """펭귄 데이터를 읽어 돌려준다(한 번만 읽고 캐싱)."""
    return pd.read_csv(DATA_DIR / "penguins.csv")


df = load_penguins()

# 사이드바 필터: 잡아 둔 자리에 그리면 푸터 위에 들어간다.
# main.py 로 열면 main.py 가 잡아 둔 자리에, 이 파일만 단독 실행하면 사이드바에 바로 그린다.
slot = st.session_state.get("sidebar_slot")
with (slot.container() if slot else st.sidebar):
    st.header("필터")
    species = st.multiselect(
        "종", sorted(df["species"].dropna().unique()),
        default=sorted(df["species"].dropna().unique()),
    )
    islands = st.multiselect(
        "서식지", sorted(df["island"].dropna().unique()),
        default=sorted(df["island"].dropna().unique()),
    )

filtered = df[df["species"].isin(species) & df["island"].isin(islands)]

# 지표
c1, c2, c3 = st.columns(3)
c1.metric("펭귄 수", f"{len(filtered)}마리")
c2.metric("평균 체중", f"{filtered['body_mass_g'].mean():.0f} g" if len(filtered) else "-")
c3.metric("평균 날개", f"{filtered['flipper_length_mm'].mean():.0f} mm" if len(filtered) else "-")

st.divider()

# 차트: plotly(대시보드) + seaborn(분포)
tab1, tab2, tab3 = st.tabs(["종별 수", "체중 분포", "데이터"])
with tab1:
    # value_counts 는 Series 다. px 에 넘기려면 열 이름이 있는 DataFrame 으로 바꾼다.
    counts = filtered["species"].value_counts().rename_axis("종").reset_index(name="건수")
    st.plotly_chart(px.bar(counts, x="종", y="건수", color="종"), width="stretch")
with tab2:
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.boxplot(data=filtered, x="species", y="body_mass_g", ax=ax)
    ax.set_xlabel("종")
    ax.set_ylabel("체중(g)")
    st.pyplot(fig)
    plt.close(fig)
with tab3:
    st.dataframe(filtered, width="stretch")
