# LV3 통합: 다이아몬드 대시보드 페이지
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

# [제공 코드] 프로젝트 루트를 찾아 경로를 맞춥니다.
PROJECT_ROOT = next(
    (p for p in Path(__file__).resolve().parents if (p / "core").is_dir()),
    Path(__file__).resolve().parent,
)
DATA_DIR = PROJECT_ROOT / "data"
sys.path.insert(0, str(PROJECT_ROOT))
from core.fonts import apply_korean_font

apply_korean_font()

st.title("💎 다이아몬드 대시보드")

# 문제 2-대시보드. diamonds.csv 를 @st.cache_data 로 로드
# 여기에 코드를 작성하세요

# 문제 2-대시보드. 사이드바 필터(컷 등급 multiselect, 최대 가격 slider)로 데이터 거르기
# 여기에 코드를 작성하세요

# 문제 2-대시보드. 고른 필터를 session_state 에 저장(챗봇 페이지가 읽어 갑니다)
# 여기에 코드를 작성하세요

# 문제 2-대시보드. 지표(columns+metric)와 탭 3개(컷별 개수 · 캐럿-가격 관계 · 데이터)
# 여기에 코드를 작성하세요
