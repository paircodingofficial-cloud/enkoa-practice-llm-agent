# LV3 통합: 문서 Q&A 페이지 (core.rag_core 연동)
import os

# [제공 코드] pandas/Streamlit 이 쓰는 Arrow 의 메모리 할당기를 표준(system)으로 고정.
# 기본 할당기(mimalloc)는 macOS 에서 화면 재실행 시 앱이 죽는 문제가 있어 미리 막아 둔다.
# 반드시 pandas 를 import 하기 전에 설정해야 효과가 있다.
os.environ.setdefault("ARROW_DEFAULT_MEMORY_POOL", "system")

import sys
from pathlib import Path

import streamlit as st

# [제공 코드] 프로젝트 루트를 찾아 경로를 맞춥니다.
PROJECT_ROOT = next(
    (p for p in Path(__file__).resolve().parents if (p / "core").is_dir()),
    Path(__file__).resolve().parent,
)
sys.path.insert(0, str(PROJECT_ROOT))
from core import rag_core
from core.keys import require_openai_key_or_stop

st.title("📚 문서 Q&A (RAG)")

# [제공 코드] 실제 OpenAI 임베딩·생성이 필요한 페이지: 키가 없으면 안내를 띄우고 여기서 멈춘다.
require_openai_key_or_stop()

# 문제 2-문서QA. 검색 자원을 @st.cache_resource 로 준비 → 사이드바 참고 문서 수(slider)
#   → 질문 입력(text_input) → rag_core.ask 로 답변 표시 → 근거 문서를 expander 로(교안 03 참고)
# 여기에 코드를 작성하세요
