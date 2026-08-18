# 실행: uv run streamlit run 교안_01_기초UI/07_부분_재실행.py
#
# 교안 01: 부분 재실행 @st.fragment
# 지금까지는 위젯을 건드리면 스크립트 '전체'가 다시 돌았습니다.
# 조각(fragment)으로 감싸면 그 조각만 다시 돌아, 무거운 부분을 건드리지 않습니다.

import os

# [제공 코드] pandas/Streamlit 이 쓰는 Arrow 의 메모리 할당기를 표준(system)으로 고정.
# 기본 할당기(mimalloc)는 macOS 에서 화면 재실행 시 앱이 죽는 문제가 있어 미리 막아 둔다.
# 반드시 pandas 를 import 하기 전에 설정해야 효과가 있다.
os.environ.setdefault("ARROW_DEFAULT_MEMORY_POOL", "system")

import time
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

DATA = Path(__file__).resolve().parent.parent / "data"

st.title("📗 부분 재실행 @st.fragment")
st.caption("무거운 화면에서 작은 위젯 하나 때문에 전체가 다시 도는 것을 막습니다")

st.divider()

# =============================================================================
st.header("1. 무엇이 문제인가")
st.markdown(
    """
교안 01-01 에서 배운 재실행 모델은 단순해서 좋지만 대가가 있습니다.
**어느 위젯을 건드려도 스크립트 전체가 처음부터 다시 실행**됩니다.

대시보드를 떠올려 보세요. 무거운 CSV 집계가 위에 있고, 아래에 정렬 방식을 고르는 작은 위젯이 있습니다.
정렬만 바꿔도 위의 집계가 다시 돕니다. 캐싱으로 많이 줄일 수 있지만,
**애초에 다시 돌 필요가 없는 코드를 안 돌리는** 방법이 `@st.fragment` 입니다.
"""
)

st.divider()

# =============================================================================
st.header("2. 실행 횟수를 세어 눈으로 확인하기")
st.markdown(
    """
말로는 감이 안 오니 **스크립트가 몇 번 돌았는지**와 **조각이 몇 번 돌았는지**를 각각 세어 봅니다.
`st.session_state` 에 카운터를 두고, 세는 위치를 다르게 하면 차이가 그대로 보입니다.
"""
)

# 스크립트가 처음부터 다시 돌 때마다 1 증가한다(파일 맨 위에서 세는 것과 같은 효과)
if "full_runs" not in st.session_state:
    st.session_state.full_runs = 0
    st.session_state.frag_runs = 0
st.session_state.full_runs += 1

st.markdown(
    """
한 가지 주의할 점이 먼저 있습니다. 조각만 다시 돌 때는 **조각이 그린 화면만** 다시 그려집니다.
그래서 두 숫자를 조각 **밖**에서 그리면, 값이 올라도 화면에는 반영되지 않습니다.
증거를 눈으로 보려면 **표시를 조각 안에 둬야** 합니다.
"""
)

st.code(
    '''# 파일 위쪽(조각 밖): 스크립트가 전체 재실행될 때마다 증가
st.session_state.full_runs += 1

@st.fragment
def sort_panel():
    # 조각 안: 조각만 다시 돌 때도 증가
    st.session_state.frag_runs += 1
    order = st.radio("정렬", ["오름차순", "내림차순"], horizontal=True, key="order")

    # 두 숫자를 조각 '안'에서 그린다. 조각만 다시 돌아도 이 두 칸은 다시 그려진다.
    col1, col2 = st.columns(2)
    col1.metric("전체 실행 횟수", st.session_state.full_runs)
    col2.metric("조각 실행 횟수", st.session_state.frag_runs)
    st.write(f"고른 정렬: {order}")

sort_panel()''',
    language="python",
)
st.caption("▼ 실제 실행 결과 (아래 라디오를 바꿔 보세요. 조각 횟수만 오릅니다)")


@st.fragment
def sort_panel():
    # 이 함수 안에서 위젯을 조작하면 이 함수만 다시 실행된다(스크립트 전체는 그대로)
    st.session_state.frag_runs += 1
    order = st.radio("정렬", ["오름차순", "내림차순"], horizontal=True, key="order")

    # 표시도 조각 안에 있어야 조각 재실행 때 갱신된다(밖에 두면 값만 오르고 화면은 그대로)
    col1, col2 = st.columns(2)
    col1.metric("전체 실행 횟수", st.session_state.full_runs)
    col2.metric("조각 실행 횟수", st.session_state.frag_runs)
    st.write(f"고른 정렬: {order}")


sort_panel()

st.info(
    "라디오를 바꾸면 **조각 실행 횟수만** 오릅니다. 전체 실행 횟수는 그대로입니다. "
    "이것이 부분 재실행의 증거입니다. 브라우저를 새로고침하면 둘 다 오릅니다(전체 재실행이니까요)."
)

