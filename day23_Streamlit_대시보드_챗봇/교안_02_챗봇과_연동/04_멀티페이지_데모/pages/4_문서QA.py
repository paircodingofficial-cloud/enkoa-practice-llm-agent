# 멀티페이지 데모: 문서 Q&A 페이지 (core.rag_core 연동)
import os

# [제공 코드] pandas/Streamlit 이 쓰는 Arrow 의 메모리 할당기를 표준(system)으로 고정.
# 기본 할당기(mimalloc)는 macOS 에서 화면 재실행 시 앱이 죽는 문제가 있어 미리 막아 둔다.
# 반드시 pandas 를 import 하기 전에 설정해야 효과가 있다.
os.environ.setdefault("ARROW_DEFAULT_MEMORY_POOL", "system")

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = next(
    (p for p in Path(__file__).resolve().parents if (p / "core").is_dir()),
    Path(__file__).resolve().parent,
)
sys.path.insert(0, str(PROJECT_ROOT))
from core import rag_core
from core.keys import require_openai_key_or_stop

st.title("📚 문서 Q&A (RAG)")

# 실제 OpenAI 임베딩·생성이 필요한 페이지: 키가 없으면 안내를 띄우고 여기서 멈춘다.
require_openai_key_or_stop()

st.caption("OpenAI 연결됨 · 서비스 FAQ 문서에서 답을 찾아 출처와 함께 보여 줍니다.")


# 무거운 준비는 한 번만
@st.cache_resource
def get_rag():
    return rag_core


rag = get_rag()

# main.py 로 열면 main.py 가 잡아 둔 자리에, 이 파일만 단독 실행하면 사이드바에 바로 그린다.
slot = st.session_state.get("sidebar_slot")
with (slot.container() if slot else st.sidebar):
    top_k = st.slider("참고 문서 수", 1, 5, 3)

question = st.text_input("FAQ에 대해 물어보세요", placeholder="예: 파일 용량 제한이 얼마인가요?")

if question:
    result = rag.ask(question, k=top_k)
    st.markdown("### 답변")
    st.write(result["answer"])
    st.markdown("### 근거 문서")
    for s in result["sources"]:
        with st.expander(f"{s['title']}  (유사도 {s['score']})"):
            st.write(s["text"])
else:
    st.info("궁금한 점을 입력하면 문서에서 근거를 찾아 답합니다.")
