# 실행: uv run streamlit run 과제_LV1_기초/app.py
# 과제 LV1(기초): 타이타닉 탑승객 대시보드 (UI에 집중)
#
# 문제.ipynb 를 보면서 아래 각 문제 섹션의 빈칸을 채워 완성하세요.
# import 와 데이터 로딩은 제공되어 있습니다. 여러분은 UI 코드만 작성합니다.

import os

# [제공 코드] pandas/Streamlit 이 쓰는 Arrow 의 메모리 할당기를 표준(system)으로 고정.
# 기본 할당기(mimalloc)는 macOS 에서 화면 재실행 시 앱이 죽는 문제가 있어 미리 막아 둔다.
# 반드시 pandas 를 import 하기 전에 설정해야 효과가 있다.
os.environ.setdefault("ARROW_DEFAULT_MEMORY_POOL", "system")

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

# [제공 코드] 어느 폴더에서 실행해도 경로가 맞도록 프로젝트 루트를 찾습니다.
PROJECT_ROOT = next(
    (p for p in Path(__file__).resolve().parents if (p / "core").is_dir()),
    Path(__file__).resolve().parent,
)
sys.path.insert(0, str(PROJECT_ROOT))
DATA_DIR = PROJECT_ROOT / "data"

from core.fonts import apply_korean_font

apply_korean_font()


# [제공 코드] 데이터 로딩. 캐싱은 문제 2에서 다시 설명합니다.
@st.cache_data
def load_data():
    return pd.read_csv(DATA_DIR / "titanic.csv")


df = load_data()


# 문제 1. 페이지 설정 + 제목 + 캡션
#   st.set_page_config(page_title=..., page_icon=..., layout="wide")
#   st.title(...) / st.caption(...)
# 여기에 코드를 작성하세요


# 문제 2. 데이터 살펴보기: st.dataframe 로 앞부분과 전체 크기를 보여주기
# 여기에 코드를 작성하세요


# 문제 3. st.metric 으로 '탑승객 수' 핵심 지표 1개 표시
# 여기에 코드를 작성하세요


# 문제 4. st.columns(3) 으로 생존 관련 지표 3개(생존자 수·생존율·평균 요금)를 나란히
# 여기에 코드를 작성하세요


# 문제 5. 사이드바에 st.multiselect 로 '객실 등급(class)' 필터 만들기
# 여기에 코드를 작성하세요


# 문제 6. 사이드바에 st.radio 로 '성별(sex)' 필터 만들기 (전체/male/female)
# 여기에 코드를 작성하세요


# 문제 7. 사이드바에 st.slider 로 '나이(age) 범위' 필터 만들기
# 여기에 코드를 작성하세요


# 문제 8. 위 필터들을 적용한 결과를 st.tabs(["데이터 표", "시각화"]) 로 나누어 표시
#   - 표 탭: st.dataframe
#   - 시각화 탭: 문제 9의 그래프
# 여기에 코드를 작성하세요


# 문제 9. 시각화 탭에 seaborn countplot 으로 '객실 등급별 생존자 수' 그래프
#   fig, ax = plt.subplots(); sns.countplot(...); st.pyplot(fig); plt.close(fig)
# 여기에 코드를 작성하세요


# 문제 10. st.session_state 로 '조회수' 카운터 버튼 만들기
# 여기에 코드를 작성하세요
