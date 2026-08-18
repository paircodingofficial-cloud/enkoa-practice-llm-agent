# 실행: uv run streamlit run 교안_01_기초UI/04_레이아웃과_차트.py
#
# 교안 01: 레이아웃과 차트 (대시보드의 뼈대)
# 화면을 사이드바·열·탭으로 나누고, 데이터를 차트로 그립니다.

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

PROJECT_ROOT = next(
    (p for p in Path(__file__).resolve().parents if (p / "core").is_dir()),
    Path(__file__).resolve().parent,
)
DATA_DIR = PROJECT_ROOT / "data"
sys.path.insert(0, str(PROJECT_ROOT))
from core.fonts import apply_korean_font

apply_korean_font()

st.set_page_config(page_title="레이아웃과 차트", layout="wide")
st.title("📗 레이아웃과 차트")
st.caption("펭귄·항공 데이터로 화면 나누기와 그래프 그리기를 익힙니다.")

df = pd.read_csv(DATA_DIR / "penguins.csv")
flights = pd.read_csv(DATA_DIR / "flights.csv")

st.divider()

# =============================================================================
st.header("1. 사이드바: st.sidebar")
st.markdown("필터·설정은 보통 **사이드바**(왼쪽 패널)에 둡니다. `with st.sidebar:` 블록 안에 위젯을 넣습니다.")

st.code(
    '''with st.sidebar:
    st.header("필터")
    species = st.multiselect("종", df["species"].unique(),
                             default=list(df["species"].unique()))
filtered = df[df["species"].isin(species)]''',
    language="python",
)
with st.sidebar:
    st.header("필터")
    species = st.multiselect(
        "종", df["species"].unique(), default=list(df["species"].unique())
    )
filtered = df[df["species"].isin(species)]
st.caption("▼ 왼쪽 사이드바에서 종을 고르면 아래 표가 바뀝니다")
st.write("선택된 펭귄 수:", len(filtered))

# 🖐️ 직접 해보기: 사이드바에서 종을 하나만 남겨 보고, 아래 숫자와 표가 함께 바뀌는지 확인해 보세요.
#               그 다음 multiselect 의 default 에서 한 종을 빼면, 앱을 열었을 때의 첫 화면이 어떻게 달라지나요?

st.divider()

# =============================================================================
st.header("2. 열 나누기: st.columns")
st.markdown("`st.columns(n)` 은 가로로 n칸을 만듭니다. 지표를 나란히 놓을 때 자주 씁니다.")

st.code(
    '''c1, c2, c3 = st.columns(3)
c1.metric("펭귄 수", f"{len(filtered)}마리")
c2.metric("평균 체중", f"{filtered['body_mass_g'].mean():.0f} g")
c3.metric("종 수", filtered["species"].nunique())''',
    language="python",
)
st.caption("▼ 실제 실행 결과")
c1, c2, c3 = st.columns(3)
c1.metric("펭귄 수", f"{len(filtered)}마리")
c2.metric("평균 체중", f"{filtered['body_mass_g'].mean():.0f} g")
c3.metric("종 수", filtered["species"].nunique())

# 🖐️ 직접 해보기: st.columns 의 개수를 2로 바꾸고 지표를 두 개만 남겨 보세요.
#               칸 수보다 많은 지표를 넣으려 하면 어떤 오류가 나는지도 한 번 보고 되돌리세요.

st.divider()

# =============================================================================
st.header("3. 탭·펼침: st.tabs, st.expander")
st.markdown("`st.tabs` 는 내용을 탭으로 전환하고, `st.expander` 는 접었다 펼 수 있는 영역을 만듭니다.")

st.code(
    '''tab1, tab2 = st.tabs(["표", "설명"])
with tab1:
    st.dataframe(filtered.head())
with tab2:
    st.write("펭귄 3종의 서식지·치수 데이터입니다.")

with st.expander("자세히 보기"):
    st.write("expander 안의 내용은 기본으로 접혀 있습니다.")''',
    language="python",
)
st.caption("▼ 실제 실행 결과")
tab1, tab2 = st.tabs(["표", "설명"])
with tab1:
    st.dataframe(filtered.head())
