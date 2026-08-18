# LV3 통합: 챗봇 페이지 (core.chatbot_core 연동)
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
from core import chatbot_core
from core.keys import require_openai_key_or_stop

st.title("💬 챗봇")

# [제공 코드] 실제 OpenAI 호출이 필요한 페이지: 키가 없으면 안내를 띄우고 여기서 멈춘다.
require_openai_key_or_stop()

# 문제 2-챗봇. 대화 이력 준비(공유 messages) → 사이드바 초기화 버튼 → 이력 다시 그리기
#   → 새 입력을 chatbot_core.stream_reply 로 스트리밍(교안 02 참고)
#   → 대시보드가 session_state 에 남긴 필터가 있으면 그 조건을 질문 앞에 붙여 함께 보내기
# 여기에 코드를 작성하세요
