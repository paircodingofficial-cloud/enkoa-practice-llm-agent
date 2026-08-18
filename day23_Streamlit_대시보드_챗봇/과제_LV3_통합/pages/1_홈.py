# LV3 통합: 홈 페이지
import os

# [제공 코드] pandas/Streamlit 이 쓰는 Arrow 의 메모리 할당기를 표준(system)으로 고정.
# 기본 할당기(mimalloc)는 macOS 에서 화면 재실행 시 앱이 죽는 문제가 있어 미리 막아 둔다.
# 반드시 pandas 를 import 하기 전에 설정해야 효과가 있다.
os.environ.setdefault("ARROW_DEFAULT_MEMORY_POOL", "system")

import streamlit as st

st.title("💎 통합 AI 대시보드")

# 문제 2-홈. 앱 소개 문구(st.markdown)와 페이지 간 공유 상태 초기화
#   - st.session_state.messages 를 빈 리스트로 초기화(없을 때만)
#   - 사이드바에서 이동한다는 안내(st.info)
# 여기에 코드를 작성하세요