with tab2:
    st.write("펭귄 3종의 서식지·치수 데이터입니다.")
with st.expander("자세히 보기"):
    st.write("expander 안의 내용은 기본으로 접혀 있습니다.")

st.divider()

# =============================================================================
st.header("4. 묶기와 자리 잡기: st.container, st.empty")
st.markdown(
    """
`st.container` 는 여러 요소를 **한 덩어리로 묶습니다**. 화면 모양은 그대로지만,
그 덩어리를 변수에 담아 두면 **나중에 그 자리에** 내용을 추가할 수 있습니다.

`st.empty` 는 **한 칸짜리 자리**입니다. 자리만 먼저 잡아 두고 나중에 채우며,
다시 채우면 **이전 내용을 지우고** 새 내용으로 바뀝니다.
"""
)

st.markdown("**st.container: 나중에 그 덩어리 안에 추가하기**")
st.code(
    '''box = st.container()
box.write("먼저 그린 줄")

st.write("이 줄은 상자 밖(아래)에 그려집니다.")

box.write("나중에 그렸지만 상자 안이라 '먼저 그린 줄' 바로 아래로 들어갑니다.")''',
    language="python",
)
st.caption("▼ 실제 실행 결과: 코드 순서와 화면 순서가 다릅니다")
box = st.container()
box.write("먼저 그린 줄")
st.write("이 줄은 상자 밖(아래)에 그려집니다.")
box.write("나중에 그렸지만 상자 안이라 '먼저 그린 줄' 바로 아래로 들어갑니다.")

st.markdown("**st.empty: 한 칸을 잡아 두고 나중에 채우기**")
st.code(
    '''slot = st.empty()                  # 자리만 잡는다(아직 비어 있음)
st.caption("이 설명은 slot 아래에 고정됩니다.")

# 조건에 따라 그 자리에 무엇을 넣을지 나중에 정한다
if st.checkbox("자리에 내용 채우기"):
    slot.info("자리에 들어온 내용")
else:
    slot.warning("아직 비어 있습니다")''',
    language="python",
)
st.caption("▼ 실제 실행 결과: 체크박스를 켜고 꺼 보세요. 아래 설명은 자리를 지킵니다")
slot = st.empty()
st.caption("이 설명은 slot 아래에 고정됩니다.")
if st.checkbox("자리에 내용 채우기"):
    slot.info("자리에 들어온 내용")
else:
    slot.warning("아직 비어 있습니다")

# 🖐️ 직접 해보기: slot.info 를 slot.warning 위로 옮겨 두 번 채워 보세요.
#               한 칸이라 나중 것만 남습니다(덮어쓰기).

st.markdown("**사이드바에서 쓰는 이유: 아래 내용을 밀지 않으려고**")
st.markdown(
    """
사이드바 맨 아래에 저작권·도움말 같은 **푸터**를 두고 싶다고 해 봅시다. 그런데 필터는
조건에 따라 나중에 그려집니다. 순서대로 그리면 필터가 푸터 **아래**로 밀립니다.
자리를 먼저 잡아 두면 나중에 채워도 **푸터 위**에 들어갑니다.
"""
)
st.code(
    '''with st.sidebar:
    st.header("필터")
    filter_slot = st.empty()          # 필터가 들어올 자리를 먼저 잡는다
    st.divider()
    st.caption("ⓒ 2026 데이터분석 캠프")   # 푸터는 항상 맨 아래

# 한참 뒤 코드에서 그 자리를 채운다
with filter_slot.container():
    st.slider("가격 상한", 0, 100, 50)''',
    language="python",
)
st.caption("▼ 실제 실행 결과: 왼쪽 사이드바를 보세요. 슬라이더가 푸터 위에 들어가 있습니다")
with st.sidebar:
    st.header("필터")
    filter_slot = st.empty()
    st.divider()
    st.caption("ⓒ 2026 데이터분석 캠프")

with filter_slot.container():
    st.slider("가격 상한", 0, 100, 50)

st.info(
    "`st.empty()` 는 한 칸이라 요소를 하나만 담습니다. 여러 개를 넣으려면 위처럼 "
    "`슬롯.container()` 로 열어 그 안에 여러 개를 그립니다."
)

