# 실행: uv run streamlit run 과제_LV3_통합/main.py
# 과제 LV3(통합): 멀티페이지 AI 대시보드 (엔트리)
#
# 문제 1에서 st.navigation 으로 아래 4개 페이지를 등록하세요.
# pages/1_홈.py, pages/2_대시보드.py, pages/3_챗봇.py, pages/4_문서QA.py

import os

# [제공 코드] pandas/Streamlit 이 쓰는 Arrow 의 메모리 할당기를 표준(system)으로 고정.
# 기본 할당기(mimalloc)는 macOS 에서 화면 재실행 시 앱이 죽는 문제가 있어 미리 막아 둔다.
# 반드시 pandas 를 import 하기 전에 설정해야 효과가 있다.
os.environ.setdefault("ARROW_DEFAULT_MEMORY_POOL", "system")

import streamlit as st

st.set_page_config(page_title="통합 AI 대시보드", page_icon="💎", layout="wide")

# 문제 1. st.navigation 으로 4개 페이지를 등록하고 pg 에 담기
#   - 딕셔너리로 그룹(시작/분석/AI)을 나누고, 각 페이지는 st.Page("pages/....py", title=..., icon=...)
#   - 홈 페이지에 default=True
# 여기에 코드를 작성하세요

# 문제 1. 등록한 네비게이션 실행
# 여기에 코드를 작성하세요
