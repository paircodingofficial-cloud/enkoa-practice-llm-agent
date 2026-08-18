# 실행: uv run streamlit run 교안_02_챗봇과_연동/04_멀티페이지_데모/main.py
#
# 교안 02: 멀티페이지 앱 (완성 데모)
# 여러 화면(홈·대시보드·챗봇·문서 Q&A)을 하나의 앱으로 묶습니다.
# 이 파일이 '엔트리(진입점)'입니다. st.navigation 으로 페이지를 등록하고 pg.run() 으로 실행합니다.

import os

# [제공 코드] pandas/Streamlit 이 쓰는 Arrow 의 메모리 할당기를 표준(system)으로 고정.
# 기본 할당기(mimalloc)는 macOS 에서 화면 재실행 시 앱이 죽는 문제가 있어 미리 막아 둔다.
# 반드시 pandas 를 import 하기 전에 설정해야 효과가 있다.
os.environ.setdefault("ARROW_DEFAULT_MEMORY_POOL", "system")

import streamlit as st

st.set_page_config(page_title="AI 대시보드 데모", page_icon="🤖", layout="wide")

# 사이드바에 '페이지별 컨트롤이 들어올 자리'를 먼저 잡고, 그 아래에 공통 푸터를 둡니다.
# 자리를 안 잡으면 페이지가 나중에 그리는 필터가 푸터 '아래'로 밀립니다.
# 각 페이지는 st.session_state.sidebar_slot 을 열어 자기 컨트롤을 그 자리에 그립니다.
with st.sidebar:
    st.session_state.sidebar_slot = st.empty()
    st.divider()
    st.caption("🤖 AI 대시보드 데모 · 23일차 실습")

# st.Page 로 각 페이지 파일을 등록하고, 딕셔너리로 그룹(사이드바 섹션)을 나눕니다.
pg = st.navigation(
    {
        "시작": [
            st.Page("pages/1_홈.py", title="홈", icon="🏠", default=True),
        ],
        "분석": [
            st.Page("pages/2_대시보드.py", title="데이터 대시보드", icon="📊"),
        ],
        "AI": [
            st.Page("pages/3_챗봇.py", title="챗봇", icon="💬"),
            st.Page("pages/4_문서QA.py", title="문서 Q&A", icon="📚"),
        ],
    }
)

pg.run()