st.divider()

# =============================================================================
st.header("5. 대시보드 차트: plotly")
st.markdown(
    """
대시보드에 올리는 차트는 **plotly** 로 그립니다. 값에 마우스를 올리면 숫자가 뜨고(호버),
드래그로 확대하고, 범례를 눌러 계열을 켜고 끌 수 있습니다. 사용자가 직접 만지는 화면에 맞습니다.

`plotly.express`(관례상 `px`)로 그림(figure)을 만들고 `st.plotly_chart(fig)` 로 화면에 올립니다.
`width="stretch"` 를 주면 가로를 꽉 채웁니다.
"""
)

st.code(
    '''# 연도별 승객 수 추이 (flights: year, month, passengers)
#   groupby 결과는 Series 라 reset_index() 로 두 열짜리 DataFrame 을 만들어 px 에 넘긴다
yearly = flights.groupby("year")["passengers"].sum().reset_index()
fig = px.line(yearly, x="year", y="passengers", markers=True, title="연도별 승객 수")
st.plotly_chart(fig, width="stretch")

# 종별 평균 체중 비교
mass = df.groupby("species")["body_mass_g"].mean().reset_index()
fig = px.bar(mass, x="species", y="body_mass_g", color="species",
             title="종별 평균 체중(g)")
st.plotly_chart(fig, width="stretch")''',
    language="python",
)
st.caption("▼ 실제 실행 결과 (막대에 마우스를 올리거나 드래그해 확대해 보세요)")

# groupby 는 Series 를 주므로 reset_index() 로 열 이름이 있는 DataFrame 으로 바꾼다
yearly = flights.groupby("year")["passengers"].sum().reset_index()
fig = px.line(yearly, x="year", y="passengers", markers=True, title="연도별 승객 수")
st.plotly_chart(fig, width="stretch")

mass = df.groupby("species")["body_mass_g"].mean().reset_index()
# color 에 범주 열을 주면 종마다 색이 갈리고 범례가 생긴다(범례를 눌러 켜고 끌 수 있다)
fig = px.bar(mass, x="species", y="body_mass_g", color="species", title="종별 평균 체중(g)")
st.plotly_chart(fig, width="stretch")

# 🖐️ 직접 해보기: px.line 을 px.area 로 바꿔 그려 보세요. 같은 데이터인데 어떤 인상이 달라지나요?
#               px.bar 에 넘기는 집계를 mean 대신 max 로 바꾸면 막대 높이가 어떻게 변하는지도 확인해 보세요.

st.divider()

# =============================================================================
st.header("6. seaborn 그래프: st.pyplot")
st.markdown(
    """
plotly 가 대시보드용이라면, **분포를 들여다보는 통계 그래프**(상자그림·바이올린·히트맵)는
지난 단원의 **matplotlib/seaborn** 이 편합니다. 그려서 `st.pyplot(fig)` 에 넘깁니다. 핵심 3단계:

1. `fig, ax = plt.subplots()` 로 그림·축을 만든다
2. seaborn 함수에 `ax=ax` 를 준다
3. `st.pyplot(fig)` 로 표시하고 `plt.close(fig)` 로 정리한다
"""
)

st.code(
    '''fig, ax = plt.subplots(figsize=(6, 4))
sns.boxplot(data=df, x="species", y="body_mass_g", ax=ax)
ax.set_xlabel("종")
ax.set_ylabel("체중(g)")
st.pyplot(fig)
plt.close(fig)''',
    language="python",
)
st.caption("▼ 실제 실행 결과")
fig, ax = plt.subplots(figsize=(6, 4))
sns.boxplot(data=df, x="species", y="body_mass_g", ax=ax)
ax.set_xlabel("종")
ax.set_ylabel("체중(g)")
st.pyplot(fig)
plt.close(fig)

# 🖐️ 직접 해보기: boxplot 을 violinplot 으로 바꿔 보세요(인자는 그대로 둡니다). 분포 모양이 더 잘 보이나요?
#               plt.close(fig) 줄을 잠시 지우고 화면을 여러 번 새로고침하면 무엇이 쌓이는지 생각해 보세요(확인 후 되돌리기).

