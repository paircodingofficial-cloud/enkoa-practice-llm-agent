# 실행: uv run streamlit run 과제_LV2_응용/app.py
# 과제 LV2(응용): 기존 챗봇/RAG 시스템 연동 + 택시 대시보드
#
# 문제.ipynb 를 보며 각 섹션의 빈칸을 채우세요.
# RAG/LLM 로직은 새로 만들지 말고 core 함수(chatbot_core, rag_core)만 호출합니다.

import os

# [제공 코드] pandas/Streamlit 이 쓰는 Arrow 의 메모리 할당기를 표준(system)으로 고정.
# 기본 할당기(mimalloc)는 macOS 에서 화면 재실행 시 앱이 죽는 문제가 있어 미리 막아 둔다.
# 반드시 pandas 를 import 하기 전에 설정해야 효과가 있다.
os.environ.setdefault("ARROW_DEFAULT_MEMORY_POOL", "system")

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# [제공 코드] 프로젝트 루트를 찾아 경로를 맞춥니다.
PROJECT_ROOT = next(
    (p for p in Path(__file__).resolve().parents if (p / "core").is_dir()),
    Path(__file__).resolve().parent,
)
sys.path.insert(0, str(PROJECT_ROOT))
DATA_DIR = PROJECT_ROOT / "data"

from core import chatbot_core, rag_core
from core.keys import require_openai_key_or_stop

st.set_page_config(page_title="AI 어시스턴트 + 대시보드", page_icon="🚕", layout="wide")
st.title("🚕 AI 어시스턴트 + 택시 대시보드")

# [제공 코드] 챗봇·문서 Q&A 는 실제 OpenAI 호출이 필요하다. 키가 없으면 안내를 띄우고 여기서 멈춘다.
require_openai_key_or_stop()

# 문제 6. 사이드바에 공통 컨트롤(RAG 참고 문서 수 slider, 대화 초기화 button) 만들기
with st.sidebar:
    st.header("설정")
    # 여기에 코드를 작성하세요
    top_k = 3  # 문제 6에서 slider 값으로 교체하세요

# [제공 코드] 탭 구성
tab_chat, tab_rag, tab_dash = st.tabs(["💬 챗봇", "📚 문서 Q&A", "📊 택시 대시보드"])

with tab_chat:
    st.subheader("무엇이든 물어보세요")
    # 문제 1~3. 대화 이력 준비 → 이력 다시 그리기 → 새 입력을 chatbot_core.stream_reply 로 스트리밍
    # 여기에 코드를 작성하세요

with tab_rag:
    st.subheader("서비스 FAQ 문서 Q&A")
    # 문제 4~5. text_input 으로 질문 받아 rag_core.ask 로 답변 + 출처(expander) 표시
    # 여기에 코드를 작성하세요

with tab_dash:
    st.subheader("뉴욕 택시 운행 데이터")

    # 문제 7. @st.cache_data 로 taxis.csv 로딩 함수 만들기
    # 여기에 코드를 작성하세요

    # 문제 8. 지표(st.metric·st.columns)와 plotly 차트(px.bar → st.plotly_chart) 그리기
    # 여기에 코드를 작성하세요
