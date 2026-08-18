# 멀티페이지 데모: 홈 페이지
# 각 페이지 파일은 '자립적'입니다: 자체적으로 필요한 것을 준비합니다.

import os

# [제공 코드] pandas/Streamlit 이 쓰는 Arrow 의 메모리 할당기를 표준(system)으로 고정.
# 기본 할당기(mimalloc)는 macOS 에서 화면 재실행 시 앱이 죽는 문제가 있어 미리 막아 둔다.
# 반드시 pandas 를 import 하기 전에 설정해야 효과가 있다.
os.environ.setdefault("ARROW_DEFAULT_MEMORY_POOL", "system")

import streamlit as st

st.title("🤖 AI 대시보드 데모")
st.markdown(
    """
이 앱은 하나의 프로젝트에 **여러 화면**을 담은 멀티페이지 예제입니다. 왼쪽 사이드바에서 이동하세요.

- **📊 데이터 대시보드**: 펭귄 데이터 필터·지표·차트
- **💬 챗봇**: 기존 챗봇 시스템(core.chatbot_core) 연동
- **📚 문서 Q&A**: 기존 RAG 시스템(core.rag_core) 연동, 답변 + 출처

멀티페이지의 핵심:
1. 엔트리(`main.py`)에서 `st.navigation` 으로 페이지 등록
2. 각 페이지는 `pages/` 폴더의 독립 파일
3. 페이지 사이에 공유할 값은 `st.session_state` 에 둔다(예: 대화 이력)
"""
)

# 페이지 간 공유 상태를 홈에서 미리 초기화해 둘 수도 있습니다.
if "messages" not in st.session_state:
    st.session_state.messages = []

st.info("사이드바에서 원하는 화면을 선택해 보세요.")