st.info("팁: 막대그래프에서 통계 오차막대가 필요 없으면 `sns.barplot(..., errorbar=None)` 로 끕니다.")

st.divider()

# =============================================================================
st.header("7. 화면에서 고치는 표: st.data_editor")
st.markdown(
    """
`st.dataframe` 은 **보기 전용**입니다. 사용자가 값을 직접 고치게 하려면 `st.data_editor` 를 씁니다.
편집 결과는 **새 DataFrame 으로 반환**되므로, 그 값을 그대로 다시 집계하거나 차트에 넘기면
"표를 고치면 숫자가 따라 바뀌는" 화면이 됩니다.

- `num_rows="dynamic"` : 사용자가 **행을 추가·삭제**할 수 있습니다(기본값은 고정).
- `disabled=[...]` : 특정 열은 **읽기 전용**으로 잠급니다.
"""
)

st.code(
    '''plan = pd.DataFrame({"분기": ["1Q", "2Q", "3Q", "4Q"], "목표": [120, 150, 130, 170]})

# 반환값이 편집된 표다. 원본(plan)은 그대로 남는다.
edited = st.data_editor(
    plan,
    width="stretch",
    num_rows="dynamic",        # 행 추가·삭제 허용
    disabled=["분기"],          # 분기 열은 못 고치게 잠근다
)

st.metric("목표 합계", int(edited["목표"].sum()))   # 표를 고치면 이 숫자가 바로 바뀐다
fig = px.bar(edited, x="분기", y="목표", title="분기별 목표")
st.plotly_chart(fig, width="stretch")''',
    language="python",
)
st.caption("▼ 실제 실행 결과 (표의 숫자를 고치거나 맨 아래 빈 행에 값을 넣어 보세요)")

plan = pd.DataFrame({"분기": ["1Q", "2Q", "3Q", "4Q"], "목표": [120, 150, 130, 170]})
# data_editor 는 편집된 표를 새로 돌려준다. 아래 집계·차트는 그 반환값을 쓴다.
edited = st.data_editor(
    plan,
    width="stretch",
    num_rows="dynamic",
    disabled=["분기"],
)
st.metric("목표 합계", int(edited["목표"].sum()))
# 차트도 원본이 아니라 편집된 표(edited)를 쓴다. 그래서 표를 고치면 함께 바뀐다.
fig = px.bar(edited, x="분기", y="목표", title="분기별 목표")
st.plotly_chart(fig, width="stretch")

# 🖐️ 직접 해보기: disabled=["분기"] 를 지우고 분기 이름을 고쳐 보세요.
#               그다음 num_rows="dynamic" 을 지우면 맨 아래 빈 행이 사라집니다(행 추가 불가).

st.warning(
    "편집 결과를 다른 화면에서도 써야 하면 반환값을 `st.session_state` 에 저장해야 합니다. "
    "그냥 변수에만 담으면 재실행 때 사라집니다(교안 05)."
)

st.divider()
st.subheader("이번 강의 정리")
st.markdown(
    """
- `st.sidebar` 로 필터를, `st.columns` 로 지표를 나란히
- `st.tabs`·`st.expander` 로 화면을 정리
- `st.container` : 여러 요소를 한 덩어리로. 변수에 담아 두면 **나중에 그 자리에** 추가할 수 있다
- `st.empty` : **한 칸을 미리 잡아 두는** 자리. 나중에 채우고 다시 채우면 덮어쓴다.
  사이드바에서 필터 자리를 먼저 잡아 두면 푸터가 아래로 밀리지 않는다
- 대시보드 차트는 **plotly**(`px.bar`/`px.line`) → `st.plotly_chart(fig, width="stretch")`. 호버·확대·범례 토글
- 분포·범주 분석은 **seaborn** → `st.pyplot(fig)` (+`plt.close`)
- `st.data_editor` : 사용자가 고치는 표. **편집된 표를 반환**하므로 집계·차트에 바로 넘긴다
"""
)
st.markdown("⏭️ **다음 시간**: 상태 유지와 캐싱 (`교안_01_기초UI/05_상태와_캐싱.py`)")
