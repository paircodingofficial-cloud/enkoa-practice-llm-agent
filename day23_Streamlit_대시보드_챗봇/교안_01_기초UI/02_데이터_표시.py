# 실행: uv run streamlit run 교안_01_기초UI/02_데이터_표시.py
#
# 교안 01: 데이터를 표·지표로 보여 주기
# 대시보드의 핵심은 데이터를 잘 보여 주는 것입니다. DataFrame·지표(metric)·차트를 다룹니다.

import os

# [제공 코드] pandas/Streamlit 이 쓰는 Arrow 의 메모리 할당기를 표준(system)으로 고정.
# 기본 할당기(mimalloc)는 macOS 에서 화면 재실행 시 앱이 죽는 문제가 있어 미리 막아 둔다.
# 반드시 pandas 를 import 하기 전에 설정해야 효과가 있다.
os.environ.setdefault("ARROW_DEFAULT_MEMORY_POOL", "system")

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# [제공 코드] core/ 가 있는 상위 폴더를 찾아 데이터 경로를 잡습니다.
PROJECT_ROOT = next(
    (p for p in Path(__file__).resolve().parents if (p / "core").is_dir()),
    Path(__file__).resolve().parent,
)
DATA_DIR = PROJECT_ROOT / "data"

st.title("📗 데이터를 표·지표로 보여 주기")
st.caption("펭귄 데이터로 DataFrame·metric·json 출력을 익힙니다.")

st.divider()

# =============================================================================
st.header("1. 데이터 불러오기와 살펴보기")
st.markdown(
    "새 데이터를 만나면 항상 **먼저 살펴봅니다**. `head()`(앞부분)·`shape`(크기)를 확인하세요. "
    "지난 단원에서 배운 pandas 를 그대로 씁니다."
)

st.code(
    '''import pandas as pd
df = pd.read_csv(DATA_DIR / "penguins.csv")
st.write("크기:", df.shape)
st.dataframe(df.head())''',
    language="python",
)
st.caption("▼ 실제 실행 결과")
df = pd.read_csv(DATA_DIR / "penguins.csv")
st.write("크기:", df.shape)
st.dataframe(df.head())

st.divider()

# =============================================================================
st.header("2. st.dataframe vs st.table")
st.markdown(
    """
- `st.dataframe` : **인터랙티브** 표(정렬·스크롤·크기조절 가능). 큰 데이터에 적합.
- `st.table` : **정적** 표(전체를 그대로 렌더). 작은 요약표에 적합.
"""
)

st.code(
    '''st.dataframe(df.head(), width="stretch")   # 인터랙티브, 가로 꽉 채움
st.table(df["species"].value_counts())      # 정적 요약표''',
    language="python",
)
st.caption("▼ 실제 실행 결과")
st.dataframe(df.head(), width="stretch")
st.table(df["species"].value_counts())

st.divider()

# =============================================================================
st.header("3. st.metric: 핵심 지표 카드")
st.markdown(
    "대시보드 맨 위의 **큰 숫자 지표**입니다. `label`·`value` 에 더해 `delta`(증감)를 주면 "
    "화살표와 색으로 변화를 보여 줍니다. `delta` 는 **비교 기준(지난달·전주 등)이 있을 때** 쓰세요. 아래 값은 형태를 보여 주기 위한 예시입니다."
)

st.code(
    '''count = len(df)
mean_mass = df["body_mass_g"].mean()
st.metric("펭귄 수", f"{count}마리")
st.metric("평균 체중", f"{mean_mass:.0f} g", delta="+120 g (예시 값)")''',
    language="python",
)
st.caption("▼ 실제 실행 결과")
count = len(df)
mean_mass = df["body_mass_g"].mean()
st.metric("펭귄 수", f"{count}마리")
st.metric("평균 체중", f"{mean_mass:.0f} g", delta="+120 g (예시 값)")

# 🖐️ 직접 해보기: 평균 날개 길이(flipper_length_mm)를 metric 으로 추가해 보세요.

st.divider()

# =============================================================================
st.header("4. st.json: 딕셔너리·구조화 데이터")
st.markdown("API 응답이나 설정처럼 **중첩된 딕셔너리**는 `st.json` 으로 접었다 펼 수 있게 보여 줍니다.")

st.code(
    '''summary = {
    "종 수": int(df["species"].nunique()),
    "서식지": df["island"].unique().tolist(),
    "결측치_있는_열": df.columns[df.isna().any()].tolist(),
}
st.json(summary)''',
    language="python",
)
st.caption("▼ 실제 실행 결과")
summary = {
    "종 수": int(df["species"].nunique()),
    "서식지": df["island"].unique().tolist(),
    "결측치_있는_열": df.columns[df.isna().any()].tolist(),
}
st.json(summary)

st.divider()
st.subheader("이번 강의 정리")
st.markdown(
    """
- 새 데이터는 `shape`·`head()` 로 **먼저 살펴본다**
- `st.dataframe`(인터랙티브) vs `st.table`(정적)
- `st.metric` 으로 핵심 지표 카드(+`delta` 증감)
- `st.json` 으로 중첩 딕셔너리 표시
"""
)
st.markdown("⏭️ **다음 시간**: 사용자 입력 위젯 (`교안_01_기초UI/03_입력_위젯.py`)")