st.warning(
    "방금 본 것이 조각의 가장 큰 함정입니다. **조각 밖의 화면은 조각 재실행으로 갱신되지 않습니다.** "
    "조각이 바꾼 값을 밖에서 보여 주고 싶으면, 그 표시를 조각 안으로 옮기거나 `st.rerun()` 으로 전체를 다시 돌려야 합니다(4절)."
)

# 🖐️ 직접 해보기: sort_panel 위의 @st.fragment 줄을 주석 처리하고 라디오를 바꿔 보세요.
#               이제 두 숫자가 함께 오릅니다. 확인했으면 주석을 풀어 되돌리세요.

st.divider()

# =============================================================================
st.header("3. 무거운 집계는 그대로 두고 필터만 다시 돌리기")
st.markdown(
    """
실제 쓰임입니다. 무거운 준비(여기서는 1초 걸리는 집계라고 가정)는 조각 **밖**에 두고,
자주 만지는 필터·정렬은 조각 **안**에 둡니다. 필터를 바꿔도 위의 집계는 다시 돌지 않습니다.
"""
)


@st.cache_data
def load_penguins():
    # 캐싱은 '같은 인자면 다시 계산 안 함'이고, fragment 는 '아예 그 코드에 안 들어감'이다.
    # 둘은 겹치지 않으므로 함께 쓴다.
    return pd.read_csv(DATA / "penguins.csv").dropna(subset=["body_mass_g"])


df = load_penguins()

# 조각 밖: 무거운 준비. 조각만 다시 돌 때는 이 줄을 지나가지 않는다.
with st.spinner("무거운 집계 준비 중…"):
    time.sleep(1.0)
    summary = df.groupby("species")["body_mass_g"].mean().round(1)

st.write("종별 평균 체중(무거운 집계 결과, 조각을 만져도 다시 계산되지 않습니다)")
st.dataframe(summary, width="stretch")


@st.fragment
def species_filter():
    # 이 안의 위젯을 조작하면 위의 sleep(1초)을 건너뛰고 이 블록만 다시 그린다
    picked = st.multiselect(
        "볼 종 고르기", sorted(df["species"].unique()), default=sorted(df["species"].unique())
    )
    shown = (summary.loc[picked] if picked else summary).rename_axis("종").reset_index(name="평균체중")
    st.plotly_chart(px.bar(shown, x="종", y="평균체중"), width="stretch")
    st.caption(f"선택 {len(picked)}종 · 이 블록만 다시 그려졌습니다")


species_filter()

st.warning(
    "체감해 보려면 종을 여러 번 바꿔 보세요. 조각이 없었다면 **매번 1초를 기다려야** 했습니다."
)

st.divider()

# =============================================================================
st.header("4. 조각 안에서 전체를 다시 돌려야 할 때")
st.markdown(
    """
조각 안의 변화가 **조각 밖 화면까지 바꿔야** 하는 경우가 있습니다. 그럴 때는 조각 안에서 `st.rerun()` 을 부릅니다.

- `st.rerun()` : 기본값이 `scope="app"` 이라 **앱 전체**를 다시 돌립니다.
- `st.rerun(scope="fragment")` : **그 조각만** 다시 돌립니다. 조각이 조각 재실행 중일 때만 쓸 수 있습니다.
"""
)

st.code(
    '''@st.fragment
def reset_panel():
    if st.button("카운터 초기화하고 전체 새로 그리기"):
        st.session_state.full_runs = 0
        st.session_state.frag_runs = 0
        st.rerun()          # scope 기본값이 "app" 이라 앱 전체가 다시 돈다

reset_panel()''',
    language="python",
)
st.caption("▼ 실제 실행 결과")


@st.fragment
def reset_panel():
    if st.button("카운터 초기화하고 전체 새로 그리기"):
        st.session_state.full_runs = 0
        st.session_state.frag_runs = 0
        # 조각 안에서 부른 st.rerun() 은 기본이 앱 전체다. 조각만 돌리려면 scope="fragment".
        st.rerun()


reset_panel()

st.divider()
st.subheader("이번 강의 정리")
st.markdown(
    """
- `@st.fragment` 를 함수에 붙이면 그 안의 위젯 조작은 **그 함수만** 다시 실행한다
- 자주 만지는 위젯은 조각 **안**, 무거운 준비는 조각 **밖**에 둔다(반대로 하면 이득이 없다)
- **조각 밖 화면은 조각 재실행으로 갱신되지 않는다.** 보여 줄 값은 조각 안에서 그린다
- 캐싱과 역할이 다르다: 캐싱은 '다시 계산 안 함', 조각은 '그 코드에 아예 안 들어감'
- 조각 밖까지 갱신해야 하면 조각 안에서 `st.rerun()`(전체) 또는 `st.rerun(scope="fragment")`(조각만)
"""
)
st.markdown("⏭️ **다음 단원**: 챗봇 UI와 기존 시스템 연동 (`교안_02_챗봇과_연동/`)")
